"""LLM Orchestrator.

整合状态机、LLM 客户端和工具调用，驱动归因分析流程。
"""

from __future__ import annotations

import asyncio
from typing import Optional, Any

from state_machine import AttributionState, AttributionStateMachine, AnalysisMode

from .client import LLMMessage, create_llm_client
from .prompts import PromptTemplate
from .tools import ToolCall, get_tool_registry


class LLMOrchestrator:
    """LLM Orchestrator.

    协调 LLM、状态机和工具执行，实现自动/手动两种分析模式。

    Example:
        >>> orchestrator = LLMOrchestrator(session_id="att-001")
        >>> await orchestrator.start_analysis(
        ...     mode=AnalysisMode.AUTO,
        ...     indicator_tree_config=config,
        ...     data_source=data_source,
        ... )
    """

    def __init__(
        self,
        session_id: str,
        llm_config: Optional[dict[str, Any]] = None,
    ):
        """初始化 Orchestrator.

        Args:
            session_id: 会话ID
            llm_config: LLM 配置
        """
        self.session_id = session_id
        self.state_machine = AttributionStateMachine(session_id=session_id)
        self.llm_client = create_llm_client(llm_config)
        self.tool_registry = get_tool_registry()
        self.context: dict[str, Any] = {}

    async def start_analysis(
        self,
        mode: AnalysisMode,
        indicator_tree_config: dict[str, Any],
        data_source: dict[str, Any],
        analysis_period: dict[str, str],
    ) -> dict[str, Any]:
        """启动归因分析.

        Args:
            mode: 分析模式
            indicator_tree_config: 指标树配置
            data_source: 数据源配置
            analysis_period: 分析周期

        Returns:
            初始响应
        """
        # 设置上下文
        self.context = {
            "task_id": self.session_id,
            "mode": mode.value,
            "analysis_period": analysis_period,
            "indicator_tree": indicator_tree_config,
            "data_source": data_source,
        }

        # 启动状态机
        self.state_machine.start(mode=mode, context=self.context)

        if mode == AnalysisMode.AUTO:
            # 自动模式：执行所有步骤后调用 LLM 生成汇总
            return await self._run_auto_mode()
        else:
            # 手动模式：执行第一步并等待用户确认
            return await self._run_manual_step()

    async def _run_auto_mode(self) -> dict[str, Any]:
        """执行自动模式分析.

        执行所有步骤，最后调用 LLM 生成汇总报告。

        Returns:
            分析结果
        """
        # 模拟执行所有步骤（实际应调用算法服务）
        steps_result = []

        # Step 1: GMV 第一层拆解
        step1_result = await self._execute_step1()
        steps_result.append(step1_result)
        self.state_machine.transition_to(AttributionState.AUTO_STEP2, step1_result)
        self._persist_step(1, step1_result)

        # Step 2: 子维度熵减计算
        step2_result = await self._execute_step2()
        steps_result.append(step2_result)
        self.state_machine.transition_to(AttributionState.AUTO_STEP3, step2_result)
        self._persist_step(2, step2_result)

        # Step 3: 动作指标定位
        step3_result = await self._execute_step3()
        steps_result.append(step3_result)
        self.state_machine.transition_to(AttributionState.AUTO_STEP4, step3_result)
        self._persist_step(3, step3_result)

        # Step 4: 最终下钻
        step4_result = await self._execute_step4()
        steps_result.append(step4_result)
        self.state_machine.transition_to(AttributionState.AUTO_SUMMARY, step4_result)
        self._persist_step(4, step4_result)

        # 生成 LLM 汇总
        self.state_machine.transition_to(AttributionState.LLM_NARRATIVE)
        narrative = await self._generate_narrative(steps_result)

        # 进入人工输入状态
        self.state_machine.transition_to(AttributionState.HUMAN_INPUT)

        return {
            "session_id": self.session_id,
            "state": self.state_machine.current_state.value,
            "attribution_chain": steps_result,
            "narrative": narrative,
            "next_action": "等待用户提交业务结论",
        }

    async def _run_manual_step(self) -> dict[str, Any]:
        """执行手动模式的单步分析.

        执行当前步骤，调用 LLM 生成解释，等待用户确认。

        Returns:
            步骤结果和解释
        """
        current_step = self.state_machine.current_step

        if not current_step:
            return {
                "error": "当前不是步骤状态",
                "state": self.state_machine.current_state.value,
            }

        # 执行当前步骤
        step_result = await self._execute_step(current_step.value)

        # 存储步骤结果
        self.state_machine.set_context(f"step_{current_step.value}_result", step_result)
        self._persist_step(current_step.value, step_result)

        # 生成 LLM 解释
        explanation = await self._generate_step_explanation(
            step=current_step.value,
            step_result=step_result,
        )

        # 根据步骤决定下一个状态
        next_states = {
            1: (AttributionState.LLM_EXPLAIN_1, AttributionState.MANUAL_STEP2),
            2: (AttributionState.LLM_EXPLAIN_2, AttributionState.MANUAL_STEP3),
            3: (AttributionState.LLM_EXPLAIN_3, AttributionState.MANUAL_STEP4),
            4: (AttributionState.LLM_EXPLAIN_4, AttributionState.HUMAN_INPUT),
        }

        explain_state, next_step_state = next_states.get(current_step.value, (None, None))

        if explain_state:
            self.state_machine.transition_to(explain_state, {"explanation": explanation})

        return {
            "session_id": self.session_id,
            "step": current_step.value,
            "state": self.state_machine.current_state.value,
            "step_result": step_result,
            "explanation": explanation,
            "next_action": "确认继续" if current_step.value < 4 else "提交业务结论",
        }

    async def continue_manual(self) -> dict[str, Any]:
        """继续手动模式的下一步.

        用户确认后继续执行下一步。

        Returns:
            下一步结果
        """
        if not self.state_machine.is_manual():
            return {"error": "当前不是手动模式"}

        # 从解释状态转到下一步
        current_state = self.state_machine.current_state

        transitions = {
            AttributionState.LLM_EXPLAIN_1: AttributionState.MANUAL_STEP2,
            AttributionState.LLM_EXPLAIN_2: AttributionState.MANUAL_STEP3,
            AttributionState.LLM_EXPLAIN_3: AttributionState.MANUAL_STEP4,
            AttributionState.LLM_EXPLAIN_4: AttributionState.HUMAN_INPUT,
        }

        next_state = transitions.get(current_state)
        if next_state:
            self.state_machine.transition_to(next_state)

        # 如果到了人工输入状态
        if self.state_machine.current_state == AttributionState.HUMAN_INPUT:
            return {
                "session_id": self.session_id,
                "state": self.state_machine.current_state.value,
                "message": "请提交业务结论",
            }

        # 执行下一步
        return await self._run_manual_step()

    async def submit_conclusion(
        self,
        conclusion: dict[str, Any],
    ) -> dict[str, Any]:
        """提交人工结论.

        Args:
            conclusion: 结构化结论

        Returns:
            最终报告
        """
        if self.state_machine.current_state != AttributionState.HUMAN_INPUT:
            return {"error": "当前状态不允许提交结论"}

        # 存储结论
        self.state_machine.set_context("human_conclusion", conclusion)

        # 进入最终报告状态
        self.state_machine.transition_to(AttributionState.FINAL_REPORT)

        # 生成最终报告
        report = await self._generate_final_report(conclusion)

        return {
            "session_id": self.session_id,
            "state": self.state_machine.current_state.value,
            "final_report": report,
            "can_export": True,
        }

    # ============ 步骤执行（模拟，实际应调用算法服务） ============

    async def _execute_step1(self) -> dict[str, Any]:
        """执行 Step 1: GMV 第一层拆解."""
        # 实际应调用算法服务
        return {
            "step": 1,
            "node_id": "gmv",
            "selected_dimension": "区域",
            "selected_child": "美国",
            "entropy_reduction": 0.74,
        }

    async def _execute_step2(self) -> dict[str, Any]:
        """执行 Step 2: 子维度熵减计算."""
        return {
            "step": 2,
            "node_id": "org_us",
            "selected_dimension": "产品",
            "selected_child": "产品A",
            "entropy_reduction": 0.56,
        }

    async def _execute_step3(self) -> dict[str, Any]:
        """执行 Step 3: 动作指标定位."""
        return {
            "step": 3,
            "node_id": "prod_a",
            "selected_dimension": "渠道",
            "selected_child": "线上",
            "entropy_reduction": 0.45,
        }

    async def _execute_step4(self) -> dict[str, Any]:
        """执行 Step 4: 最终下钻."""
        return {
            "step": 4,
            "node_id": "ch_online",
            "action_indicator": "广告预算",
            "change_rate": -0.35,
            "contribution": -52000,
        }

    def _persist_step(self, step_number: int, step_result: dict[str, Any]) -> None:
        """将步骤结果持久化到数据库（失败不阻塞主流程）."""
        try:
            from db.models import AttributionStep, _SessionLocal

            if _SessionLocal is None:
                return

            db = _SessionLocal()
            try:
                db_step = AttributionStep(
                    session_id=self.session_id,
                    step_number=step_number,
                    node_id=step_result.get("node_id", "-"),
                    node_name=step_result.get("node_name", step_result.get("node_id", "-")),
                    node_type=step_result.get("node_type", "operation"),
                    selected_dimension=step_result.get("selected_dimension"),
                    selected_child=step_result.get("selected_child"),
                    entropy_results=step_result,
                )
                db.add(db_step)
                db.commit()
            finally:
                db.close()
        except Exception:
            # 持久化失败不应影响分析流程
            pass

    async def _execute_step(self, step: int) -> dict[str, Any]:
        """执行指定步骤."""
        step_functions = {
            1: self._execute_step1,
            2: self._execute_step2,
            3: self._execute_step3,
            4: self._execute_step4,
        }
        func = step_functions.get(step)
        if func:
            return await func()
        return {"error": f"未知步骤: {step}"}

    # ============ LLM 调用 ============

    async def _generate_step_explanation(
        self,
        step: int,
        step_result: dict[str, Any],
    ) -> str:
        """生成步骤解释."""
        prompt = PromptTemplate.for_step(
            step=step,
            mode=self.state_machine.mode.value if self.state_machine.mode else "unknown",
            step_result=step_result,
            context=self.context,
        )

        messages = [
            LLMMessage(role="system", content=PromptTemplate.SYSTEM_PROMPT),
            LLMMessage(role="user", content=prompt),
        ]

        response = self.llm_client.complete_with_retry(messages)
        return response.content

    async def _generate_narrative(
        self,
        attribution_chain: list[dict[str, Any]],
    ) -> str:
        """生成自动模式汇总叙事."""
        uploaded_files = self.state_machine.get_context("uploaded_files")
        prompt = PromptTemplate.for_auto_summary(
            attribution_chain=attribution_chain,
            context=self.context,
            uploaded_files=uploaded_files,
        )

        messages = [
            LLMMessage(role="system", content=PromptTemplate.SYSTEM_PROMPT),
            LLMMessage(role="user", content=prompt),
        ]

        response = self.llm_client.complete_with_retry(messages)
        return response.content

    async def _generate_final_report(
        self,
        human_conclusion: Optional[dict[str, Any]],
    ) -> str:
        """生成最终报告."""
        # 获取归因链
        attribution_chain = []
        for i in range(1, 5):
            result = self.state_machine.get_context(f"step_{i}_result")
            if result:
                attribution_chain.append(result)

        uploaded_files = self.state_machine.get_context("uploaded_files")
        prompt = PromptTemplate.for_final_report(
            attribution_chain=attribution_chain,
            human_conclusion=human_conclusion,
            context=self.context,
            uploaded_files=uploaded_files,
        )

        messages = [
            LLMMessage(role="system", content=PromptTemplate.SYSTEM_PROMPT),
            LLMMessage(role="user", content=prompt),
        ]

        response = self.llm_client.complete_with_retry(messages)
        return response.content

    def get_status(self) -> dict[str, Any]:
        """获取当前状态."""
        return {
            "session_id": self.session_id,
            "state": self.state_machine.current_state.value,
            "mode": self.state_machine.mode.value if self.state_machine.mode else None,
            "step": self.state_machine.current_step.value if self.state_machine.current_step else None,
            "can_export_process": self.state_machine.can_export_process(),
            "can_export_full": self.state_machine.can_export_full(),
            "is_terminal": self.state_machine.is_terminal(),
        }

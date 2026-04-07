"""Task 4 端到端自证测试.

验证 LLM Orchestrator + 状态机 + 会话管理的完整功能。
"""

from __future__ import annotations

import asyncio

from llm import LLMOrchestrator, PromptTemplate
from state_machine import AnalysisMode, AttributionState


def run_async(coro):
    """运行异步协程."""
    return asyncio.run(coro)


class TestTask4LLMOrchestrator:
    """LLM Orchestrator 端到端测试."""

    def test_auto_mode_full_flow(self):
        """测试自动模式完整流程: INIT -> ... -> HUMAN_INPUT -> FINAL_REPORT."""
        orch = LLMOrchestrator(session_id="test-auto-001")

        # 启动自动模式分析
        result = run_async(orch.start_analysis(
            mode=AnalysisMode.AUTO,
            indicator_tree_config={"root": "gmv"},
            data_source={"type": "excel"},
            analysis_period={
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "comparison_period": "prev_month",
            },
        ))

        # 验证状态
        assert result["session_id"] == "test-auto-001"
        assert result["state"] == "HUMAN_INPUT"
        assert "narrative" in result
        assert "attribution_chain" in result
        assert len(result["attribution_chain"]) == 4  # 4个步骤

        # 验证状态机状态
        status = orch.get_status()
        assert status["state"] == "HUMAN_INPUT"
        assert status["mode"] == "auto"
        assert status["can_export_process"] is True
        assert status["can_export_full"] is False
        assert status["is_terminal"] is False

    def test_manual_mode_step_by_step(self):
        """测试手动模式逐步推进."""
        orch = LLMOrchestrator(session_id="test-manual-001")

        # 启动手动模式
        result = run_async(orch.start_analysis(
            mode=AnalysisMode.MANUAL,
            indicator_tree_config={"root": "gmv"},
            data_source={"type": "excel"},
            analysis_period={
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "comparison_period": "prev_month",
            },
        ))

        # 第一步应该在 MANUAL_STEP1 或 LLM_EXPLAIN_1
        assert result["step"] == 1
        assert "explanation" in result
        assert result["next_action"] == "确认继续"

        # 继续第二步
        result = run_async(orch.continue_manual())
        assert result["step"] == 2

        # 继续第三步
        result = run_async(orch.continue_manual())
        assert result["step"] == 3

        # 继续第四步
        result = run_async(orch.continue_manual())
        assert result["step"] == 4
        assert result["next_action"] == "提交业务结论"

        # 继续到 HUMAN_INPUT
        result = run_async(orch.continue_manual())
        assert result["state"] == "HUMAN_INPUT"

    def test_submit_conclusion(self):
        """测试提交业务结论."""
        orch = LLMOrchestrator(session_id="test-conclusion-001")

        # 先完成自动模式分析
        run_async(orch.start_analysis(
            mode=AnalysisMode.AUTO,
            indicator_tree_config={"root": "gmv"},
            data_source={"type": "excel"},
            analysis_period={
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
            },
        ))

        # 提交结论
        conclusion = {
            "reason_type": "预算削减",
            "detailed_explanation": "Q1预算调整导致广告投放减少",
            "involved_departments": ["市场部", "财务部"],
            "suggested_actions": "申请追加预算或调整投放策略",
            "confidence_level": "high",
        }

        result = run_async(orch.submit_conclusion(conclusion))

        assert result["state"] == "FINAL_REPORT"
        assert result["can_export"] is True
        assert "final_report" in result

        # 验证状态机
        status = orch.get_status()
        assert status["can_export_full"] is True
        assert status["is_terminal"] is True


class TestTask4PromptTemplates:
    """Prompt 模板测试."""

    def test_step_prompt_generation(self):
        """测试步骤 Prompt 生成."""
        step_result = {
            "selected_dimension": "区域",
            "entropy_reduction": 0.74,
        }

        prompt = PromptTemplate.for_step(
            step=1,
            mode="auto",
            step_result=step_result,
            context={"task_id": "test-001"},
        )

        assert "Step 1" in prompt
        assert "区域" in prompt
        assert "0.74" in str(prompt)
        assert "test-001" in prompt

    def test_auto_summary_prompt(self):
        """测试自动汇总 Prompt 生成."""
        attribution_chain = [
            {"step": 1, "dimension": "区域"},
            {"step": 2, "dimension": "产品"},
        ]

        prompt = PromptTemplate.for_auto_summary(
            attribution_chain=attribution_chain,
            context={"task_id": "test-002"},
        )

        assert "auto" in prompt
        assert "区域" in prompt
        assert "产品" in prompt

    def test_error_prompt(self):
        """测试错误 Prompt 生成."""
        prompt = PromptTemplate.for_error(
            error_state="DATA_MISSING",
            error_message="缺少区域维度数据",
        )

        assert "数据缺失" in prompt
        assert "缺少区域维度数据" in prompt


class TestTask4Integration:
    """Task 4 集成测试."""

    def test_end_to_end_auto_mode(self):
        """端到端自动模式测试（完整自证）."""
        print("\n=== Task 4 自证: 自动模式端到端测试 ===")

        # 1. 创建会话
        orch = LLMOrchestrator(session_id="e2e-auto-001")
        print("✓ 1. 创建 LLMOrchestrator")

        # 2. 启动自动分析
        result = run_async(orch.start_analysis(
            mode=AnalysisMode.AUTO,
            indicator_tree_config={"root": "gmv", "children": ["org", "ops"]},
            data_source={"type": "excel", "path": "./testdata"},
            analysis_period={
                "start_date": "2026-03-01",
                "end_date": "2026-03-31",
                "comparison_period": "prev_month",
            },
        ))
        print(f"✓ 2. 自动分析完成，当前状态: {result['state']}")

        # 3. 验证归因链
        assert len(result["attribution_chain"]) == 4
        print(f"✓ 3. 归因链包含 4 个步骤")

        # 4. 验证 LLM 叙事
        assert "narrative" in result
        assert len(result["narrative"]) > 0
        print(f"✓ 4. LLM 叙事生成成功 ({len(result['narrative'])} 字符)")

        # 5. 验证状态机状态
        status = orch.get_status()
        assert status["state"] == "HUMAN_INPUT"
        assert status["mode"] == "auto"
        print(f"✓ 5. 状态机状态正确: {status['state']}")

        # 6. 提交业务结论
        conclusion = {
            "reason_type": "预算削减",
            "detailed_explanation": "Q1预算调整导致广告投放减少",
            "involved_departments": ["市场部"],
            "suggested_actions": "申请追加预算",
            "confidence_level": "high",
        }
        final_result = run_async(orch.submit_conclusion(conclusion))
        print(f"✓ 6. 提交业务结论，生成最终报告")

        # 7. 验证最终状态
        assert final_result["state"] == "FINAL_REPORT"
        assert final_result["can_export"] is True
        print(f"✓ 7. 最终状态: {final_result['state']}, 可导出: {final_result['can_export']}")

        print("\n=== Task 4 自证通过 ===")

    def test_end_to_end_manual_mode(self):
        """端到端手动模式测试（完整自证）."""
        print("\n=== Task 4 自证: 手动模式端到端测试 ===")

        # 1. 创建会话
        orch = LLMOrchestrator(session_id="e2e-manual-001")
        print("✓ 1. 创建 LLMOrchestrator")

        # 2. 启动手动分析
        result = run_async(orch.start_analysis(
            mode=AnalysisMode.MANUAL,
            indicator_tree_config={"root": "gmv"},
            data_source={"type": "excel"},
            analysis_period={"start_date": "2026-03-01", "end_date": "2026-03-31"},
        ))
        print(f"✓ 2. 手动分析启动，步骤: {result['step']}")

        # 3. 逐步推进
        for i in range(2, 5):
            result = run_async(orch.continue_manual())
            print(f"✓ 3.{i-1}. 推进到步骤 {result.get('step', 'END')}")

        # 4. 到 HUMAN_INPUT
        result = run_async(orch.continue_manual())
        assert result["state"] == "HUMAN_INPUT"
        print(f"✓ 4. 到达 {result['state']} 状态")

        # 5. 提交结论
        final = run_async(orch.submit_conclusion({
            "reason_type": "竞品影响",
            "detailed_explanation": "竞品促销活动",
            "involved_departments": ["销售部"],
            "suggested_actions": "跟进促销",
            "confidence_level": "medium",
        }))
        assert final["state"] == "FINAL_REPORT"
        print(f"✓ 5. 提交结论，到达 {final['state']}")

        print("\n=== Task 4 自证通过 ===")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])

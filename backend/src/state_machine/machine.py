"""状态机核心类.

实现 GMV 归因系统的状态流转逻辑。
"""

from __future__ import annotations

import time
from typing import Any, Callable, Optional

from .states import (
    AnalysisMode,
    AttributionState,
    AttributionStep,
    can_export_full_report,
    can_export_process_report,
    get_step_from_state,
    is_auto_state,
    is_error_state,
    is_manual_state,
    is_terminal_state,
)


class StateTransitionError(Exception):
    """状态流转错误."""

    def __init__(self, message: str, current_state: AttributionState, target_state: AttributionState):
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(f"[{current_state.value} -> {target_state.value}] {message}")


class AttributionStateMachine:
    """归因分析状态机.

    管理归因分析任务的状态流转，支持自动模式和手动模式。

    Example:
        >>> sm = AttributionStateMachine(session_id="att-001")
        >>> sm.start(mode=AnalysisMode.AUTO)
        >>> sm.current_state
        AttributionState.AUTO_STEP1
        >>> sm.transition_to(AttributionState.AUTO_STEP2, step_result={...})
    """

    # 定义合法的状态流转
    VALID_TRANSITIONS: dict[AttributionState, set[AttributionState]] = {
        # 初始状态
        AttributionState.INIT: {
            AttributionState.MODE_SELECT,
            AttributionState.TERMINATED,
        },
        AttributionState.MODE_SELECT: {
            AttributionState.AUTO_STEP1,
            AttributionState.MANUAL_STEP1,
            AttributionState.TERMINATED,
        },

        # 自动模式流转
        AttributionState.AUTO_STEP1: {
            AttributionState.AUTO_STEP2,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.AUTO_STEP2: {
            AttributionState.AUTO_STEP3,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.AUTO_STEP3: {
            AttributionState.AUTO_STEP4,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.AUTO_STEP4: {
            AttributionState.AUTO_SUMMARY,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.AUTO_SUMMARY: {
            AttributionState.LLM_NARRATIVE,
            AttributionState.ALGO_ERROR,
        },

        # 手动模式流转
        AttributionState.MANUAL_STEP1: {
            AttributionState.LLM_EXPLAIN_1,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.LLM_EXPLAIN_1: {
            AttributionState.MANUAL_STEP2,
            AttributionState.HUMAN_INPUT,  # 用户可以中断
        },
        AttributionState.MANUAL_STEP2: {
            AttributionState.LLM_EXPLAIN_2,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.LLM_EXPLAIN_2: {
            AttributionState.MANUAL_STEP3,
            AttributionState.HUMAN_INPUT,
        },
        AttributionState.MANUAL_STEP3: {
            AttributionState.LLM_EXPLAIN_3,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.LLM_EXPLAIN_3: {
            AttributionState.MANUAL_STEP4,
            AttributionState.HUMAN_INPUT,
        },
        AttributionState.MANUAL_STEP4: {
            AttributionState.LLM_EXPLAIN_4,
            AttributionState.ALGO_ERROR,
            AttributionState.DATA_MISSING,
        },
        AttributionState.LLM_EXPLAIN_4: {
            AttributionState.HUMAN_INPUT,
        },

        # LLM 叙事
        AttributionState.LLM_NARRATIVE: {
            AttributionState.HUMAN_INPUT,
        },

        # 人工输入
        AttributionState.HUMAN_INPUT: {
            AttributionState.FINAL_REPORT,
            AttributionState.TERMINATED,
        },

        # 最终报告
        AttributionState.FINAL_REPORT: {
            AttributionState.EXPORT_PROCESS,
            AttributionState.TERMINATED,
        },
        AttributionState.EXPORT_PROCESS: {
            AttributionState.FINAL_REPORT,
            AttributionState.TERMINATED,
        },

        # 异常状态可以转到人工输入（降级）
        AttributionState.ALGO_ERROR: {
            AttributionState.HUMAN_INPUT,
            AttributionState.TERMINATED,
        },
        AttributionState.DATA_MISSING: {
            AttributionState.HUMAN_INPUT,
            AttributionState.TERMINATED,
        },
    }

    def __init__(
        self,
        session_id: str,
        initial_state: AttributionState = AttributionState.INIT,
    ):
        """初始化状态机.

        Args:
            session_id: 会话唯一标识
            initial_state: 初始状态，默认为 INIT
        """
        self.session_id = session_id
        self._current_state = initial_state
        self._mode: Optional[AnalysisMode] = None
        self._state_history: list[dict[str, Any]] = []
        self._step_results: dict[int, dict[str, Any]] = {}
        self._context: dict[str, Any] = {}
        self._state_enter_time: float = time.time()

        # 状态变更回调
        self._on_state_change: Optional[Callable[[AttributionState, AttributionState, dict], None]] = None

    @property
    def current_state(self) -> AttributionState:
        """获取当前状态."""
        return self._current_state

    @property
    def mode(self) -> Optional[AnalysisMode]:
        """获取当前分析模式."""
        return self._mode

    @property
    def state_history(self) -> list[dict[str, Any]]:
        """获取状态历史."""
        return self._state_history.copy()

    @property
    def current_step(self) -> Optional[AttributionStep]:
        """获取当前步骤."""
        return get_step_from_state(self._current_state)

    def set_state_change_callback(
        self,
        callback: Callable[[AttributionState, AttributionState, dict], None],
    ) -> None:
        """设置状态变更回调函数.

        Args:
            callback: 回调函数，参数为 (from_state, to_state, context)
        """
        self._on_state_change = callback

    def start(self, mode: AnalysisMode, context: Optional[dict[str, Any]] = None) -> None:
        """启动状态机.

        Args:
            mode: 分析模式（自动/手动）
            context: 初始上下文数据

        Raises:
            StateTransitionError: 如果当前状态不是 INIT
        """
        if self._current_state != AttributionState.INIT:
            raise StateTransitionError(
                "状态机已启动，无法重复启动",
                self._current_state,
                AttributionState.MODE_SELECT,
            )

        self._mode = mode
        if context:
            self._context.update(context)

        # 根据模式跳转到第一步
        first_state = (
            AttributionState.AUTO_STEP1
            if mode == AnalysisMode.AUTO
            else AttributionState.MANUAL_STEP1
        )

        self._transition(AttributionState.MODE_SELECT, {"selected_mode": mode.value})
        self._transition(first_state, {})

    def transition_to(
        self,
        target_state: AttributionState,
        step_result: Optional[dict[str, Any]] = None,
    ) -> None:
        """状态流转到目标状态.

        Args:
            target_state: 目标状态
            step_result: 当前步骤的结果数据

        Raises:
            StateTransitionError: 如果流转不合法
        """
        # 检查流转是否合法
        valid_targets = self.VALID_TRANSITIONS.get(self._current_state, set())
        if target_state not in valid_targets:
            raise StateTransitionError(
                f"非法的状态流转",
                self._current_state,
                target_state,
            )

        # 保存步骤结果
        if step_result and self.current_step:
            self._step_results[self.current_step.value] = step_result

        # 执行流转
        self._transition(target_state, step_result or {})

    def _transition(self, new_state: AttributionState, context_update: dict) -> None:
        """执行状态流转."""
        old_state = self._current_state

        # 记录历史
        self._state_history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": time.time(),
            "duration": time.time() - self._state_enter_time,
            "context": context_update,
        })

        # 更新状态
        self._current_state = new_state
        self._state_enter_time = time.time()
        self._context.update(context_update)

        # 触发回调
        if self._on_state_change:
            self._on_state_change(old_state, new_state, self._context)

    def can_transition_to(self, target_state: AttributionState) -> bool:
        """检查是否可以流转到目标状态."""
        valid_targets = self.VALID_TRANSITIONS.get(self._current_state, set())
        return target_state in valid_targets

    def get_step_result(self, step: AttributionStep) -> Optional[dict[str, Any]]:
        """获取指定步骤的结果."""
        return self._step_results.get(step.value)

    def get_all_step_results(self) -> dict[int, dict[str, Any]]:
        """获取所有步骤的结果."""
        return self._step_results.copy()

    def set_context(self, key: str, value: Any) -> None:
        """设置上下文数据."""
        self._context[key] = value

    def get_context(self, key: str, default: Any = None) -> Any:
        """获取上下文数据."""
        return self._context.get(key, default)

    def is_auto(self) -> bool:
        """检查是否为自动模式."""
        return is_auto_state(self._current_state)

    def is_manual(self) -> bool:
        """检查是否为手动模式."""
        return is_manual_state(self._current_state)

    def is_error(self) -> bool:
        """检查是否为异常状态."""
        return is_error_state(self._current_state)

    def is_terminal(self) -> bool:
        """检查是否为终止状态."""
        return is_terminal_state(self._current_state)

    def can_export_process(self) -> bool:
        """检查是否可以导出过程报告."""
        return can_export_process_report(self._current_state)

    def can_export_full(self) -> bool:
        """检查是否可以导出完整报告."""
        return can_export_full_report(self._current_state)

    def to_dict(self) -> dict[str, Any]:
        """将状态机状态导出为字典."""
        return {
            "session_id": self.session_id,
            "current_state": self._current_state.value,
            "mode": self._mode.value if self._mode else None,
            "current_step": self.current_step.value if self.current_step else None,
            "state_history": self._state_history,
            "step_results": self._step_results,
            "context": self._context,
            "is_terminal": self.is_terminal(),
            "can_export_process": self.can_export_process(),
            "can_export_full": self.can_export_full(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttributionStateMachine":
        """从字典恢复状态机."""
        sm = cls(
            session_id=data["session_id"],
            initial_state=AttributionState(data["current_state"]),
        )
        sm._mode = AnalysisMode(data["mode"]) if data.get("mode") else None
        sm._state_history = data.get("state_history", [])
        sm._step_results = data.get("step_results", {})
        sm._context = data.get("context", {})
        return sm

"""状态机模块.

提供 GMV 归因系统的状态管理功能。
"""

from __future__ import annotations

from .machine import AttributionStateMachine, StateTransitionError
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

__all__ = [
    # 状态机核心
    "AttributionStateMachine",
    "StateTransitionError",
    # 状态定义
    "AttributionState",
    "AnalysisMode",
    "AttributionStep",
    # 状态判断函数
    "is_auto_state",
    "is_manual_state",
    "is_error_state",
    "is_terminal_state",
    "get_step_from_state",
    "can_export_process_report",
    "can_export_full_report",
]

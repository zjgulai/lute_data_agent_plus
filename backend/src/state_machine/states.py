"""状态机状态定义.

定义 GMV 归因系统的所有可能状态。
"""

from __future__ import annotations

from enum import Enum, auto


class AttributionState(str, Enum):
    """归因分析状态枚举.

    状态流转图：
    INIT -> MODE_SELECT -> (AUTO_STEP1~4 | MANUAL_STEP1~4) -> LLM_NARRATIVE -> HUMAN_INPUT -> FINAL_REPORT

    异常分支：
    - 任何算法错误 -> ALGO_ERROR -> HUMAN_INPUT
    - 数据缺失 -> DATA_MISSING -> HUMAN_INPUT
    """

    # 初始状态
    INIT = "INIT"
    MODE_SELECT = "MODE_SELECT"

    # 自动模式
    AUTO_STEP1 = "AUTO_STEP1"
    AUTO_STEP2 = "AUTO_STEP2"
    AUTO_STEP3 = "AUTO_STEP3"
    AUTO_STEP4 = "AUTO_STEP4"
    AUTO_SUMMARY = "AUTO_SUMMARY"

    # 手动模式
    MANUAL_STEP1 = "MANUAL_STEP1"
    MANUAL_STEP2 = "MANUAL_STEP2"
    MANUAL_STEP3 = "MANUAL_STEP3"
    MANUAL_STEP4 = "MANUAL_STEP4"

    # LLM 交互状态
    LLM_EXPLAIN_1 = "LLM_EXPLAIN_1"
    LLM_EXPLAIN_2 = "LLM_EXPLAIN_2"
    LLM_EXPLAIN_3 = "LLM_EXPLAIN_3"
    LLM_EXPLAIN_4 = "LLM_EXPLAIN_4"
    LLM_NARRATIVE = "LLM_NARRATIVE"

    # 人工输入与报告
    HUMAN_INPUT = "HUMAN_INPUT"
    FINAL_REPORT = "FINAL_REPORT"

    # 导出状态
    EXPORT_PROCESS = "EXPORT_PROCESS"

    # 异常状态
    ALGO_ERROR = "ALGO_ERROR"
    DATA_MISSING = "DATA_MISSING"

    # 终止状态
    TERMINATED = "TERMINATED"


class AnalysisMode(str, Enum):
    """分析模式枚举."""

    AUTO = "auto"  # 自动模式：3-5秒完成全部分析
    MANUAL = "manual"  # 手动模式：每步暂停等待确认


class AttributionStep(int, Enum):
    """归因分析步骤枚举."""

    STEP_1 = 1  # GMV第一层拆解
    STEP_2 = 2  # 子维度熵减计算与交叉校验
    STEP_3 = 3  # 动作指标定位
    STEP_4 = 4  # 请求人工结论


def get_step_from_state(state: AttributionState) -> AttributionStep | None:
    """从状态获取当前步骤.

    Args:
        state: 当前状态

    Returns:
        对应的步骤，如果不是步骤状态则返回 None
    """
    step_map = {
        # 自动模式
        AttributionState.AUTO_STEP1: AttributionStep.STEP_1,
        AttributionState.AUTO_STEP2: AttributionStep.STEP_2,
        AttributionState.AUTO_STEP3: AttributionStep.STEP_3,
        AttributionState.AUTO_STEP4: AttributionStep.STEP_4,
        # 手动模式
        AttributionState.MANUAL_STEP1: AttributionStep.STEP_1,
        AttributionState.MANUAL_STEP2: AttributionStep.STEP_2,
        AttributionState.MANUAL_STEP3: AttributionStep.STEP_3,
        AttributionState.MANUAL_STEP4: AttributionStep.STEP_4,
    }
    return step_map.get(state)


def is_auto_state(state: AttributionState) -> bool:
    """检查是否为自动模式状态."""
    auto_states = {
        AttributionState.AUTO_STEP1,
        AttributionState.AUTO_STEP2,
        AttributionState.AUTO_STEP3,
        AttributionState.AUTO_STEP4,
        AttributionState.AUTO_SUMMARY,
    }
    return state in auto_states


def is_manual_state(state: AttributionState) -> bool:
    """检查是否为手动模式状态."""
    manual_states = {
        AttributionState.MANUAL_STEP1,
        AttributionState.MANUAL_STEP2,
        AttributionState.MANUAL_STEP3,
        AttributionState.MANUAL_STEP4,
        AttributionState.LLM_EXPLAIN_1,
        AttributionState.LLM_EXPLAIN_2,
        AttributionState.LLM_EXPLAIN_3,
        AttributionState.LLM_EXPLAIN_4,
    }
    return state in manual_states


def is_error_state(state: AttributionState) -> bool:
    """检查是否为异常状态."""
    return state in {AttributionState.ALGO_ERROR, AttributionState.DATA_MISSING}


def is_terminal_state(state: AttributionState) -> bool:
    """检查是否为终止状态."""
    return state in {
        AttributionState.FINAL_REPORT,
        AttributionState.TERMINATED,
    }


def can_export_process_report(state: AttributionState) -> bool:
    """检查当前状态是否允许导出过程报告."""
    allowed_states = {
        AttributionState.AUTO_SUMMARY,
        AttributionState.MANUAL_STEP4,
        AttributionState.LLM_NARRATIVE,
        AttributionState.HUMAN_INPUT,
        AttributionState.ALGO_ERROR,
        AttributionState.FINAL_REPORT,
    }
    return state in allowed_states


def can_export_full_report(state: AttributionState) -> bool:
    """检查当前状态是否允许导出完整报告."""
    return state == AttributionState.FINAL_REPORT

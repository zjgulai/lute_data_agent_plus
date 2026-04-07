"""状态机单元测试."""

from __future__ import annotations

import pytest

from state_machine import (
    AnalysisMode,
    AttributionState,
    AttributionStateMachine,
    AttributionStep,
    StateTransitionError,
)


class TestAttributionStateMachine:
    """状态机核心功能测试."""

    def test_initial_state(self):
        """测试初始状态."""
        sm = AttributionStateMachine(session_id="test-001")
        assert sm.current_state == AttributionState.INIT
        assert sm.mode is None
        assert sm.current_step is None

    def test_start_auto_mode(self):
        """测试启动自动模式."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        assert sm.current_state == AttributionState.AUTO_STEP1
        assert sm.mode == AnalysisMode.AUTO
        assert sm.current_step == AttributionStep.STEP_1
        assert sm.is_auto()
        assert not sm.is_manual()

    def test_start_manual_mode(self):
        """测试启动手动模式."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.MANUAL)

        assert sm.current_state == AttributionState.MANUAL_STEP1
        assert sm.mode == AnalysisMode.MANUAL
        assert sm.current_step == AttributionStep.STEP_1
        assert sm.is_manual()
        assert not sm.is_auto()

    def test_cannot_start_twice(self):
        """测试不能重复启动."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        with pytest.raises(StateTransitionError):
            sm.start(mode=AnalysisMode.AUTO)

    def test_auto_mode_transition(self):
        """测试自动模式状态流转."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        # Step 1 -> Step 2
        sm.transition_to(AttributionState.AUTO_STEP2, {"result": "step1_done"})
        assert sm.current_state == AttributionState.AUTO_STEP2
        assert sm.current_step == AttributionStep.STEP_2

        # Step 2 -> Step 3
        sm.transition_to(AttributionState.AUTO_STEP3)
        assert sm.current_state == AttributionState.AUTO_STEP3

        # Step 3 -> Step 4
        sm.transition_to(AttributionState.AUTO_STEP4)
        assert sm.current_state == AttributionState.AUTO_STEP4

        # Step 4 -> Summary
        sm.transition_to(AttributionState.AUTO_SUMMARY)
        assert sm.current_state == AttributionState.AUTO_SUMMARY

        # Summary -> LLM_NARRATIVE
        sm.transition_to(AttributionState.LLM_NARRATIVE)
        assert sm.current_state == AttributionState.LLM_NARRATIVE

        # LLM_NARRATIVE -> HUMAN_INPUT
        sm.transition_to(AttributionState.HUMAN_INPUT)
        assert sm.current_state == AttributionState.HUMAN_INPUT

        # HUMAN_INPUT -> FINAL_REPORT
        sm.transition_to(AttributionState.FINAL_REPORT)
        assert sm.current_state == AttributionState.FINAL_REPORT
        assert sm.is_terminal()

    def test_manual_mode_transition(self):
        """测试手动模式状态流转."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.MANUAL)

        # Step 1 -> Explain 1
        sm.transition_to(AttributionState.LLM_EXPLAIN_1)
        assert sm.current_state == AttributionState.LLM_EXPLAIN_1

        # Explain 1 -> Step 2
        sm.transition_to(AttributionState.MANUAL_STEP2)
        assert sm.current_state == AttributionState.MANUAL_STEP2

        # Step 2 -> Explain 2
        sm.transition_to(AttributionState.LLM_EXPLAIN_2)
        assert sm.current_state == AttributionState.LLM_EXPLAIN_2

        # Explain 2 -> Step 3
        sm.transition_to(AttributionState.MANUAL_STEP3)
        assert sm.current_state == AttributionState.MANUAL_STEP3

        # Step 3 -> Explain 3
        sm.transition_to(AttributionState.LLM_EXPLAIN_3)
        assert sm.current_state == AttributionState.LLM_EXPLAIN_3

        # Explain 3 -> Step 4
        sm.transition_to(AttributionState.MANUAL_STEP4)
        assert sm.current_state == AttributionState.MANUAL_STEP4

        # Step 4 -> Explain 4
        sm.transition_to(AttributionState.LLM_EXPLAIN_4)
        assert sm.current_state == AttributionState.LLM_EXPLAIN_4

        # Explain 4 -> HUMAN_INPUT
        sm.transition_to(AttributionState.HUMAN_INPUT)
        assert sm.current_state == AttributionState.HUMAN_INPUT

    def test_invalid_transition(self):
        """测试非法状态流转."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        # AUTO_STEP1 不能直接到 HUMAN_INPUT
        with pytest.raises(StateTransitionError):
            sm.transition_to(AttributionState.HUMAN_INPUT)

    def test_error_state_transition(self):
        """测试异常状态流转."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        # Step 1 -> ALGO_ERROR
        sm.transition_to(AttributionState.ALGO_ERROR, {"error": "calculation failed"})
        assert sm.current_state == AttributionState.ALGO_ERROR
        assert sm.is_error()

        # ALGO_ERROR -> HUMAN_INPUT (降级处理)
        sm.transition_to(AttributionState.HUMAN_INPUT)
        assert sm.current_state == AttributionState.HUMAN_INPUT

    def test_step_result_storage(self):
        """测试步骤结果存储."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        step1_result = {"dimension": "区域", "entropy_reduction": 0.74}
        sm.transition_to(AttributionState.AUTO_STEP2, step1_result)

        # 获取步骤结果
        result = sm.get_step_result(AttributionStep.STEP_1)
        assert result == step1_result

    def test_context_management(self):
        """测试上下文管理."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.set_context("user_id", "user-123")
        sm.set_context("tree_config", {"root": "gmv"})

        assert sm.get_context("user_id") == "user-123"
        assert sm.get_context("tree_config") == {"root": "gmv"}
        assert sm.get_context("nonexistent") is None
        assert sm.get_context("nonexistent", "default") == "default"

    def test_state_history(self):
        """测试状态历史记录."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)
        sm.transition_to(AttributionState.AUTO_STEP2)

        history = sm.state_history
        assert len(history) >= 2  # MODE_SELECT + AUTO_STEP1 + AUTO_STEP2

    def test_export_permissions(self):
        """测试导出权限判断."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        # 初始状态不能导出
        assert not sm.can_export_process()
        assert not sm.can_export_full()

        # 流转到可以导出的状态
        sm.transition_to(AttributionState.AUTO_STEP2)
        sm.transition_to(AttributionState.AUTO_STEP3)
        sm.transition_to(AttributionState.AUTO_STEP4)
        sm.transition_to(AttributionState.AUTO_SUMMARY)

        # SUMMARY 可以导出过程报告
        assert sm.can_export_process()
        assert not sm.can_export_full()

        # 到 FINAL_REPORT 可以导出完整报告
        sm.transition_to(AttributionState.LLM_NARRATIVE)
        sm.transition_to(AttributionState.HUMAN_INPUT)
        sm.transition_to(AttributionState.FINAL_REPORT)

        assert sm.can_export_process()
        assert sm.can_export_full()

    def test_to_dict(self):
        """测试序列化为字典."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO, context={"user_id": "u123"})

        data = sm.to_dict()
        assert data["session_id"] == "test-001"
        assert data["current_state"] == "AUTO_STEP1"
        assert data["mode"] == "auto"
        assert data["context"]["user_id"] == "u123"

    def test_from_dict(self):
        """测试从字典恢复."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)
        sm.transition_to(AttributionState.AUTO_STEP2, {"test": "data"})

        data = sm.to_dict()
        restored = AttributionStateMachine.from_dict(data)

        assert restored.session_id == sm.session_id
        assert restored.current_state == sm.current_state
        assert restored.mode == sm.mode

    def test_can_transition_to(self):
        """测试状态流转预判."""
        sm = AttributionStateMachine(session_id="test-001")
        sm.start(mode=AnalysisMode.AUTO)

        assert sm.can_transition_to(AttributionState.AUTO_STEP2)
        assert not sm.can_transition_to(AttributionState.HUMAN_INPUT)


class TestStateHelperFunctions:
    """状态辅助函数测试."""

    def test_is_auto_state(self):
        """测试自动状态判断."""
        from state_machine import is_auto_state

        assert is_auto_state(AttributionState.AUTO_STEP1)
        assert is_auto_state(AttributionState.AUTO_SUMMARY)
        assert not is_auto_state(AttributionState.MANUAL_STEP1)
        assert not is_auto_state(AttributionState.HUMAN_INPUT)

    def test_is_manual_state(self):
        """测试手动状态判断."""
        from state_machine import is_manual_state

        assert is_manual_state(AttributionState.MANUAL_STEP1)
        assert is_manual_state(AttributionState.LLM_EXPLAIN_1)
        assert not is_manual_state(AttributionState.AUTO_STEP1)
        assert not is_manual_state(AttributionState.HUMAN_INPUT)

    def test_get_step_from_state(self):
        """测试从状态获取步骤."""
        from state_machine import get_step_from_state

        assert get_step_from_state(AttributionState.AUTO_STEP1) == AttributionStep.STEP_1
        assert get_step_from_state(AttributionState.MANUAL_STEP2) == AttributionStep.STEP_2
        assert get_step_from_state(AttributionState.HUMAN_INPUT) is None

"""报告导出功能测试.

验证 Word / PDF 生成器和导出逻辑的正确性。
"""

from __future__ import annotations

import asyncio

import pytest

from api.export import _build_session_data, _check_export_permission
from api.session import _orchestrators as session_orchestrators
from report.engine import ReportEngine, ReportFormat, ReportType
from state_machine import AttributionState


def run_async(coro):
    """运行异步协程."""
    return asyncio.run(coro)


class TestReportEngine:
    """测试报告生成引擎."""

    def test_generate_word_process_report(self):
        engine = ReportEngine()
        session_data = {
            "session_id": "test-001",
            "analysis_mode": "auto",
            "current_state": "FINAL_REPORT",
            "start_date": "2026-03-01",
            "end_date": "2026-03-31",
            "comparison_period": "prev_month",
            "generated_at": "2026-04-04 12:00:00",
            "steps": [
                {
                    "step_number": 1,
                    "node_id": "gmv",
                    "node_name": "GMV",
                    "node_type": "operation",
                    "selected_dimension": "区域",
                    "selected_child": "美国",
                    "entropy_results": [{"entropy_reduction_normalized": 0.74}],
                }
            ],
            "conclusion": {
                "reason_type": "budget_cut",
                "detailed_explanation": "预算削减导致 GMV 下滑",
                "involved_departments": ["市场部"],
                "suggested_actions": "增加预算",
                "confidence_level": "high",
            },
        }
        content = run_async(engine.generate(session_data, ReportType.PROCESS, ReportFormat.WORD))
        assert len(content) > 0
        # docx 文件签名
        assert content[:4] == b"PK\x03\x04"

    def test_generate_pdf_full_report(self):
        engine = ReportEngine()
        session_data = {
            "session_id": "test-002",
            "analysis_mode": "manual",
            "current_state": "FINAL_REPORT",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "comparison_period": "prev_month",
            "generated_at": "2026-04-04 12:00:00",
            "steps": [],
            "conclusion": None,
        }
        content = run_async(engine.generate(session_data, ReportType.FULL, ReportFormat.PDF))
        assert len(content) > 0
        # PDF 文件签名
        assert content[:4] == b"%PDF"

    def test_generate_unsupported_format(self):
        engine = ReportEngine()
        with pytest.raises(ValueError, match="不支持的报告格式"):
            run_async(engine.generate({}, ReportType.PROCESS, "txt"))  # type: ignore[arg-type]


class TestExportLogic:
    """测试导出逻辑（不依赖 TestClient）."""

    @pytest.fixture(autouse=True)
    def setup_orchestrator(self):
        """清理并准备 orchestrators."""
        session_orchestrators.clear()
        yield
        session_orchestrators.clear()

    def _create_orchestrator(self, session_id: str, state: str = "FINAL_REPORT"):
        """创建并注册一个测试用的 Orchestrator."""
        from llm import LLMOrchestrator

        orch = LLMOrchestrator(session_id=session_id)
        orch.state_machine._context["start_date"] = "2026-03-01"
        orch.state_machine._context["end_date"] = "2026-03-31"
        orch.state_machine._context["comparison_period"] = "prev_month"
        orch.state_machine._context["human_conclusion"] = {
            "reason_type": "seasonal",
            "detailed_explanation": "季节性因素",
            "confidence_level": "medium",
        }
        orch.state_machine._context["step_1_result"] = {
            "node_id": "gmv",
            "node_name": "GMV",
            "node_type": "operation",
            "selected_dimension": "区域",
            "selected_child": "美国",
            "entropy_results": [{"entropy_reduction_normalized": 0.74}],
        }

        # 手动推进到目标状态
        target_state = getattr(AttributionState, state)
        orch.state_machine._current_state = target_state

        session_orchestrators[session_id] = orch
        return orch

    def test_build_session_data_success(self):
        self._create_orchestrator("test-build-001")
        data = _build_session_data("test-build-001")
        assert data["session_id"] == "test-build-001"
        assert data["analysis_mode"] == "-"  # orch.get_status 返回的 mode 可能为 None
        assert len(data["steps"]) == 1
        assert data["steps"][0]["node_name"] == "GMV"
        assert data["conclusion"]["reason_type"] == "seasonal"

    def test_build_session_data_not_found(self):
        with pytest.raises(Exception) as exc_info:
            _build_session_data("nonexistent")
        assert exc_info.value.status_code == 404  # type: ignore[attr-defined]

    def test_check_export_permission_process_allowed(self):
        status = {"can_export_process": True, "can_export_full": False}
        # 不应抛出异常
        _check_export_permission(status, ReportType.PROCESS)

    def test_check_export_permission_full_forbidden(self):
        status = {"can_export_process": True, "can_export_full": False}
        with pytest.raises(Exception) as exc_info:
            _check_export_permission(status, ReportType.FULL)
        assert exc_info.value.status_code == 403  # type: ignore[attr-defined]

    def test_check_export_permission_process_forbidden(self):
        status = {"can_export_process": False, "can_export_full": False}
        with pytest.raises(Exception) as exc_info:
            _check_export_permission(status, ReportType.PROCESS)
        assert exc_info.value.status_code == 403  # type: ignore[attr-defined]

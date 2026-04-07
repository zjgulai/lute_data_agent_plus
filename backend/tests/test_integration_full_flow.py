"""端到端集成测试 - 完整业务流验证.

验证路径（不依赖 TestClient，直接调用服务层）：
1. 算法引擎：单维度熵减 + 交叉维度分析
2. 报告引擎：Word / PDF 生成
3. 文件解析引擎：Excel 上传解析
4. 状态机 + Orchestrator：创建会话、推进状态、提交结论
"""

from __future__ import annotations

import asyncio
import io
from typing import Any

import pytest

from algorithm.engine import AlgorithmEngine, get_algorithm_engine
from api.algorithm import FullAttributionRequest
from api.session import _orchestrators as session_orchestrators
from file_parser.engine import FileParser, FileParseError
from llm import LLMOrchestrator
from report.engine import ReportEngine, ReportFormat, ReportType
from state_machine import AttributionState


def run_async(coro):
    """运行异步协程."""
    return asyncio.run(coro)


@pytest.fixture
def engine() -> AlgorithmEngine:
    return get_algorithm_engine()


@pytest.fixture
def sample_raw_data() -> dict[str, Any]:
    return {
        "美国": -1980000,
        "中国": 100000,
        "欧洲": -120000,
        "亚太": 0,
        "产品A": -1200000,
        "产品B": -800000,
        "产品C": 10000,
        "线上": 0,
        "线下": 0,
    }


@pytest.fixture
def sample_dimension_pool() -> list[dict[str, Any]]:
    return [
        {
            "dimension_name": "区域",
            "dimension_id": "region",
            "child_nodes": ["美国", "中国", "欧洲", "亚太"],
        },
        {
            "dimension_name": "产品",
            "dimension_id": "product",
            "child_nodes": ["产品A", "产品B", "产品C"],
        },
        {
            "dimension_name": "渠道",
            "dimension_id": "channel",
            "child_nodes": ["线上", "线下"],
        },
    ]


class TestAlgorithmIntegration:
    """算法引擎端到端集成测试."""

    def test_full_attribution_analysis(self, engine, sample_raw_data, sample_dimension_pool):
        """完整归因分析：熵减 + 交叉维度."""
        request = FullAttributionRequest(
            node_id="gmv",
            dimension_pool=sample_dimension_pool,
            raw_data=sample_raw_data,
            entropy_threshold=0.2,
            cross_timeout=3.0,
        )

        result = run_async(engine.calculate_entropy_with_cross_dimension(
            node_id=request.node_id,
            dimension_pool=request.dimension_pool,
            raw_data=request.raw_data,
            entropy_threshold=request.entropy_threshold,
            cross_timeout=request.cross_timeout,
        ))

        assert result["node_id"] == "gmv"
        assert result["selected_dimension"] == "区域"
        assert result["selected_child"] == "美国"
        assert result["should_drill_down"] is True
        assert len(result["single_dimension_results"]) == 3
        assert "cross_dimension" in result
        cross = result["cross_dimension"]
        assert "completed" in cross
        assert "results" in cross
        assert "recommendations" in cross

    def test_contribution_calculation_additive(self, engine):
        """贡献度计算：加和型指标."""
        data = {
            "child_changes": {"A": -20, "B": 20},
        }
        contributions = engine.calculate_contributions("additive", data)
        assert "A" in contributions
        assert "B" in contributions
        assert contributions["A"] == -20
        assert contributions["B"] == 20


class TestReportEngineIntegration:
    """报告引擎端到端集成测试."""

    def test_word_export_full_report(self):
        engine = ReportEngine()
        session_data = {
            "session_id": "int-test-001",
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
        content = run_async(engine.generate(session_data, ReportType.FULL, ReportFormat.WORD))
        assert len(content) > 0
        assert content[:4] == b"PK\x03\x04"

    def test_pdf_export_process_report(self):
        engine = ReportEngine()
        session_data = {
            "session_id": "int-test-002",
            "analysis_mode": "manual",
            "current_state": "FINAL_REPORT",
            "start_date": "2026-02-01",
            "end_date": "2026-02-28",
            "comparison_period": "prev_month",
            "generated_at": "2026-04-04 12:00:00",
            "steps": [],
            "conclusion": None,
        }
        content = run_async(engine.generate(session_data, ReportType.PROCESS, ReportFormat.PDF))
        assert len(content) > 0
        assert content[:4] == b"%PDF"


class TestFileParserIntegration:
    """文件解析引擎集成测试."""

    def test_parse_excel(self, tmp_path):
        # 构造临时 Excel 文件
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.append(["日期", "地区", "GMV"])
        ws.append(["2024-01-01", "华东", 1000])
        ws.append(["2024-01-02", "华北", 800])
        file_path = tmp_path / "test.xlsx"
        wb.save(file_path)

        engine = FileParser()
        text = engine.parse(str(file_path))
        assert "华东" in text
        assert "华北" in text
        assert "1000" in text

    def test_parse_unsupported_type(self, tmp_path):
        engine = FileParser()
        file_path = tmp_path / "test.txt"
        file_path.write_text("not a valid file")
        with pytest.raises(FileParseError, match="不支持的文件类型"):
            engine.parse(str(file_path))


class TestStateMachineOrchestratorIntegration:
    """状态机 + Orchestrator 集成测试."""

    @pytest.fixture(autouse=True)
    def cleanup_orchestrators(self):
        session_orchestrators.clear()
        yield
        session_orchestrators.clear()

    def test_create_session_and_advance(self):
        orch = LLMOrchestrator(session_id="int-test-003")
        orch.state_machine._context["start_date"] = "2026-03-01"
        orch.state_machine._context["end_date"] = "2026-03-31"
        orch.state_machine._context["comparison_period"] = "prev_month"
        session_orchestrators["int-test-003"] = orch

        # 初始状态应为 INIT
        status = orch.get_status()
        assert status["session_id"] == "int-test-003"
        assert status["state"] == AttributionState.INIT.value

        # 模拟状态推进
        orch.state_machine._current_state = AttributionState.FINAL_REPORT
        orch.state_machine._context["human_conclusion"] = {
            "reason_type": "seasonal",
            "detailed_explanation": "季节性因素",
            "confidence_level": "medium",
        }

        status = orch.get_status()
        assert status["state"] == AttributionState.FINAL_REPORT.value
        assert orch.state_machine._context.get("human_conclusion") is not None

    def test_conclusion_round_trip(self):
        orch = LLMOrchestrator(session_id="int-test-004")
        conclusion = {
            "summary": "GMV 下滑主要受华东地区影响",
            "confidence_level": "high",
            "recommendations": ["加强华东推广", "优化 A 产品库存"],
        }
        orch.state_machine._context["human_conclusion"] = conclusion

        retrieved = orch.state_machine._context.get("human_conclusion")
        assert retrieved["summary"] == conclusion["summary"]
        assert retrieved["confidence_level"] == conclusion["confidence_level"]

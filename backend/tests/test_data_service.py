"""数据服务模块测试."""

from pathlib import Path

import pandas as pd
import pytest

from data_service import DataReadingError, ExcelDataReader


class TestExcelDataReader:
    """Excel 数据读取器测试."""

    @pytest.fixture
    def reader(self):
        """返回配置好的读取器."""
        testdata_dir = Path(__file__).parent.parent / "testdata"
        return ExcelDataReader(data_dir=testdata_dir)

    def test_read_sample_gmv(self, reader: ExcelDataReader) -> None:
        """测试读取 GMV 数据."""
        df = reader.read_sheet("sample_gmv.xlsx", "Sheet1")

        assert not df.empty
        assert "date" in df.columns
        assert "gmv" in df.columns
        assert "uv" in df.columns
        assert "conversion_rate" in df.columns
        assert "avg_order_value" in df.columns

    def test_read_with_required_fields_success(self, reader: ExcelDataReader) -> None:
        """测试读取时验证必需字段（成功）."""
        df = reader.read_sheet(
            "sample_gmv.xlsx",
            "Sheet1",
            required_fields=["date", "gmv", "uv"],
        )
        assert not df.empty

    def test_read_with_required_fields_missing(self, reader: ExcelDataReader) -> None:
        """测试读取时验证必需字段（失败）."""
        with pytest.raises(DataReadingError) as exc_info:
            reader.read_sheet(
                "sample_gmv.xlsx",
                "Sheet1",
                required_fields=["date", "gmv", "nonexistent_field"],
            )

        assert "nonexistent_field" in str(exc_info.value)
        assert "nonexistent_field" in exc_info.value.missing_fields

    def test_read_nonexistent_file(self, reader: ExcelDataReader) -> None:
        """测试读取不存在的文件."""
        with pytest.raises(DataReadingError) as exc_info:
            reader.read_sheet("nonexistent.xlsx", "Sheet1")

        assert "不存在" in str(exc_info.value)

    def test_read_with_filter(self, reader: ExcelDataReader) -> None:
        """测试带过滤条件的读取."""
        df = reader.read_with_filter(
            "sample_region_gmv.xlsx",
            "Sheet1",
            filter_conditions={"region": "Asia_Pacific"},
        )

        assert not df.empty
        assert all(df["region"] == "Asia_Pacific")

    def test_read_with_date_range(self, reader: ExcelDataReader) -> None:
        """测试带日期范围的读取."""
        df = reader.read_with_filter(
            "sample_gmv.xlsx",
            "Sheet1",
            date_range=("2026-02-01", "2026-02-28"),
        )

        assert not df.empty
        # 验证只包含 2 月数据
        df["date"] = pd.to_datetime(df["date"])
        assert all(df["date"].dt.month == 2)

    def test_aggregate_metric_sum(self, reader: ExcelDataReader) -> None:
        """测试 SUM 聚合."""
        result = reader.aggregate_metric(
            "sample_gmv.xlsx",
            "Sheet1",
            metric_field="gmv",
            agg_func="SUM",
        )

        assert isinstance(result, float)
        assert result > 0

    def test_aggregate_metric_avg(self, reader: ExcelDataReader) -> None:
        """测试 AVG 聚合."""
        result = reader.aggregate_metric(
            "sample_gmv.xlsx",
            "Sheet1",
            metric_field="conversion_rate",
            agg_func="AVG",
        )

        assert isinstance(result, float)
        assert 0 < result < 1

    def test_aggregate_with_group_by(self, reader: ExcelDataReader) -> None:
        """测试分组聚合."""
        result = reader.aggregate_metric(
            "sample_region_gmv.xlsx",
            "Sheet1",
            metric_field="gmv",
            agg_func="SUM",
            group_by=["region"],
        )

        assert isinstance(result, pd.DataFrame)
        assert "region" in result.columns
        assert "gmv" in result.columns
        assert len(result) == 4  # 4 个区域


class TestDataReadingError:
    """数据读取异常测试."""

    def test_error_to_dict(self) -> None:
        """测试异常转换为字典."""
        error = DataReadingError(
            message="测试错误",
            missing_fields=["field1", "field2"],
            empty_sheets=["sheet1"],
            source="/path/to/file.xlsx",
        )

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "DATA_MISSING"
        assert error_dict["message"] == "测试错误"
        assert error_dict["missing_fields"] == ["field1", "field2"]
        assert error_dict["empty_sheets"] == ["sheet1"]
        assert error_dict["source"] == "/path/to/file.xlsx"

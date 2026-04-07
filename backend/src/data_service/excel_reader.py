"""Excel 数据读取模块."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Any

import pandas as pd


class DataReadingError(Exception):
    """数据读取异常."""

    def __init__(
        self,
        message: str,
        missing_fields: Optional[list[str]] = None,
        empty_sheets: Optional[list[str]] = None,
        source: Optional[str] = None,
    ):
        super().__init__(message)
        self.missing_fields = missing_fields or []
        self.empty_sheets = empty_sheets or []
        self.source = source

    def to_dict(self) -> dict[str, Any]:
        """转换为字典格式，用于 API 响应."""
        return {
            "error_type": "DATA_MISSING",
            "message": str(self),
            "missing_fields": self.missing_fields,
            "empty_sheets": self.empty_sheets,
            "source": self.source,
        }


class ExcelDataReader:
    """Excel 数据读取器.

    根据指标树配置读取 Excel 文件中的数据。
    """

    def __init__(self, data_dir: str | Path = "./testdata"):
        """初始化读取器.

        Args:
            data_dir: Excel 文件存放目录
        """
        self.data_dir = Path(data_dir)

    def read_sheet(
        self,
        file_name: str,
        sheet_name: str,
        required_fields: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """读取指定工作表.

        Args:
            file_name: Excel 文件名
            sheet_name: 工作表名
            required_fields: 必需字段列表

        Returns:
            DataFrame 数据

        Raises:
            DataReadingError: 文件不存在、字段缺失或数据为空
        """
        file_path = self.data_dir / file_name

        if not file_path.exists():
            raise DataReadingError(
                f"数据文件不存在: {file_path}",
                source=str(file_path),
            )

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
        except ValueError as e:
            raise DataReadingError(
                f"工作表 '{sheet_name}' 不存在: {e}",
                source=str(file_path),
            ) from e

        # 检查空数据
        if df.empty:
            raise DataReadingError(
                f"工作表 '{sheet_name}' 数据为空",
                empty_sheets=[sheet_name],
                source=str(file_path),
            )

        # 检查必需字段
        if required_fields:
            missing = [f for f in required_fields if f not in df.columns]
            if missing:
                raise DataReadingError(
                    f"缺少必需字段: {missing}",
                    missing_fields=missing,
                    source=str(file_path),
                )

        return df

    def read_with_filter(
        self,
        file_name: str,
        sheet_name: str,
        filter_conditions: Optional[dict[str, Any]] = None,
        date_range: Optional[tuple[str, str]] = None,
        date_column: str = "date",
    ) -> pd.DataFrame:
        """读取并过滤数据.

        Args:
            file_name: Excel 文件名
            sheet_name: 工作表名
            filter_conditions: 过滤条件，如 {"region": "Asia_Pacific"}
            date_range: 日期范围 (start, end)，格式 "YYYY-MM-DD"
            date_column: 日期列名

        Returns:
            过滤后的 DataFrame
        """
        df = self.read_sheet(file_name, sheet_name)

        # 日期过滤
        if date_range and date_column in df.columns:
            start_date, end_date = date_range
            df[date_column] = pd.to_datetime(df[date_column])
            df = df[
                (df[date_column] >= start_date) & (df[date_column] <= end_date)
            ]

        # 条件过滤
        if filter_conditions:
            for column, value in filter_conditions.items():
                if column in df.columns:
                    df = df[df[column] == value]

        return df

    def aggregate_metric(
        self,
        file_name: str,
        sheet_name: str,
        metric_field: str,
        agg_func: str = "SUM",
        group_by: Optional[list[str]] = None,
        filter_conditions: Optional[dict[str, Any]] = None,
        date_range: Optional[tuple[str, str]] = None,
    ) -> pd.DataFrame | float:
        """聚合计算指标.

        Args:
            file_name: Excel 文件名
            sheet_name: 工作表名
            metric_field: 指标字段名
            agg_func: 聚合函数 (SUM, AVG, COUNT, MAX, MIN)
            group_by: 分组字段
            filter_conditions: 过滤条件
            date_range: 日期范围

        Returns:
            聚合结果（分组时为 DataFrame，否则为标量）
        """
        df = self.read_with_filter(
            file_name, sheet_name, filter_conditions, date_range
        )

        if metric_field not in df.columns:
            raise DataReadingError(
                f"指标字段 '{metric_field}' 不存在",
                missing_fields=[metric_field],
            )

        # 执行聚合
        agg_func_upper = agg_func.upper()

        if group_by:
            # 确保分组字段存在
            missing_groups = [g for g in group_by if g not in df.columns]
            if missing_groups:
                raise DataReadingError(
                    f"分组字段不存在: {missing_groups}",
                    missing_fields=missing_groups,
                )

            result = df.groupby(group_by)[metric_field].agg(agg_func_upper.lower())
            return result.reset_index()
        else:
            # 标量聚合
            if agg_func_upper == "SUM":
                return float(df[metric_field].sum())
            elif agg_func_upper == "AVG":
                return float(df[metric_field].mean())
            elif agg_func_upper == "COUNT":
                return int(df[metric_field].count())
            elif agg_func_upper == "MAX":
                return float(df[metric_field].max())
            elif agg_func_upper == "MIN":
                return float(df[metric_field].min())
            else:
                raise ValueError(f"不支持的聚合函数: {agg_func}")


def validate_data_source_config(
    df: pd.DataFrame,
    data_source: dict[str, Any],
) -> None:
    """验证数据源配置与 DataFrame 是否匹配.

    Args:
        df: 数据 DataFrame
        data_source: 数据源配置

    Raises:
        DataReadingError: 配置不匹配
    """
    field = data_source.get("field")
    group_by = data_source.get("group_by", [])

    missing = []

    if field and field not in df.columns:
        missing.append(field)

    for g in group_by:
        if g not in df.columns:
            missing.append(g)

    if missing:
        raise DataReadingError(
            f"数据源配置与数据不匹配，缺少字段: {missing}",
            missing_fields=missing,
        )

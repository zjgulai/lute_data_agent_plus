"""数据切片模块：按 dimension_pool 配置进行数据切片."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Any

import pandas as pd

from indicator_tree.models import DataSliceRule, Dimension


@dataclass
class SliceConfiguration:
    """切片配置."""

    dimension: Dimension
    base_period: tuple[str, str]  # (start_date, end_date)
    comparison_period: Optional[tuple[str, str]] = None


class DataSlicer:
    """数据切片器.

    根据指标树的 dimension_pool 配置，对数据进行维度切片。
    """

    def __init__(self, data_reader):
        """初始化切片器.

        Args:
            data_reader: ExcelDataReader 实例
        """
        self.data_reader = data_reader

    def slice_by_dimension(
        self,
        rule: DataSliceRule,
        base_period: tuple[str, str],
        comparison_period: Optional[tuple[str, str]] = None,
    ) -> dict[str, Any]:
        """按维度进行数据切片.

        Args:
            rule: 数据切片规则
            base_period: 基期日期范围 (start, end)
            comparison_period: 对比期日期范围 (start, end)，可选

        Returns:
            切片结果，包含各子类别的当前值和基期值
        """
        # 读取数据
        df = self.data_reader.read_sheet(
            file_name=f"{rule.source_view}.xlsx",
            sheet_name="data",
        )

        # 应用额外过滤
        if rule.filter_template:
            # TODO: 解析并应用 filter_template
            pass

        # 按维度分组计算
        base_data = self._aggregate_by_group(
            df, rule, base_period, rule.group_by_field, rule.metric_field
        )

        result = {
            "dimension_id": rule.group_by_field,
            "base_period": {
                "start": base_period[0],
                "end": base_period[1],
                "values": base_data,
            },
        }

        if comparison_period:
            comparison_data = self._aggregate_by_group(
                df, rule, comparison_period, rule.group_by_field, rule.metric_field
            )
            result["comparison_period"] = {
                "start": comparison_period[0],
                "end": comparison_period[1],
                "values": comparison_data,
            }

            # 计算变化
            changes = self._calculate_changes(base_data, comparison_data)
            result["changes"] = changes

        return result

    def _aggregate_by_group(
        self,
        df: pd.DataFrame,
        rule: DataSliceRule,
        date_range: tuple[str, str],
        group_by_field: str,
        metric_field: str,
    ) -> dict[str, float]:
        """按组聚合数据.

        Args:
            df: 原始数据
            rule: 切片规则
            date_range: 日期范围
            group_by_field: 分组字段
            metric_field: 指标字段

        Returns:
            各组的聚合值
        """
        # 日期过滤
        if "date" in df.columns:
            df = df.copy()
            df["date"] = pd.to_datetime(df["date"])
            mask = (df["date"] >= date_range[0]) & (df["date"] <= date_range[1])
            df = df[mask]

        # 分组聚合
        grouped = df.groupby(group_by_field)[metric_field].agg(rule.agg_func)
        return grouped.to_dict()

    def _calculate_changes(
        self,
        base_values: dict[str, float],
        comparison_values: dict[str, float],
    ) -> dict[str, dict[str, float]]:
        """计算变化.

        Args:
            base_values: 基期值
            comparison_values: 对比期值

        Returns:
            各组的变化情况
        """
        changes = {}
        all_keys = set(base_values.keys()) | set(comparison_values.keys())

        for key in all_keys:
            base = base_values.get(key, 0)
            comparison = comparison_values.get(key, 0)
            change = base - comparison
            change_rate = (change / comparison) if comparison != 0 else 0

            changes[key] = {
                "base_value": base,
                "comparison_value": comparison,
                "change": change,
                "change_rate": change_rate,
            }

        return changes

    def prepare_entropy_input(
        self,
        dimension: Dimension,
        base_period: tuple[str, str],
        comparison_period: tuple[str, str],
    ) -> dict[str, float]:
        """准备熵减算法的输入数据.

        Args:
            dimension: 维度配置
            base_period: 基期
            comparison_period: 对比期

        Returns:
            各子类别的带符号波动贡献
        """
        if not dimension.data_slice_rule:
            raise ValueError(f"维度 '{dimension.dimension_id}' 未配置 data_slice_rule")

        rule = dimension.data_slice_rule
        result = self.slice_by_dimension(rule, base_period, comparison_period)

        # 提取变化值
        contributions = {}
        if "changes" in result:
            for key, change_info in result["changes"].items():
                contributions[key] = change_info["change"]

        return contributions

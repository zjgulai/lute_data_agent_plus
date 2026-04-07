"""算法引擎主类.

整合熵减计算、贡献度计算、交叉维度校验的核心算法功能。
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from data_service.exceptions import DataMissingError

from .contribution import (
    calculate_additive_contribution,
    calculate_multiplicative_contribution,
    calculate_pseudo_weight_contribution,
    format_contribution_report,
)
from .cross_dimension import check_cross_dimensions
from .entropy import (
    calculate_dimension_entropy_reduction,
    select_best_split_dimension,
)


class AlgorithmEngine:
    """算法引擎主类.

    提供统一的算法计算接口，包括：
    - 单维度熵减计算
    - 最佳切分维度选择
    - 贡献度计算（加和型/乘积型/伪权重型）
    - 交叉维度校验

    Example:
        >>> engine = AlgorithmEngine()
        >>> result = engine.calculate_entropy_for_node(
        ...     node_id="gmv",
        ...     dimension_pool=dimension_pool,
        ...     raw_data=raw_data,
        ... )
    """

    def __init__(self, default_entropy_threshold: float = 0.2):
        """初始化算法引擎.

        Args:
            default_entropy_threshold: 默认熵减阈值
        """
        self.default_entropy_threshold = default_entropy_threshold

    def calculate_entropy_reduction(
        self,
        dimension_name: str,
        contributions: dict[str, float],
        entropy_threshold: Optional[float] = None,
    ) -> dict[str, Any]:
        """计算单个维度的熵减.

        Args:
            dimension_name: 维度名称
            contributions: 各子类别的带符号贡献值
            entropy_threshold: 熵减阈值，None则使用默认值

        Returns:
            维度熵减分析结果
        """
        threshold = entropy_threshold if entropy_threshold is not None else self.default_entropy_threshold
        return calculate_dimension_entropy_reduction(dimension_name, contributions, threshold)

    def select_best_dimension(
        self,
        candidate_dimensions: list[dict[str, Any]],
        entropy_threshold: Optional[float] = None,
    ) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
        """从多个候选维度中选择最佳切分维度.

        Args:
            candidate_dimensions: 候选维度列表
            entropy_threshold: 熵减阈值

        Returns:
            (最佳维度结果, 所有维度结果列表)
        """
        threshold = entropy_threshold if entropy_threshold is not None else self.default_entropy_threshold
        return select_best_split_dimension(candidate_dimensions, threshold)

    def calculate_contributions(
        self,
        indicator_type: str,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        """计算指标贡献度.

        Args:
            indicator_type: 指标类型，可选 "additive" | "multiplicative" | "pseudo_weight"
            data: 计算所需数据

        Returns:
            贡献度计算结果

        Raises:
            ValueError: 不支持的指标类型
        """
        if indicator_type == "additive":
            return calculate_additive_contribution(
                data.get("child_changes", {}),
                data.get("weights"),
            )

        elif indicator_type == "multiplicative":
            return calculate_multiplicative_contribution(
                data.get("base_values", {}),
                data.get("current_values", {}),
                data.get("parent_base", 0),
                data.get("include_interaction", False),
            )

        elif indicator_type == "pseudo_weight":
            return calculate_pseudo_weight_contribution(
                data.get("indicator_change", 0),
                data.get("pseudo_weight", 0),
                data.get("parent_base", 0),
            )

        else:
            raise ValueError(f"不支持的指标类型: {indicator_type}")

    async def calculate_entropy_with_cross_dimension(
        self,
        node_id: str,
        dimension_pool: list[dict[str, Any]],
        raw_data: dict[str, Any],
        entropy_threshold: Optional[float] = None,
        cross_timeout: float = 3.0,
        historical_pairs: Optional[list[tuple[str, str]]] = None,
        manual_pairs: Optional[list[tuple[str, str]]] = None,
    ) -> dict[str, Any]:
        """计算熵减并执行交叉维度校验.

        这是核心归因算法接口，执行以下步骤：
        1. 计算所有单维度的熵减
        2. 选择最佳切分维度
        3. 异步执行交叉维度校验（带3秒超时）

        Args:
            node_id: 当前节点ID
            dimension_pool: 维度池配置
            raw_data: 原始数据，包含各维度的贡献值
            entropy_threshold: 熵减阈值
            cross_timeout: 交叉维度计算超时时间（秒）
            historical_pairs: 历史高频交叉组合
            manual_pairs: 手动指定的交叉组合

        Returns:
            完整的归因分析结果

        Raises:
            DataMissingError: 数据缺失
        """
        threshold = entropy_threshold if entropy_threshold is not None else self.default_entropy_threshold

        # 1. 验证数据完整性
        if not dimension_pool:
            raise DataMissingError(
                message="维度池为空",
                missing_fields=["dimension_pool"],
            )

        # 2. 构建候选维度列表并计算熵减
        candidate_dimensions = []
        for dim in dimension_pool:
            dim_name = dim.get("dimension_name", dim.get("dimension_id", ""))
            child_nodes = dim.get("child_nodes", [])

            # 从 raw_data 中提取贡献值
            contributions = {}
            for child_id in child_nodes:
                contribution = raw_data.get(child_id, 0)
                contributions[child_id] = contribution

            if contributions:
                candidate_dimensions.append({
                    "dimension_name": dim_name,
                    "contributions": contributions,
                })

        if not candidate_dimensions:
            raise DataMissingError(
                message="没有有效的候选维度",
                missing_fields=["contributions"],
            )

        # 3. 计算单维度熵减并选择最佳维度
        best_dim, all_results = self.select_best_dimension(candidate_dimensions, threshold)

        # 4. 异步执行交叉维度校验
        cross_result = await check_cross_dimensions(
            dimension_pool=dimension_pool,
            raw_data=raw_data,
            single_dimension_results=all_results,
            entropy_threshold=threshold,
            timeout_seconds=cross_timeout,
            historical_pairs=historical_pairs,
            manual_pairs=manual_pairs,
        )

        # 5. 组装完整结果
        return {
            "node_id": node_id,
            "entropy_threshold": threshold,
            "selected_dimension": best_dim["dimension"] if best_dim else None,
            "selected_child": best_dim["top_child"] if best_dim else None,
            "should_drill_down": best_dim is not None and best_dim.get("is_key_dimension", False),
            "single_dimension_results": all_results,
            "cross_dimension": cross_result,
            "summary": self._generate_summary(best_dim, cross_result),
        }

    def _generate_summary(
        self,
        best_dim: Optional[dict[str, Any]],
        cross_result: dict[str, Any],
    ) -> str:
        """生成归因分析摘要.

        Args:
            best_dim: 最佳维度结果
            cross_result: 交叉维度结果

        Returns:
            自然语言摘要
        """
        if not best_dim:
            return "未找到关键维度，建议停止下钻或人工分析。"

        dim_name = best_dim["dimension"]
        er_norm = best_dim["entropy_reduction_normalized"]
        top_child = best_dim.get("top_child", "")
        top_share = best_dim.get("top_child_share", 0)

        summary = f"维度『{dim_name}』的熵减为{er_norm:.1%}，"
        summary += f"其中『{top_child}』贡献了{top_share:.1%}的波动份额。"

        # 添加交叉维度信息
        if cross_result.get("completed") and cross_result.get("recommendations"):
            rec = cross_result["recommendations"][0]
            summary += f"交叉维度『{rec['cross_dimension']}』显示『{rec['top_combination']}』"
            summary += f"有显著影响，建议关注。"

        return summary

    def format_report(
        self,
        contributions: dict[str, float],
        total_gmv: float,
        unit: str = "元",
    ) -> list[dict[str, Any]]:
        """格式化贡献度报告.

        Args:
            contributions: 各指标贡献度
            total_gmv: GMV总值
            unit: 金额单位

        Returns:
            格式化后的报告数据
        """
        return format_contribution_report(contributions, total_gmv, unit)


# 全局引擎实例（单例模式）
_engine: Optional[AlgorithmEngine] = None


def get_algorithm_engine() -> AlgorithmEngine:
    """获取算法引擎单例实例.

    Returns:
        AlgorithmEngine 实例
    """
    global _engine
    if _engine is None:
        _engine = AlgorithmEngine()
    return _engine

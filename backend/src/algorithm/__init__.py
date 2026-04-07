"""算法引擎模块.

提供 GMV 归因分析的核心算法功能：
- 熵减计算：基于维度贡献集中度选择最佳切分维度
- 贡献度计算：支持加和型、乘积型、伪权重型指标
- 交叉维度校验：捕捉单维度拆解遗漏的交互效应
"""

from __future__ import annotations

from .contribution import (
    calculate_additive_contribution,
    calculate_multiplicative_contribution,
    calculate_pseudo_weight_contribution,
    format_contribution_report,
)
from .cross_dimension import (
    calculate_cross_dimension_entropy_reduction,
    check_cross_dimensions,
    generate_cross_dimension_candidates,
)
from .entropy import (
    calculate_dimension_entropy_reduction,
    calculate_distribution_entropy,
    select_best_split_dimension,
)
from .engine import AlgorithmEngine, get_algorithm_engine

__all__ = [
    # 熵减计算
    "calculate_distribution_entropy",
    "calculate_dimension_entropy_reduction",
    "select_best_split_dimension",
    # 贡献度计算
    "calculate_additive_contribution",
    "calculate_multiplicative_contribution",
    "calculate_pseudo_weight_contribution",
    "format_contribution_report",
    # 交叉维度
    "calculate_cross_dimension_entropy_reduction",
    "check_cross_dimensions",
    "generate_cross_dimension_candidates",
    # 引擎
    "AlgorithmEngine",
    "get_algorithm_engine",
]

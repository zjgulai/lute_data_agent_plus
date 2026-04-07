"""熵减算法实现.

基于维度贡献集中度的归因决策树核心算法。
"""

from __future__ import annotations

import math
from typing import Optional, Any


def calculate_distribution_entropy(probabilities: list[float]) -> float:
    """计算概率分布的香农熵（以2为底）.

    Args:
        probabilities: 概率分布列表，总和应为 1

    Returns:
        香农熵值

    Example:
        >>> calculate_distribution_entropy([0.5, 0.5])
        1.0
        >>> calculate_distribution_entropy([1.0, 0.0])
        0.0
    """
    entropy = 0.0
    for p in probabilities:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def calculate_dimension_entropy_reduction(
    dimension_name: str,
    contributions: dict[str, float],
    entropy_threshold: float = 0.2,
) -> dict[str, Any]:
    """计算某个维度的熵减得分.

    Args:
        dimension_name: 维度名称，如 "区域"
        contributions: 各子类别的带符号波动贡献值
        entropy_threshold: 熵减阈值，大于此值才视为关键维度

    Returns:
        该维度的熵减分析结果

    Example:
        >>> contributions = {"美国": -1980000, "中国": 100000, "欧洲": -120000, "亚太": 0}
        >>> result = calculate_dimension_entropy_reduction("区域", contributions)
        >>> result["entropy_reduction_normalized"]
        0.74
    """
    # 1. 计算绝对贡献份额分布
    abs_contributions = {k: abs(v) for k, v in contributions.items()}
    total_abs = sum(abs_contributions.values())

    if total_abs == 0:
        return {
            "dimension": dimension_name,
            "num_categories": len(contributions),
            "entropy": 0.0,
            "max_entropy": math.log2(len(contributions)) if contributions else 0,
            "entropy_reduction": 0.0,
            "entropy_reduction_normalized": 0.0,
            "is_key_dimension": False,
            "error": "所有子类别绝对贡献均为 0",
            "child_details": [],
        }

    probabilities = [v / total_abs for v in abs_contributions.values()]
    m = len(contributions)

    # 2. 计算熵减
    h_dimension = calculate_distribution_entropy(probabilities)
    h_max = math.log2(m)
    entropy_reduction = h_max - h_dimension
    er_norm = entropy_reduction / h_max if h_max > 0 else 0.0

    # 3. 识别最大贡献子类别
    max_child = max(abs_contributions, key=abs_contributions.get)
    max_share = abs_contributions[max_child] / total_abs

    # 4. 构建子类别详情
    child_details = [
        {
            "child_name": k,
            "signed_contribution": v,
            "abs_contribution": abs_contributions[k],
            "share": round(abs_contributions[k] / total_abs, 4),
        }
        for k, v in contributions.items()
    ]

    # 按绝对贡献降序排列
    child_details.sort(key=lambda x: x["abs_contribution"], reverse=True)

    return {
        "dimension": dimension_name,
        "num_categories": m,
        "entropy": round(h_dimension, 4),
        "max_entropy": round(h_max, 4),
        "entropy_reduction": round(entropy_reduction, 4),
        "entropy_reduction_normalized": round(er_norm, 4),
        "is_key_dimension": er_norm > entropy_threshold,
        "top_child": max_child,
        "top_child_share": round(max_share, 4),
        "child_details": child_details,
    }


def select_best_split_dimension(
    candidate_dimensions: list[dict[str, Any]],
    entropy_threshold: float = 0.2,
) -> tuple[Optional[dict[str, Any]], list[dict[str, Any]]]:
    """从多个候选维度中选择熵减最大的维度作为优先切分维度.

    Args:
        candidate_dimensions: 候选维度列表，每个元素包含:
            - dimension_name: 维度名称
            - contributions: dict, 子类别贡献值
        entropy_threshold: 熵减阈值

    Returns:
        (最佳维度结果, 所有维度结果列表)
        如果没有关键维度，最佳维度结果为 None
    """
    results = []
    for dim in candidate_dimensions:
        result = calculate_dimension_entropy_reduction(
            dim["dimension_name"],
            dim["contributions"],
            entropy_threshold,
        )
        results.append(result)

    # 按归一化熵减降序排列
    results.sort(key=lambda x: x["entropy_reduction_normalized"], reverse=True)

    if not results or not results[0]["is_key_dimension"]:
        return None, results

    return results[0], results


def calculate_entropy_reduction_for_node(
    node_id: str,
    dimension_pool: list[dict[str, Any]],
    raw_data: dict[str, Any],
    entropy_threshold: float = 0.2,
) -> dict[str, Any]:
    """为指标树节点计算熵减.

    Args:
        node_id: 当前节点 ID
        dimension_pool: 维度池配置
        raw_data: 原始数据
        entropy_threshold: 熵减阈值

    Returns:
        完整的熵减计算结果
    """
    # 构建候选维度列表
    candidate_dimensions = []
    for dim in dimension_pool:
        dim_id = dim["dimension_id"]
        child_nodes = dim.get("child_nodes", [])
        
        # 从 raw_data 中提取各子类别的贡献
        contributions = {}
        for child_id in child_nodes:
            # TODO: 从 raw_data 中根据 child_id 查找对应的贡献值
            # 这里假设 raw_data 中已经有计算好的贡献值
            contributions[child_id] = raw_data.get(child_id, 0)
        
        candidate_dimensions.append({
            "dimension_name": dim.get("dimension_name", dim_id),
            "contributions": contributions,
        })

    # 选择最佳维度
    best_dim, all_results = select_best_split_dimension(
        candidate_dimensions, entropy_threshold
    )

    return {
        "node_id": node_id,
        "selected_dimension": best_dim["dimension"] if best_dim else None,
        "selected_child": best_dim["top_child"] if best_dim else None,
        "entropy_results": all_results,
    }

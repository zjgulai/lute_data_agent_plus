"""交叉维度校验引擎.

支持两个业务维度组合切分后的异常波动集中度计算，
用于捕捉单维度拆解遗漏的关键交互效应。
"""

from __future__ import annotations

import asyncio
from typing import Optional, Any

from .entropy import calculate_dimension_entropy_reduction


async def calculate_cross_dimension_entropy_reduction(
    dimension_a_name: str,
    dimension_b_name: str,
    contributions: dict[str, dict[str, float]],
    entropy_threshold: float = 0.2,
) -> dict[str, Any]:
    """计算两个维度的交叉熵减.

    构建笛卡尔积组合，计算交叉维度的熵减得分。

    Args:
        dimension_a_name: 维度A名称，如 "区域"
        dimension_b_name: 维度B名称，如 "产品"
        contributions: 嵌套字典，格式为 {a_value: {b_value: contribution}}
            如 {"美国": {"A产品": -1500000, "B产品": -480000}}
        entropy_threshold: 熵减阈值

    Returns:
        交叉维度熵减分析结果
    """
    # 构建笛卡尔积组合
    cross_contributions = {}
    for a_value, b_dict in contributions.items():
        for b_value, contribution in b_dict.items():
            cross_key = f"{a_value}×{b_value}"
            cross_contributions[cross_key] = contribution

    # 使用标准熵减计算
    cross_result = calculate_dimension_entropy_reduction(
        f"{dimension_a_name}×{dimension_b_name}",
        cross_contributions,
        entropy_threshold,
    )

    # 解析最佳组合
    top_combination = cross_result.get("top_child", "")
    top_a, top_b = "", ""
    if "×" in top_combination:
        parts = top_combination.split("×")
        if len(parts) == 2:
            top_a, top_b = parts

    return {
        "dimension_a": dimension_a_name,
        "dimension_b": dimension_b_name,
        "cross_dimension_name": f"{dimension_a_name}×{dimension_b_name}",
        "num_combinations": len(cross_contributions),
        "entropy": cross_result["entropy"],
        "max_entropy": cross_result["max_entropy"],
        "entropy_reduction": cross_result["entropy_reduction"],
        "entropy_reduction_normalized": cross_result["entropy_reduction_normalized"],
        "is_key_cross_dimension": cross_result["is_key_dimension"],
        "top_combination": top_combination,
        "top_combination_share": cross_result.get("top_child_share", 0),
        "top_a_value": top_a,
        "top_b_value": top_b,
        "child_details": cross_result["child_details"],
    }


def generate_cross_dimension_candidates(
    single_dimension_results: list[dict[str, Any]],
    historical_pairs: list[tuple[str, str]] | None = None,
    manual_pairs: list[tuple[str, str]] | None = None,
    max_candidates: int = 5,
) -> list[tuple[str, str]]:
    """生成候选交叉维度组合.

    优先级：
    - P0: 历史高频组合（最多2个）
    - P1: 手动指定组合（最多2个）
    - P2: 单维度熵减前三的自动组合（最多1个）
    - 总计不超过5个

    Args:
        single_dimension_results: 单维度熵减结果列表
        historical_pairs: 历史高频交叉组合，如 [("区域", "产品")]
        manual_pairs: 手动指定的交叉组合
        max_candidates: 最大候选数，默认5

    Returns:
        候选交叉维度组合列表
    """
    candidates = []
    used_pairs = set()

    # P0: 历史高频组合（最多2个）
    if historical_pairs:
        for pair in historical_pairs[:2]:
            normalized = tuple(sorted(pair))
            if normalized not in used_pairs:
                candidates.append(pair)
                used_pairs.add(normalized)

    # P1: 手动指定组合（最多2个）
    if manual_pairs:
        for pair in manual_pairs[:2]:
            normalized = tuple(sorted(pair))
            if normalized not in used_pairs and len(candidates) < max_candidates:
                candidates.append(pair)
                used_pairs.add(normalized)

    # P2: 自动补充（单维度熵减前三的两两组合，最多1个）
    if len(candidates) < max_candidates:
        # 按熵减排序，取前三
        sorted_dims = sorted(
            single_dimension_results,
            key=lambda x: x.get("entropy_reduction_normalized", 0),
            reverse=True,
        )[:3]

        dim_names = [d["dimension"] for d in sorted_dims if d.get("is_key_dimension")]

        # 两两组合
        for i in range(len(dim_names)):
            for j in range(i + 1, len(dim_names)):
                pair = (dim_names[i], dim_names[j])
                normalized = tuple(sorted(pair))
                if normalized not in used_pairs and len(candidates) < max_candidates:
                    candidates.append(pair)
                    used_pairs.add(normalized)
                    break
            if len(candidates) >= max_candidates:
                break

    return candidates[:max_candidates]


async def check_cross_dimensions(
    dimension_pool: list[dict[str, Any]],
    raw_data: dict[str, Any],
    single_dimension_results: list[dict[str, Any]],
    entropy_threshold: float = 0.2,
    timeout_seconds: float = 3.0,
    historical_pairs: list[tuple[str, str]] | None = None,
    manual_pairs: list[tuple[str, str]] | None = None,
) -> dict[str, Any]:
    """执行交叉维度校验（带超时降级）.

    Args:
        dimension_pool: 维度池配置
        raw_data: 原始数据
        single_dimension_results: 单维度熵减结果
        entropy_threshold: 熵减阈值
        timeout_seconds: 超时时间，默认3秒
        historical_pairs: 历史高频组合
        manual_pairs: 手动指定组合

    Returns:
        包含交叉维度结果的字典
        - completed: 是否完成所有计算
        - results: 完成的交叉维度结果列表
        - pending: 未完成（超时）的组合
        - recommendations: 插入建议
    """
    # 生成候选组合
    candidates = generate_cross_dimension_candidates(
        single_dimension_results,
        historical_pairs,
        manual_pairs,
    )

    if not candidates:
        return {
            "completed": True,
            "results": [],
            "pending": [],
            "recommendations": [],
        }

    # 准备交叉维度数据并执行计算
    async def compute_cross_dimension(pair: tuple[str, str]) -> Optional[dict[str, Any]]:
        dim_a_name, dim_b_name = pair

        # 从 dimension_pool 找到对应维度
        dim_a_config = None
        dim_b_config = None
        for dim in dimension_pool:
            if dim.get("dimension_name") == dim_a_name:
                dim_a_config = dim
            if dim.get("dimension_name") == dim_b_name:
                dim_b_config = dim

        if not dim_a_config or not dim_b_config:
            return None

        # 构建交叉维度贡献数据
        # 格式: {a_value: {b_value: contribution}}
        contributions = {}
        for a_child in dim_a_config.get("child_nodes", []):
            contributions[a_child] = {}
            for b_child in dim_b_config.get("child_nodes", []):
                # 从 raw_data 中查找交叉贡献
                cross_key = f"{a_child}×{b_child}"
                contribution = raw_data.get(cross_key, 0)
                contributions[a_child][b_child] = contribution

        return await calculate_cross_dimension_entropy_reduction(
            dim_a_name, dim_b_name, contributions, entropy_threshold
        )

    # 并发执行所有交叉维度计算
    tasks = [compute_cross_dimension(pair) for pair in candidates]

    try:
        # 等待所有任务，但设置超时
        results = await asyncio.wait_for(
            asyncio.gather(*tasks, return_exceptions=True),
            timeout=timeout_seconds,
        )

        # 过滤掉异常和None结果
        valid_results = []
        for r in results:
            if isinstance(r, dict) and "cross_dimension_name" in r:
                valid_results.append(r)

        return {
            "completed": True,
            "results": valid_results,
            "pending": [],
            "recommendations": _generate_recommendations(valid_results, entropy_threshold),
        }

    except asyncio.TimeoutError:
        # 超时降级：返回已完成的部分结果
        completed_results = []
        pending_pairs = []

        for i, task in enumerate(tasks):
            if task.done() and not task.exception():
                result = task.result()
                if result and isinstance(result, dict):
                    completed_results.append(result)
            else:
                pending_pairs.append(candidates[i])

        return {
            "completed": False,
            "results": completed_results,
            "pending": pending_pairs,
            "recommendations": _generate_recommendations(completed_results, entropy_threshold),
        }


def _generate_recommendations(
    cross_results: list[dict[str, Any]],
    entropy_threshold: float,
) -> list[dict[str, Any]]:
    """生成交叉维度插入建议.

    当交叉维度熵减超过单维度最大熵减的20%阈值时，
    建议将交叉节点作为附加节点加入归因链。

    Args:
        cross_results: 交叉维度结果列表
        entropy_threshold: 熵减阈值

    Returns:
        插入建议列表
    """
    recommendations = []

    for result in cross_results:
        if not result.get("is_key_cross_dimension"):
            continue

        er_norm = result.get("entropy_reduction_normalized", 0)

        # 建议插入操作
        recommendation = {
            "cross_dimension": result["cross_dimension_name"],
            "entropy_reduction_normalized": er_norm,
            "top_combination": result["top_combination"],
            "top_combination_share": result["top_combination_share"],
            "action": "insert_as_child",
            "target_node": result.get("top_a_value", ""),
            "child_node": result["top_combination"],
            "reason": f"交叉维度熵减为{er_norm:.1%}，超过阈值，建议加入归因链",
        }
        recommendations.append(recommendation)

    return recommendations


def check_cross_dimension_threshold(
    cross_er_normalized: float,
    single_max_er_normalized: float,
    threshold_ratio: float = 0.2,
) -> bool:
    """检查交叉维度是否触发插入条件.

    当交叉维度熵减超过单维度最大熵减的指定比例时，触发插入。

    Args:
        cross_er_normalized: 交叉维度归一化熵减
        single_max_er_normalized: 单维度最大归一化熵减
        threshold_ratio: 阈值比例，默认20%

    Returns:
        是否触发插入
    """
    if single_max_er_normalized <= 0:
        return cross_er_normalized > 0.2  # 单维度无关键维度时，交叉维度需独立判断

    return cross_er_normalized >= single_max_er_normalized * threshold_ratio

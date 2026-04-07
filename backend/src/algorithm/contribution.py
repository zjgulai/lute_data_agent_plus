"""贡献度计算模块.

支持加和型、乘积型、伪权重型指标的贡献度计算。
"""

from __future__ import annotations

from typing import Optional, Literal


def calculate_additive_contribution(
    child_changes: dict[str, float],
    weights: Optional[dict[str, float]] = None,
) -> dict[str, float]:
    """计算加和型指标的贡献度.

    公式: Contrib(C_i) = w_i · ΔC_i

    Args:
        child_changes: 各子类别的变化值，如 {"新客UV": -50000, "老客UV": -120000}
        weights: 各子类别的权重，默认为 1.0

    Returns:
        各子类别对父指标的贡献度

    Example:
        >>> changes = {"新客UV": -5, "老客UV": -12}
        >>> calculate_additive_contribution(changes)
        {"新客UV": -5, "老客UV": -12}
    """
    contributions = {}
    for child_id, change in child_changes.items():
        weight = weights.get(child_id, 1.0) if weights else 1.0
        contributions[child_id] = weight * change
    return contributions


def calculate_multiplicative_contribution(
    base_values: dict[str, float],
    current_values: dict[str, float],
    parent_base: float,
    include_interaction: bool = False,
) -> dict[str, float | dict[str, float]]:
    """计算乘积型指标的贡献度.

    单一维度贡献度（偏微分法）:
        Contrib(C_i) = P_0 · (ΔC_i / C_i0)

    组合维度贡献度（精确展开法）:
        Contrib(C_i, C_j) = P_0 · (ΔC_i / C_i0) · (ΔC_j / C_j0)

    Args:
        base_values: 基期值，如 {"UV": 1000000, "CR": 0.05, "AOV": 200}
        current_values: 当期值，如 {"UV": 800000, "CR": 0.045, "AOV": 222}
        parent_base: 父指标基期值（如 GMV 基期）
        include_interaction: 是否计算组合维度贡献度

    Returns:
        各维度的贡献度，可选包含交互项

    Example:
        >>> base = {"UV": 1000000, "CR": 0.05, "AOV": 200}
        >>> current = {"UV": 800000, "CR": 0.045, "AOV": 222}
        >>> result = calculate_multiplicative_contribution(base, current, 10000000)
        >>> result["UV"]
        -2000000.0  # UV 下滑贡献 -200万
    """
    # 计算变化率
    change_rates = {}
    for key in base_values:
        if base_values[key] != 0:
            change_rates[key] = (current_values[key] - base_values[key]) / base_values[key]
        else:
            change_rates[key] = 0

    # 单一维度贡献度
    single_contributions = {}
    for key, rate in change_rates.items():
        single_contributions[key] = parent_base * rate

    if not include_interaction:
        return single_contributions

    # 组合维度贡献度（两两组合）
    interaction_contributions = {}
    keys = list(base_values.keys())
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            key_i, key_j = keys[i], keys[j]
            # P_0 * (ΔC_i/C_i0) * (ΔC_j/C_j0)
            interaction = parent_base * change_rates[key_i] * change_rates[key_j]
            interaction_contributions[f"{key_i}×{key_j}"] = interaction

    # 三维度交互（如果超过 2 个维度）
    if len(keys) >= 3:
        triple_interaction = parent_base
        for key in keys:
            triple_interaction *= change_rates[key]
        interaction_contributions["×".join(keys)] = triple_interaction

    return {
        "single": single_contributions,
        "interaction": interaction_contributions,
    }


def calculate_pseudo_weight_contribution(
    indicator_change: float,
    pseudo_weight: float,
    parent_base: float,
) -> float:
    """计算伪权重型指标的贡献度.

    公式: Contrib = α · ΔC · P_0

    适用于没有精确数学公式的动作指标，如"会员日活动参与率"。

    Args:
        indicator_change: 指标变化值（如参与率变化 -0.05）
        pseudo_weight: 伪权重（如 0.35，表示每变化 1% 对父指标的影响）
        parent_base: 父指标基期值

    Returns:
        该指标对父指标的贡献度

    Example:
        >>> calculate_pseudo_weight_contribution(-0.05, 0.35, 10000000)
        -175000.0  # 贡献 -17.5万
    """
    return pseudo_weight * indicator_change * parent_base


def calculate_hierarchical_contribution(
    contribution_to_parent: float,
    parent_contribution_to_gmv: float,
) -> float:
    """计算指标对总 GMV 的层级传递贡献度.

    公式:
        Contrib(C_i → GMV) = Contrib(C_i → parent) × PathWeight(parent → GMV)

    Args:
        contribution_to_parent: 对直接父节点的贡献度
        parent_contribution_to_gmv: 父节点对 GMV 的贡献度（层级权重连乘）

    Returns:
        对总 GMV 的贡献度
    """
    return contribution_to_parent * parent_contribution_to_gmv


def format_contribution_report(
    contributions: dict[str, float],
    total_gmv: float,
    unit: str = "元",
) -> list[dict[str, str]]:
    """格式化贡献度报告.

    Args:
        contributions: 各指标贡献度
        total_gmv: GMV 总值
        unit: 金额单位

    Returns:
        格式化后的报告数据
    """
    report = []
    for indicator, contribution in contributions.items():
        percentage = (contribution / total_gmv * 100) if total_gmv != 0 else 0
        report.append({
            "indicator": indicator,
            "contribution": contribution,
            "contribution_formatted": f"{contribution:,.0f}{unit}",
            "percentage": percentage,
            "percentage_formatted": f"{percentage:+.1f}%",
            "direction": "up" if contribution > 0 else "down" if contribution < 0 else "neutral",
        })

    # 按绝对贡献度降序排列
    report.sort(key=lambda x: abs(x["contribution"]), reverse=True)
    return report

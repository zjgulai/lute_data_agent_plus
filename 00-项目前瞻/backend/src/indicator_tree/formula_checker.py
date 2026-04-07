"""公式循环依赖检测."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .models import TreeNode


def extract_formula_variables(formula: str) -> set[str]:
    """从数学公式中提取变量名（标识符）.

    支持字母、数字、下划线，但排除纯数字。
    例如：
        "uv * conversion_rate * avg_order_value" -> {"uv", "conversion_rate", "avg_order_value"}
        "new_user_uv + old_user_uv" -> {"new_user_uv", "old_user_uv"}
    """
    # 匹配标识符（字母或下划线开头，后跟字母数字下划线）
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", formula)
    # 排除数学函数名（简单排除列表）
    math_funcs = {"log", "ln", "exp", "sqrt", "abs", "max", "min", "sum", "prod"}
    return set(tokens) - math_funcs


def build_dependency_graph(nodes: dict[str, TreeNode]) -> dict[str, set[str]]:
    """构建节点间的公式依赖图.

    如果节点 A 的 formula 中引用了节点 B 的 id，则建立边 A -> B。
    """
    graph: dict[str, set[str]] = {node_id: set() for node_id in nodes}

    for node_id, node in nodes.items():
        if node.formula:
            vars_in_formula = extract_formula_variables(node.formula)
            for var in vars_in_formula:
                if var in nodes and var != node_id:
                    graph[node_id].add(var)

    return graph


def detect_cycles(graph: dict[str, set[str]]) -> list[list[str]]:
    """使用 DFS 检测有向图中的所有环.

    返回每个环的节点列表。
    """
    cycles: list[list[str]] = []
    visited: set[str] = set()
    rec_stack: list[str] = []
    rec_set: set[str] = set()

    def _dfs(node: str) -> None:
        visited.add(node)
        rec_stack.append(node)
        rec_set.add(node)

        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                _dfs(neighbor)
            elif neighbor in rec_set:
                # 发现一个环
                cycle_start = rec_stack.index(neighbor)
                cycle = rec_stack[cycle_start:] + [neighbor]
                cycles.append(cycle)

        rec_stack.pop()
        rec_set.remove(node)

    for node in graph:
        if node not in visited:
            _dfs(node)

    return cycles


def check_formula_cycles(nodes: dict[str, TreeNode]) -> list[str]:
    """检查指标树中是否存在公式循环依赖.

    返回错误信息列表。空列表表示无循环依赖。
    """
    graph = build_dependency_graph(nodes)
    cycles = detect_cycles(graph)

    errors: list[str] = []
    seen: set[frozenset[str]] = set()

    for cycle in cycles:
        cycle_set = frozenset(cycle)
        if cycle_set not in seen:
            seen.add(cycle_set)
            cycle_str = " -> ".join(cycle)
            errors.append(f"发现公式循环依赖: {cycle_str}")

    return errors

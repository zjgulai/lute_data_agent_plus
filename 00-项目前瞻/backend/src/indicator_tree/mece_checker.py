"""MECE 校验器."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .formula_checker import extract_formula_variables

if TYPE_CHECKING:
    from .models import TreeNode


def check_mece(root: TreeNode) -> list[str]:
    """检查指标树的 MECE 原则.

    返回错误信息列表。空列表表示通过 MECE 校验。
    """
    errors: list[str] = []

    def _traverse(node: TreeNode) -> None:
        child_ids = [child.id for child in node.children]
        child_names = [child.name for child in node.children]

        # 1. 子节点 id 唯一性
        if len(child_ids) != len(set(child_ids)):
            dup = {x for x in child_ids if child_ids.count(x) > 1}
            errors.append(f"节点 '{node.id}' 的子节点中存在重复的 id: {dup}")

        # 2. 子节点 name 唯一性（同一层级下名称不应重复）
        if len(child_names) != len(set(child_names)):
            dup = {x for x in child_names if child_names.count(x) > 1}
            errors.append(f"节点 '{node.id}' 的子节点中存在重复的名称: {dup}")

        # 3. 组织侧节点不应配置 dimension_pool
        if node.type == "organization" and node.dimension_pool:
            errors.append(f"组织侧节点(organization) '{node.id}' 不应配置 dimension_pool")

        # 4. dimension_pool 中的 child_nodes 必须指向指标树中存在的节点 id
        # 注意：它们不一定是当前节点的直接 children，可以是树中任意合法节点
        # 全局存在性检查由 validator.py 在完整树遍历后补充

        # 5. formula 中的变量应该是直接 children 的 id 之一（公式递进原则）
        if node.formula and node.children:
            vars_in_formula = extract_formula_variables(node.formula)
            # 允许公式中引用直接子节点的 id
            invalid_vars = vars_in_formula - set(child_ids)
            # 但也可能引用一些非节点的系统变量或常量，这里只做宽松检查：
            # 如果 formula 中的变量恰好是指标树中其他节点的 id，但不是当前节点的直接 children，则报错
            # 这个检查会在 validator 的完整树遍历中补充

        # 5. formula 中的变量应该是直接 children 的 id 之一（公式递进原则）
        if node.formula and node.children:
            vars_in_formula = extract_formula_variables(node.formula)
            # 允许公式中引用直接子节点的 id
            invalid_vars = vars_in_formula - set(child_ids)
            # 但也可能引用一些非节点的系统变量或常量，这里只做宽松检查：
            # 如果 formula 中的变量恰好是指标树中其他节点的 id，但不是当前节点的直接 children，则报错
            # 这个检查会在 validator 的完整树遍历中补充

        for child in node.children:
            _traverse(child)

    _traverse(root)
    return errors


def check_formula_scope(node: TreeNode, all_tree_node_ids: set[str]) -> list[str]:
    """检查节点的 formula 是否遵循'公式递进'原则.

    即：formula 中如果引用了指标树中的节点 id，那么这个 id 应该是当前节点的直接 children 之一。
    这是一个逐节点的检查，需要配合完整树的节点 id 集合使用。
    """
    errors: list[str] = []
    if not node.formula:
        return errors

    vars_in_formula = extract_formula_variables(node.formula)
    child_ids = {child.id for child in node.children}

    for var in vars_in_formula:
        if var in all_tree_node_ids and var not in child_ids:
            errors.append(
                f"节点 '{node.id}' 的 formula 引用了节点 '{var}'，"
                f"但 '{var}' 不是其直接子节点，违反公式递进原则"
            )

    return errors

"""指标树配置主校验器."""

from __future__ import annotations

from .formula_checker import check_formula_cycles
from .mece_checker import check_formula_scope, check_mece
from .models import IndicatorTree, TreeNode
from .parser import IndicatorTreeParser


class IndicatorTreeValidator:
    """指标树配置校验器.

    提供三个层级的校验：
    1. Schema 校验（Pydantic 模型自动完成）
    2. MECE 校验（互斥性、穷尽性、公式递进）
    3. 公式循环依赖检测
    """

    @staticmethod
    def validate(tree: IndicatorTree) -> list[str]:
        """执行完整校验，返回所有错误信息列表.

        空列表表示校验完全通过。
        """
        errors: list[str] = []

        # 1. 基础 Schema 校验已由 Pydantic 在 parse 阶段完成
        # 如果代码能执行到这里，说明模型结构是合法的

        # 2. 将树打平，获取所有节点字典
        nodes = IndicatorTreeParser.flatten_nodes(tree.root)
        all_node_ids = set(nodes.keys())

        # 3. MECE 校验（树结构层面）
        errors.extend(check_mece(tree.root))

        # 4. 公式递进校验（每个节点的 formula 只能引用直接 children）
        def _check_formula_scope_recursive(node: TreeNode) -> None:
            errors.extend(check_formula_scope(node, all_node_ids))
            for child in node.children:
                _check_formula_scope_recursive(child)

        _check_formula_scope_recursive(tree.root)

        # 5. dimension_pool 全局存在性校验
        def _check_dimension_pool_global(node: TreeNode) -> None:
            if node.dimension_pool:
                for dim in node.dimension_pool:
                    for child_node_id in dim.child_nodes:
                        if child_node_id not in all_node_ids:
                            errors.append(
                                f"节点 '{node.id}' 的 dimension_pool "
                                f"'{dim.dimension_id}' 中的 child_nodes "
                                f"'{child_node_id}' 不在指标树中"
                            )
            for child in node.children:
                _check_dimension_pool_global(child)

        _check_dimension_pool_global(tree.root)

        # 6. 公式循环依赖检测
        errors.extend(check_formula_cycles(nodes))

        # 6. ID 唯一性校验（flatten 过程中如果发现有重复 id，理论上不可能因为 dict 会覆盖，
        #    但我们可以显式检查树中是否有重复 id 的节点）
        def _collect_ids(node: TreeNode) -> list[str]:
            ids = [node.id]
            for child in node.children:
                ids.extend(_collect_ids(child))
            return ids

        all_ids = _collect_ids(tree.root)
        if len(all_ids) != len(set(all_ids)):
            from collections import Counter

            dup = {k: v for k, v in Counter(all_ids).items() if v > 1}
            errors.append(f"指标树中存在重复的节点 id: {dup}")

        # 7. 根节点特殊校验
        if tree.root.id != "gmv":
            errors.append(f"根节点 id 必须是 'gmv'，当前为 '{tree.root.id}'")

        return errors

    @staticmethod
    def validate_file(path: str) -> list[str]:
        """从文件加载并校验."""
        try:
            tree = IndicatorTreeParser.parse_file(path)
        except Exception as e:
            return [f"文件解析失败: {e}"]
        return IndicatorTreeValidator.validate(tree)

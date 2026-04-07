"""YAML 解析器：将指标树配置文件解析为 Pydantic 模型."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import yaml

from .models import IndicatorTree, TreeNode


class IndicatorTreeParser:
    """指标树配置文件解析器."""

    @staticmethod
    def parse_file(path: str | Path) -> IndicatorTree:
        """从 YAML 文件解析指标树."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"指标树配置文件不存在: {path}")

        with path.open("r", encoding="utf-8") as f:
            raw_data = yaml.safe_load(f)

        return IndicatorTree.model_validate(raw_data)

    @staticmethod
    def parse_string(content: str) -> IndicatorTree:
        """从 YAML 字符串解析指标树."""
        raw_data = yaml.safe_load(content)
        return IndicatorTree.model_validate(raw_data)

    @staticmethod
    def flatten_nodes(root: TreeNode) -> dict[str, TreeNode]:
        """将指标树打平为以 id 为键的字典，并自动补全 parent_id."""
        result: dict[str, TreeNode] = {}

        def _traverse(node: TreeNode, parent_id: Optional[str] = None) -> None:
            if parent_id is not None:
                node.parent_id = parent_id
            result[node.id] = node
            for child in node.children:
                _traverse(child, node.id)

        _traverse(root)
        return result

    @staticmethod
    def collect_dimension_pool_nodes(root: TreeNode) -> dict[str, list[Dimension]]:
        """收集所有配置了 dimension_pool 的节点."""
        from .models import Dimension

        result: dict[str, list[Dimension]] = {}

        def _traverse(node: TreeNode) -> None:
            if node.dimension_pool:
                result[node.id] = node.dimension_pool
            for child in node.children:
                _traverse(child)

        _traverse(root)
        return result

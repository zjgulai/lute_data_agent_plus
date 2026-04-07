"""指标树可视化：生成 Mermaid.js 图语法."""

from __future__ import annotations

from .models import TreeNode


class IndicatorTreeVisualizer:
    """指标树 Mermaid 图生成器."""

    @staticmethod
    def to_mermaid(root: TreeNode) -> str:
        """将指标树转换为 Mermaid 流程图语法.

        使用 graph TD（Top Down）布局，组织侧和经营侧用不同颜色区分。
        """
        lines: list[str] = ["graph TD"]
        styles: list[str] = []

        def _get_node_label(node: TreeNode) -> str:
            label = node.name
            if node.level_code:
                label = f"{node.level_code}: {label}"
            if node.formula:
                label += f"<br/>[{node.formula}]"
            elif node.pseudo_weight is not None:
                label += f"<br/>[pw={node.pseudo_weight}]"
            return label

        def _get_node_style_class(node_type: str) -> str:
            if node_type == "organization":
                return "orgNode"
            if node_type == "operation":
                return "opNode"
            return "actionNode"

        def _traverse(node: TreeNode) -> None:
            safe_id = node.id.replace("-", "_").replace(".", "_")

            # 定义节点样式类引用
            class_name = _get_node_style_class(node.type)
            label = _get_node_label(node)
            lines.append(f'    {safe_id}["{label}"]:::{class_name}')

            for child in node.children:
                child_safe_id = child.id.replace("-", "_").replace(".", "_")
                lines.append(f"    {safe_id} --> {child_safe_id}")
                _traverse(child)

        _traverse(root)

        # 添加样式定义
        lines.append("")
        lines.append("    classDef orgNode fill:#3B82F6,stroke:#1E40AF,stroke-width:2px,color:#fff")
        lines.append("    classDef opNode fill:#10B981,stroke:#047857,stroke-width:2px,color:#fff")
        lines.append("    classDef actionNode fill:#F59E0B,stroke:#B45309,stroke-width:2px,color:#fff")

        return "\n".join(lines)

    @staticmethod
    def to_markdown_with_mermaid(root: TreeNode, title: str = "指标树预览") -> str:
        """生成包含 Mermaid 图的 Markdown 文档."""
        mermaid = IndicatorTreeVisualizer.to_mermaid(root)
        return f"""# {title}

```mermaid
{mermaid}
```
"""

"""指标树可视化测试."""

from pathlib import Path

from indicator_tree import IndicatorTreeParser, IndicatorTreeVisualizer


CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicator_tree.yaml"


def test_to_mermaid_contains_key_elements() -> None:
    tree = IndicatorTreeParser.parse_file(CONFIG_PATH)
    mermaid = IndicatorTreeVisualizer.to_mermaid(tree.root)

    assert "graph TD" in mermaid
    assert "gmv" in mermaid
    assert "org_side" in mermaid
    assert "op_side" in mermaid
    assert "classDef orgNode" in mermaid
    assert "classDef opNode" in mermaid
    assert "classDef actionNode" in mermaid


def test_to_markdown_with_mermaid() -> None:
    tree = IndicatorTreeParser.parse_file(CONFIG_PATH)
    md = IndicatorTreeVisualizer.to_markdown_with_mermaid(tree.root, title="测试预览")

    assert "# 测试预览" in md
    assert "```mermaid" in md
    assert "graph TD" in md

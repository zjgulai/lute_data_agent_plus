"""pytest 配置文件."""

from pathlib import Path

import pytest

from indicator_tree import IndicatorTreeParser


@pytest.fixture
def sample_tree_path() -> Path:
    """返回示例指标树配置文件路径."""
    return Path(__file__).parent.parent / "config" / "indicator_tree.yaml"


@pytest.fixture
def sample_tree(sample_tree_path: Path):
    """返回解析后的示例指标树."""
    return IndicatorTreeParser.parse_file(sample_tree_path)


@pytest.fixture
def minimal_tree_yaml() -> str:
    """返回最小化的有效指标树 YAML."""
    return """
version: "1.0.0"
root:
  id: gmv
  name: GMV
  type: operation
  level: 0
  level_code: L0
  entropy_threshold: 0.2
  children: []
"""

"""指标树解析器边界情况测试."""

from pathlib import Path

import pytest
import yaml

from indicator_tree import IndicatorTreeParser


class TestParserEdgeCases:
    """解析器边界情况测试."""

    def test_parse_nonexistent_file(self) -> None:
        """测试解析不存在的文件."""
        with pytest.raises(FileNotFoundError) as exc_info:
            IndicatorTreeParser.parse_file("/nonexistent/path/config.yaml")
        assert "指标树配置文件不存在" in str(exc_info.value)

    def test_parse_empty_yaml(self) -> None:
        """测试解析空的 YAML 内容."""
        empty_yaml = ""
        with pytest.raises(Exception):
            IndicatorTreeParser.parse_string(empty_yaml)

    def test_parse_invalid_yaml_syntax(self) -> None:
        """测试解析语法错误的 YAML."""
        invalid_yaml = """
        version: "1.0.0"
        root:
          id: gmv
          name: GMV
          type: operation
          level: 0
          children: [invalid syntax here
        """
        with pytest.raises(yaml.YAMLError):
            IndicatorTreeParser.parse_string(invalid_yaml)

    def test_parse_missing_required_fields(self) -> None:
        """测试解析缺少必填字段的 YAML."""
        incomplete_yaml = """
        version: "1.0.0"
        root:
          id: gmv
          # 缺少 name 和 type 字段
          level: 0
          children: []
        """
        with pytest.raises(Exception):
            IndicatorTreeParser.parse_string(incomplete_yaml)

    def test_flatten_empty_tree(self) -> None:
        """测试打平只有根节点的树."""
        yaml_content = """
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
        tree = IndicatorTreeParser.parse_string(yaml_content)
        nodes = IndicatorTreeParser.flatten_nodes(tree.root)

        assert len(nodes) == 1
        assert "gmv" in nodes
        assert nodes["gmv"].parent_id is None

    def test_collect_dimension_pool_empty(self) -> None:
        """测试收集没有 dimension_pool 的树."""
        yaml_content = """
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
        tree = IndicatorTreeParser.parse_string(yaml_content)
        pools = IndicatorTreeParser.collect_dimension_pool_nodes(tree.root)

        assert len(pools) == 0

    def test_parse_string_valid(self) -> None:
        """测试从字符串解析有效的 YAML."""
        yaml_content = """
version: "1.0.0"
root:
  id: gmv
  name: GMV
  type: operation
  level: 0
  level_code: L0
  entropy_threshold: 0.2
  children:
    - id: test_child
      name: 测试子节点
      type: action
      level: 1
      level_code: L1
      pseudo_weight: 0.5
"""
        tree = IndicatorTreeParser.parse_string(yaml_content)
        assert tree.version == "1.0.0"
        assert tree.root.id == "gmv"
        assert len(tree.root.children) == 1
        assert tree.root.children[0].id == "test_child"

    def test_deep_nesting_flatten(self) -> None:
        """测试深层嵌套树的打平."""
        yaml_content = """
version: "1.0.0"
root:
  id: level0
  name: 层级0
  type: operation
  level: 0
  entropy_threshold: 0.2
  children:
    - id: level1
      name: 层级1
      type: operation
      level: 1
      entropy_threshold: 0.2
      children:
        - id: level2
          name: 层级2
          type: operation
          level: 2
          entropy_threshold: 0.2
          children:
            - id: level3
              name: 层级3
              type: action
              level: 3
              pseudo_weight: 0.5
"""
        tree = IndicatorTreeParser.parse_string(yaml_content)
        nodes = IndicatorTreeParser.flatten_nodes(tree.root)

        assert len(nodes) == 4
        assert nodes["level0"].parent_id is None
        assert nodes["level1"].parent_id == "level0"
        assert nodes["level2"].parent_id == "level1"
        assert nodes["level3"].parent_id == "level2"


class TestParserWithSpecialCharacters:
    """测试特殊字符处理."""

    def test_node_id_with_special_chars(self) -> None:
        """测试包含特殊字符的节点 ID."""
        yaml_content = """
version: "1.0.0"
root:
  id: gmv-test_node.v1
  name: GMV
  type: operation
  level: 0
  entropy_threshold: 0.2
  children: []
"""
        tree = IndicatorTreeParser.parse_string(yaml_content)
        assert tree.root.id == "gmv-test_node.v1"

    def test_unicode_names(self) -> None:
        """测试 Unicode 字符的名称."""
        yaml_content = """
version: "1.0.0"
root:
  id: gmv
  name: GMV交易额（元）
  type: operation
  level: 0
  entropy_threshold: 0.2
  children: []
"""
        tree = IndicatorTreeParser.parse_string(yaml_content)
        assert tree.root.name == "GMV交易额（元）"

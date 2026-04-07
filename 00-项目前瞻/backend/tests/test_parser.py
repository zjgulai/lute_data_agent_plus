"""指标树解析器测试."""

from pathlib import Path

import pytest

from indicator_tree import IndicatorTreeParser


CONFIG_PATH = Path(__file__).parent.parent / "config" / "indicator_tree.yaml"


def test_parse_file_success() -> None:
    tree = IndicatorTreeParser.parse_file(CONFIG_PATH)
    assert tree.version == "1.0.0"
    assert tree.root.id == "gmv"
    assert tree.root.name == "GMV"


def test_flatten_nodes() -> None:
    tree = IndicatorTreeParser.parse_file(CONFIG_PATH)
    nodes = IndicatorTreeParser.flatten_nodes(tree.root)

    assert "gmv" in nodes
    assert "org_side" in nodes
    assert "op_side" in nodes
    assert "act_member_day_participation" in nodes
    assert "act_facebook_ads" in nodes

    # 检查 parent_id 是否正确补全
    assert nodes["org_side"].parent_id == "gmv"
    assert nodes["org_sg_marketing"].parent_id == "org_sg"
    assert nodes["act_facebook_ads"].parent_id == "op_ad_traffic"


def test_dimension_pool_collection() -> None:
    tree = IndicatorTreeParser.parse_file(CONFIG_PATH)
    pools = IndicatorTreeParser.collect_dimension_pool_nodes(tree.root)

    assert "gmv" in pools
    assert "op_uv" in pools
    assert "op_old_user_uv" in pools

    # 检查 dimension_pool 内容
    gmv_pool = pools["gmv"]
    assert len(gmv_pool) == 2
    assert gmv_pool[0].dimension_id == "dim_region"
    assert gmv_pool[1].dimension_id == "dim_operation"

"""指标树校验器测试."""

from indicator_tree import IndicatorTreeParser, IndicatorTreeValidator
from indicator_tree.models import IndicatorTree, TreeNode


def test_validate_success() -> None:
    from pathlib import Path

    config_path = Path(__file__).parent.parent / "config" / "indicator_tree.yaml"
    tree = IndicatorTreeParser.parse_file(config_path)
    errors = IndicatorTreeValidator.validate(tree)

    # 如果示例配置有错误，打印出来方便调试
    if errors:
        for e in errors:
            print(f"VALIDATION ERROR: {e}")

    assert len(errors) == 0, f"预期校验通过，但发现错误: {errors}"


def test_validate_duplicate_id() -> None:
    """测试重复 id 检测."""
    root = TreeNode(
        id="gmv",
        name="GMV",
        type="operation",
        level=0,
        children=[
            TreeNode(id="child_a", name="A", type="operation", level=1),
            TreeNode(id="child_a", name="B", type="operation", level=1),  # 重复 id
        ],
    )
    tree = IndicatorTree(version="1.0.0", root=root)
    errors = IndicatorTreeValidator.validate(tree)
    assert any("重复" in e for e in errors)


def test_validate_organization_with_dimension_pool() -> None:
    """测试组织侧节点不应有 dimension_pool."""
    from indicator_tree.models import Dimension

    root = TreeNode(
        id="gmv",
        name="GMV",
        type="operation",
        level=0,
        children=[
            TreeNode(
                id="org_side",
                name="组织侧",
                type="organization",
                level=1,
                dimension_pool=[
                    Dimension(
                        dimension_name="区域",
                        dimension_id="dim_region",
                        child_nodes=[],
                    )
                ],
            ),
        ],
    )
    tree = IndicatorTree(version="1.0.0", root=root)
    errors = IndicatorTreeValidator.validate(tree)
    assert any("organization" in e.lower() and "dimension_pool" in e.lower() for e in errors)


def test_validate_formula_cycle() -> None:
    """测试公式循环依赖检测."""
    root = TreeNode(
        id="gmv",
        name="GMV",
        type="operation",
        level=0,
        formula="a + b",
        children=[
            TreeNode(
                id="a",
                name="A",
                type="operation",
                level=1,
                formula="gmv + c",  # 引用父节点，形成循环
            ),
            TreeNode(id="b", name="B", type="operation", level=1),
        ],
    )
    tree = IndicatorTree(version="1.0.0", root=root)
    errors = IndicatorTreeValidator.validate(tree)
    assert any("循环依赖" in e for e in errors)


def test_validate_formula_scope_violation() -> None:
    """测试公式递进原则：formula 只能引用直接 children."""
    root = TreeNode(
        id="gmv",
        name="GMV",
        type="operation",
        level=0,
        formula="a + b",
        children=[
            TreeNode(id="a", name="A", type="operation", level=1),
            TreeNode(
                id="b",
                name="B",
                type="operation",
                level=1,
                formula="c + d",  # c 和 d 不是 b 的直接 children
            ),
            TreeNode(id="c", name="C", type="operation", level=1),
            TreeNode(id="d", name="D", type="operation", level=1),
        ],
    )
    tree = IndicatorTree(version="1.0.0", root=root)
    errors = IndicatorTreeValidator.validate(tree)
    assert any("公式递进" in e for e in errors)

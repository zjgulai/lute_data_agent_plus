"""性能测试 - 大数据量下的算法引擎表现.

使用 pytest-benchmark 风格（无需额外依赖），测量不同数据规模下的：
1. 单维度熵减计算耗时
2. 交叉维度分析耗时
3. 贡献度计算耗时
"""

from __future__ import annotations

import random
import time
from typing import Any

import pytest

from algorithm.engine import get_algorithm_engine


def generate_raw_data(num_children: int, seed: int = 42) -> dict[str, float]:
    """生成指定数量的子节点变化数据."""
    random.seed(seed)
    return {f"child_{i}": random.uniform(-100000, 100000) for i in range(num_children)}


def generate_dimension_pool(num_dimensions: int, num_children_per_dim: int) -> list[dict[str, Any]]:
    """生成维度池配置."""
    pool = []
    for d in range(num_dimensions):
        pool.append({
            "dimension_name": f"维度_{d}",
            "dimension_id": f"dim_{d}",
            "child_nodes": [f"child_{i}" for i in range(num_children_per_dim)],
        })
    return pool


class TestAlgorithmPerformance:
    """算法性能基准测试."""

    @pytest.mark.parametrize("num_children", [10, 50, 100])
    def test_entropy_calculation_scaling(self, num_children: int):
        """测试单维度熵减在不同子节点数量下的耗时."""
        engine = get_algorithm_engine()
        raw_data = generate_raw_data(num_children)
        dimension_pool = [{
            "dimension_name": "测试维度",
            "dimension_id": "test_dim",
            "child_nodes": list(raw_data.keys()),
        }]

        start = time.perf_counter()
        import asyncio
        result = asyncio.run(engine.calculate_entropy_with_cross_dimension(
            node_id="gmv",
            dimension_pool=dimension_pool,
            raw_data=raw_data,
            entropy_threshold=0.2,
            cross_timeout=1.0,
        ))
        elapsed = time.perf_counter() - start

        # 重点验证耗时，不强制业务结果（随机数据可能未过阈值）
        assert "single_dimension_results" in result
        # 100 个子节点应在 1 秒内完成
        assert elapsed < 1.0, f"Entropy calc for {num_children} children took {elapsed:.3f}s"

    @pytest.mark.parametrize("num_dimensions", [3, 5, 10])
    def test_multi_dimension_entropy_scaling(self, num_dimensions: int):
        """测试多维度熵减计算耗时."""
        engine = get_algorithm_engine()
        raw_data = generate_raw_data(num_dimensions * 10)
        dimension_pool = generate_dimension_pool(num_dimensions, 10)

        start = time.perf_counter()
        import asyncio
        result = asyncio.run(engine.calculate_entropy_with_cross_dimension(
            node_id="gmv",
            dimension_pool=dimension_pool,
            raw_data=raw_data,
            entropy_threshold=0.2,
            cross_timeout=1.0,
        ))
        elapsed = time.perf_counter() - start

        assert len(result["single_dimension_results"]) == num_dimensions
        # 10 维度应在 2 秒内完成
        assert elapsed < 2.0, f"Multi-dim entropy for {num_dimensions} dims took {elapsed:.3f}s"

    def test_contribution_performance(self):
        """测试贡献度计算性能（大数据量）."""
        engine = get_algorithm_engine()
        num_items = 1000
        data = {
            "child_changes": {f"item_{i}": random.uniform(-1000, 1000) for i in range(num_items)},
        }

        start = time.perf_counter()
        contributions = engine.calculate_contributions("additive", data)
        elapsed = time.perf_counter() - start

        assert len(contributions) == num_items
        assert elapsed < 0.5, f"Contribution calc for {num_items} items took {elapsed:.3f}s"

    def test_cross_dimension_timeout(self):
        """测试交叉维度在超时限流下的表现."""
        engine = get_algorithm_engine()
        raw_data = generate_raw_data(20)
        dimension_pool = generate_dimension_pool(4, 5)

        start = time.perf_counter()
        import asyncio
        result = asyncio.run(engine.calculate_entropy_with_cross_dimension(
            node_id="gmv",
            dimension_pool=dimension_pool,
            raw_data=raw_data,
            entropy_threshold=0.2,
            cross_timeout=0.1,  # 100ms 超时
        ))
        elapsed = time.perf_counter() - start

        cross = result["cross_dimension"]
        # 即使超时，也应返回已计算部分和 pending 列表
        assert "completed" in cross
        assert "results" in cross
        assert "pending" in cross
        # 总耗时应在 1 秒内（含超时兜底）
        assert elapsed < 1.0, f"Cross-dimension with timeout took {elapsed:.3f}s"

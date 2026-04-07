"""FastAPI 算法服务接口.

提供熵减计算、贡献度计算、交叉维度校验的 RESTful API。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from algorithm.engine import AlgorithmEngine, get_algorithm_engine
from data_service.exceptions import DataMissingError

router = APIRouter(prefix="/api/v1/entropy", tags=["algorithm"])


# ============ 请求/响应模型 ============

class DimensionContribution(BaseModel):
    """维度贡献数据."""

    dimension_name: str = Field(..., description="维度名称")
    contributions: dict[str, float] = Field(..., description="各子类别的带符号贡献值")


class EntropyCalculateRequest(BaseModel):
    """熵减计算请求."""

    node_id: str = Field(..., description="当前节点ID")
    dimension_pool: list[dict[str, Any]] = Field(..., description="维度池配置")
    raw_data: dict[str, Any] = Field(..., description="原始数据")
    entropy_threshold: float = Field(0.2, description="熵减阈值")


class EntropyCalculateResponse(BaseModel):
    """熵减计算响应."""

    node_id: str
    entropy_threshold: float
    selected_dimension: Optional[str]
    selected_child: Optional[str]
    should_drill_down: bool
    single_dimension_results: list[dict[str, Any]]
    summary: str


class CrossDimensionRequest(BaseModel):
    """交叉维度校验请求."""

    node_id: str = Field(..., description="当前节点ID")
    dimension_pool: list[dict[str, Any]] = Field(..., description="维度池配置")
    raw_data: dict[str, Any] = Field(..., description="原始数据")
    single_results: list[dict[str, Any]] = Field(..., description="单维度熵减结果")
    entropy_threshold: float = Field(0.2, description="熵减阈值")
    timeout_seconds: float = Field(3.0, description="超时时间（秒）")
    historical_pairs: Optional[list[tuple[str, str]]] = Field(None, description="历史高频组合")
    manual_pairs: Optional[list[tuple[str, str]]] = Field(None, description="手动指定组合")


class CrossDimensionResponse(BaseModel):
    """交叉维度校验响应."""

    completed: bool
    results: list[dict[str, Any]]
    pending: list[tuple[str, str]]
    recommendations: list[dict[str, Any]]


class FullAttributionRequest(BaseModel):
    """完整归因分析请求."""

    node_id: str = Field(..., description="当前节点ID")
    dimension_pool: list[dict[str, Any]] = Field(..., description="维度池配置")
    raw_data: dict[str, Any] = Field(..., description="原始数据")
    entropy_threshold: float = Field(0.2, description="熵减阈值")
    cross_timeout: float = Field(3.0, description="交叉维度超时时间")
    historical_pairs: Optional[list[tuple[str, str]]] = Field(None, description="历史高频组合")
    manual_pairs: Optional[list[tuple[str, str]]] = Field(None, description="手动指定组合")


class FullAttributionResponse(BaseModel):
    """完整归因分析响应."""

    node_id: str
    entropy_threshold: float
    selected_dimension: Optional[str]
    selected_child: Optional[str]
    should_drill_down: bool
    single_dimension_results: list[dict[str, Any]]
    cross_dimension: dict[str, Any]
    summary: str


class ContributionRequest(BaseModel):
    """贡献度计算请求."""

    indicator_type: str = Field(..., description="指标类型: additive | multiplicative | pseudo_weight")
    data: dict[str, Any] = Field(..., description="计算数据")


class ContributionResponse(BaseModel):
    """贡献度计算响应."""

    indicator_type: str
    contributions: dict[str, Any]


# ============ API 端点 ============

@router.post("/calculate", response_model=EntropyCalculateResponse)
async def calculate_entropy(
    request: EntropyCalculateRequest,
) -> EntropyCalculateResponse:
    """计算单维度熵减并选择最佳切分维度.

    接收维度池和原始数据，返回各维度的熵减分析结果和最佳切分维度。
    """
    engine = get_algorithm_engine()

    try:
        # 构建候选维度
        candidate_dimensions = []
        for dim in request.dimension_pool:
            dim_name = dim.get("dimension_name", dim.get("dimension_id", ""))
            child_nodes = dim.get("child_nodes", [])

            contributions = {
                child_id: request.raw_data.get(child_id, 0)
                for child_id in child_nodes
            }

            if contributions:
                candidate_dimensions.append({
                    "dimension_name": dim_name,
                    "contributions": contributions,
                })

        # 计算熵减
        best_dim, all_results = engine.select_best_dimension(
            candidate_dimensions,
            request.entropy_threshold,
        )

        return EntropyCalculateResponse(
            node_id=request.node_id,
            entropy_threshold=request.entropy_threshold,
            selected_dimension=best_dim["dimension"] if best_dim else None,
            selected_child=best_dim["top_child"] if best_dim else None,
            should_drill_down=best_dim is not None and best_dim.get("is_key_dimension", False),
            single_dimension_results=all_results,
            summary=_generate_summary(best_dim),
        )

    except DataMissingError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/cross-dimension", response_model=CrossDimensionResponse)
async def check_cross_dimension(
    request: CrossDimensionRequest,
) -> CrossDimensionResponse:
    """执行交叉维度校验.

    对候选维度组合进行交叉熵减计算，返回交叉维度分析结果和插入建议。
    """
    engine = get_algorithm_engine()

    try:
        result = await engine.calculate_entropy_with_cross_dimension(
            node_id=request.node_id,
            dimension_pool=request.dimension_pool,
            raw_data=request.raw_data,
            entropy_threshold=request.entropy_threshold,
            cross_timeout=request.timeout_seconds,
            historical_pairs=request.historical_pairs,
            manual_pairs=request.manual_pairs,
        )

        return CrossDimensionResponse(
            completed=result["cross_dimension"]["completed"],
            results=result["cross_dimension"]["results"],
            pending=result["cross_dimension"]["pending"],
            recommendations=result["cross_dimension"]["recommendations"],
        )

    except DataMissingError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/analyze", response_model=FullAttributionResponse)
async def full_attribution_analysis(
    request: FullAttributionRequest,
) -> FullAttributionResponse:
    """执行完整归因分析（熵减 + 交叉维度）.

    这是最完整的归因分析接口，包含：
    1. 单维度熵减计算
    2. 最佳切分维度选择
    3. 交叉维度校验（异步，3秒超时）
    """
    engine = get_algorithm_engine()

    try:
        result = await engine.calculate_entropy_with_cross_dimension(
            node_id=request.node_id,
            dimension_pool=request.dimension_pool,
            raw_data=request.raw_data,
            entropy_threshold=request.entropy_threshold,
            cross_timeout=request.cross_timeout,
            historical_pairs=request.historical_pairs,
            manual_pairs=request.manual_pairs,
        )

        return FullAttributionResponse(
            node_id=result["node_id"],
            entropy_threshold=result["entropy_threshold"],
            selected_dimension=result["selected_dimension"],
            selected_child=result["selected_child"],
            should_drill_down=result["should_drill_down"],
            single_dimension_results=result["single_dimension_results"],
            cross_dimension=result["cross_dimension"],
            summary=result["summary"],
        )

    except DataMissingError as e:
        raise HTTPException(status_code=400, detail=e.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/contribution", response_model=ContributionResponse)
def calculate_contribution(
    request: ContributionRequest,
) -> ContributionResponse:
    """计算指标贡献度.

    支持加和型、乘积型、伪权重型三种指标类型。
    """
    engine = get_algorithm_engine()

    try:
        contributions = engine.calculate_contributions(
            request.indicator_type,
            request.data,
        )

        return ContributionResponse(
            indicator_type=request.indicator_type,
            contributions=contributions,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.get("/demo/prd-4-1")
def get_prd_4_1_demo() -> dict[str, Any]:
    """获取 PRD 4.1 节熵减计算示例数据.

    返回 PRD 中定义的示例数据和预期结果，用于验证算法正确性。
    """
    # PRD 4.1 节示例数据
    demo_data = {
        "scenario": "GMV下滑20%归因",
        "raw_data": {
            "美国": -1980000,
            "中国": 100000,
            "欧洲": -120000,
            "亚太": 0,
            "产品A": -1200000,
            "产品B": -800000,
            "产品C": 10000,
            "线上": 0,
            "线下": 0,
        },
        "dimension_pool": [
            {
                "dimension_name": "区域",
                "dimension_id": "region",
                "child_nodes": ["美国", "中国", "欧洲", "亚太"],
            },
            {
                "dimension_name": "产品",
                "dimension_id": "product",
                "child_nodes": ["产品A", "产品B", "产品C"],
            },
            {
                "dimension_name": "渠道",
                "dimension_id": "channel",
                "child_nodes": ["线上", "线下"],
            },
        ],
        "expected_results": {
            "区域": {
                "entropy_reduction_normalized": 0.74,
                "is_key_dimension": True,
                "top_child": "美国",
                "top_child_share": 0.99,
            },
            "产品": {
                "entropy_reduction_normalized": 0.445,
                "is_key_dimension": True,
                "top_child": "产品A",
            },
            "渠道": {
                "entropy_reduction_normalized": 0,
                "is_key_dimension": False,
            },
        },
    }

    return demo_data


# ============ 辅助函数 ============

def _generate_summary(best_dim: Optional[dict[str, Any]]) -> str:
    """生成简要摘要."""
    if not best_dim:
        return "未找到关键维度"

    return (
        f"维度『{best_dim['dimension']}』的熵减为"
        f"{best_dim['entropy_reduction_normalized']:.1%}，"
        f"建议优先从此维度下钻。"
    )

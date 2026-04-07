"""FastAPI 指标树预览接口."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from indicator_tree import IndicatorTreeParser, IndicatorTreeValidator, IndicatorTreeVisualizer

router = APIRouter(prefix="/api/v1/tree", tags=["indicator-tree"])

DEFAULT_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "indicator_tree.yaml"


class PreviewResponse(BaseModel):
    """预览接口响应模型."""

    valid: bool
    errors: list[str]
    mermaid: str


class ValidateResponse(BaseModel):
    """校验接口响应模型."""

    valid: bool
    errors: list[str]


@router.get("/preview", response_model=PreviewResponse)
def preview_tree(config_path: Optional[str] = None) -> PreviewResponse:
    """加载指标树配置文件，校验后返回 Mermaid 图语法."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH

    try:
        tree = IndicatorTreeParser.parse_file(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"配置文件解析失败: {e}")

    errors = IndicatorTreeValidator.validate(tree)
    mermaid = IndicatorTreeVisualizer.to_mermaid(tree.root)

    return PreviewResponse(valid=len(errors) == 0, errors=errors, mermaid=mermaid)


@router.get("/validate", response_model=ValidateResponse)
def validate_tree(config_path: Optional[str] = None) -> ValidateResponse:
    """仅校验指标树配置文件，返回校验结果."""
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    errors = IndicatorTreeValidator.validate_file(str(path))
    return ValidateResponse(valid=len(errors) == 0, errors=errors)

"""会话管理 API.

提供归因会话的创建、状态查询、推进等接口。
"""

from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from auth import require_permission
from auth.models import UserPermissions
from llm import LLMOrchestrator
from state_machine import AnalysisMode
from db.models import AttributionSession, AttributionConclusion, AttributionStep, get_db
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])

# 内存存储（运行时状态）
_orchestrators: dict[str, LLMOrchestrator] = {}


# ============ 请求/响应模型 ============

class CreateSessionRequest(BaseModel):
    """创建会话请求."""

    user_id: str = Field(..., description="用户ID")
    user_role: str = Field(..., description="用户角色: manager / business")
    mode: str = Field(..., description="分析模式: auto / manual")
    start_date: str = Field(..., description="分析开始日期: YYYY-MM-DD")
    end_date: str = Field(..., description="分析结束日期: YYYY-MM-DD")
    comparison_period: str = Field(default="prev_month", description="对比周期: prev_month / yoy")
    indicator_tree_config: dict[str, Any] = Field(default_factory=dict, description="指标树配置")


class CreateSessionResponse(BaseModel):
    """创建会话响应."""

    session_id: str
    state: str
    mode: str
    message: str


class SessionStatusResponse(BaseModel):
    """会话状态响应."""

    session_id: str
    state: str
    mode: Optional[str]
    step: Optional[int]
    can_export_process: bool
    can_export_full: bool
    is_terminal: bool


class ContinueRequest(BaseModel):
    """继续分析请求."""

    session_id: str


class SubmitConclusionRequest(BaseModel):
    """提交结论请求."""

    session_id: str
    reason_type: str = Field(..., description="原因类型")
    detailed_explanation: str = Field(..., description="详细说明")
    involved_departments: list[str] = Field(default_factory=list, description="涉及部门")
    suggested_actions: str = Field(default="", description="建议行动")
    confidence_level: str = Field(..., description="置信度: high / medium / low")


# ============ API 端点 ============

@router.post("/create", response_model=CreateSessionResponse)
async def create_session(
    request: CreateSessionRequest,
    db: Session = Depends(get_db),
) -> CreateSessionResponse:
    """创建新的归因分析会话."""
    import uuid
    import json

    session_id = f"att-{uuid.uuid4().hex[:8]}"

    # 创建 Orchestrator
    orchestrator = LLMOrchestrator(session_id=session_id)
    _orchestrators[session_id] = orchestrator

    # 启动分析
    mode = AnalysisMode.AUTO if request.mode == "auto" else AnalysisMode.MANUAL

    result = await orchestrator.start_analysis(
        mode=mode,
        indicator_tree_config=request.indicator_tree_config,
        data_source={"type": "excel", "path": "./testdata"},
        analysis_period={
            "start_date": request.start_date,
            "end_date": request.end_date,
            "comparison_period": request.comparison_period,
        },
    )

    # 持久化到数据库
    db_session = AttributionSession(
        session_id=session_id,
        user_id=request.user_id,
        user_role=request.user_role,
        analysis_mode=request.mode,
        indicator_tree_config=json.dumps(request.indicator_tree_config),
        start_date=request.start_date,
        end_date=request.end_date,
        comparison_period=request.comparison_period,
        current_state=result.get("state", "INIT"),
        status="running",
    )
    db.add(db_session)
    db.commit()

    return CreateSessionResponse(
        session_id=session_id,
        state=result.get("state", "UNKNOWN"),
        mode=request.mode,
        message=result.get("next_action", "分析已启动"),
    )


@router.get("/{session_id}/status", response_model=SessionStatusResponse)
def get_session_status(session_id: str) -> SessionStatusResponse:
    """获取会话当前状态."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    status = orchestrator.get_status()
    return SessionStatusResponse(
        session_id=status["session_id"],
        state=status["state"],
        mode=status["mode"],
        step=status["step"],
        can_export_process=status["can_export_process"],
        can_export_full=status["can_export_full"],
        is_terminal=status["is_terminal"],
    )


@router.post("/{session_id}/continue")
async def continue_session(session_id: str) -> dict[str, Any]:
    """继续手动模式的下一步（仅在手动模式下有效）."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    result = await orchestrator.continue_manual()
    return result


@router.post("/{session_id}/submit-conclusion")
async def submit_conclusion(
    session_id: str,
    request: SubmitConclusionRequest,
    _user: UserPermissions = Depends(require_permission("submit_conclusions")),
    db: Session = Depends(get_db),
) -> dict[str, Any]:
    """提交业务结论."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    conclusion = {
        "reason_type": request.reason_type,
        "detailed_explanation": request.detailed_explanation,
        "involved_departments": request.involved_departments,
        "suggested_actions": request.suggested_actions,
        "confidence_level": request.confidence_level,
    }

    result = await orchestrator.submit_conclusion(conclusion)

    # 持久化结论到数据库
    db_session = db.query(AttributionSession).filter(AttributionSession.session_id == session_id).first()
    if db_session:
        db_conclusion = AttributionConclusion(
            session_id=session_id,
            user_id=request.user_id,
            reason_type=request.reason_type,
            detailed_explanation=request.detailed_explanation,
            involved_departments=request.involved_departments,
            suggested_actions=request.suggested_actions,
            confidence_level=request.confidence_level,
        )
        db.add(db_conclusion)
        db_session.current_state = result.get("state", db_session.current_state)
        db_session.status = "completed"
        db.commit()

    return result


@router.get("/{session_id}/result")
def get_session_result(
    session_id: str,
    _user: UserPermissions = Depends(require_permission("export_reports")),
) -> dict[str, Any]:
    """获取会话完整结果（包括归因链和结论）."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    status = orchestrator.get_status()

    # 获取归因链
    attribution_chain = []
    for i in range(1, 5):
        result = orchestrator.state_machine.get_context(f"step_{i}_result")
        if result:
            attribution_chain.append(result)

    return {
        "session_id": session_id,
        "state": status["state"],
        "attribution_chain": attribution_chain,
        "conclusion": orchestrator.state_machine.get_context("human_conclusion"),
        "can_export": status["can_export_process"],
    }

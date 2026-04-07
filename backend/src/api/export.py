"""报告导出 API.

提供 Word 和 PDF 格式的报告下载。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import io

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from auth import require_permission
from auth.models import UserPermissions
from report.engine import ReportEngine, ReportFormat, ReportType

# 从 session API 导入内存存储的 orchestrators
from api.session import _orchestrators
from db.models import get_db, init_db, _SessionLocal
from db.repository import build_session_data_from_db

router = APIRouter(prefix="/api/v1/export", tags=["export"])

_report_engine = ReportEngine()


def _build_session_data_from_orchestrator(session_id: str) -> dict[str, Any]:
    """从内存 Orchestrator 构建报告所需的会话数据."""
    orchestrator = _orchestrators.get(session_id)
    if not orchestrator:
        raise HTTPException(status_code=404, detail="会话不存在")

    status = orchestrator.get_status()
    sm = orchestrator.state_machine

    # 提取步骤数据
    steps = []
    for i in range(1, 5):
        step_result = sm.get_context(f"step_{i}_result")
        if step_result:
            steps.append({
                "step_number": i,
                "node_id": step_result.get("node_id", "-"),
                "node_name": step_result.get("node_name", "-"),
                "node_type": step_result.get("node_type", "operation"),
                "selected_dimension": step_result.get("selected_dimension"),
                "selected_child": step_result.get("selected_child"),
                "entropy_results": step_result.get("entropy_results", []),
                "cross_dimension_results": step_result.get("cross_dimension_results", []),
                "contributions": step_result.get("contributions", {}),
            })

    # 提取结论
    conclusion = sm.get_context("human_conclusion")

    return {
        "session_id": session_id,
        "analysis_mode": status.get("mode") or "-",
        "current_state": status.get("state", "-"),
        "start_date": sm.get_context("start_date", "-"),
        "end_date": sm.get_context("end_date", "-"),
        "comparison_period": sm.get_context("comparison_period", "-"),
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "steps": steps,
        "conclusion": conclusion,
    }


def _build_session_data(session_id: str) -> dict[str, Any]:
    """构建报告所需的会话数据（优先内存，后备数据库）.

    Args:
        session_id: 会话ID

    Returns:
        格式化的会话数据字典
    """
    if session_id in _orchestrators:
        return _build_session_data_from_orchestrator(session_id)

    # 内存中没有，尝试从数据库恢复
    if _SessionLocal is not None:
        db = next(get_db())
        try:
            data = build_session_data_from_db(session_id, db)
            if data:
                return data
        finally:
            db.close()

    raise HTTPException(status_code=404, detail="会话不存在")


def _check_export_permission(status: dict[str, Any], report_type: ReportType) -> None:
    """检查当前状态是否允许导出指定类型报告."""
    can_process = status.get("can_export_process", False)
    can_full = status.get("can_export_full", False)

    if report_type == ReportType.PROCESS and not can_process:
        raise HTTPException(status_code=403, detail="当前状态不允许导出过程报告")

    if report_type == ReportType.FULL and not can_full:
        raise HTTPException(status_code=403, detail="当前状态不允许导出完整报告")


@router.get("/{session_id}/word")
async def export_word(
    session_id: str,
    report_type: ReportType = Query(ReportType.PROCESS, description="报告类型: process / full"),
    _user: UserPermissions = Depends(require_permission("export_reports")),
) -> StreamingResponse:
    """导出 Word 格式报告."""
    orchestrator = _orchestrators.get(session_id)
    if orchestrator:
        _check_export_permission(orchestrator.get_status(), report_type)
    else:
        # 数据库后备：检查会话是否存在即可导出
        session_data = _build_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")

    session_data = _build_session_data(session_id)
    content = await _report_engine.generate(
        session_data,
        report_type,
        ReportFormat.WORD,
    )

    filename = f"gmv_attribution_{session_id}_{report_type.value}.docx"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/{session_id}/pdf")
async def export_pdf(
    session_id: str,
    report_type: ReportType = Query(ReportType.PROCESS, description="报告类型: process / full"),
    _user: UserPermissions = Depends(require_permission("export_reports")),
) -> StreamingResponse:
    """导出 PDF 格式报告."""
    orchestrator = _orchestrators.get(session_id)
    if orchestrator:
        _check_export_permission(orchestrator.get_status(), report_type)
    else:
        session_data = _build_session_data(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="会话不存在")

    session_data = _build_session_data(session_id)
    content = await _report_engine.generate(
        session_data,
        report_type,
        ReportFormat.PDF,
    )

    filename = f"gmv_attribution_{session_id}_{report_type.value}.pdf"
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )

"""数据库仓库层：提供会话数据的持久化读取.

为报告导出等场景提供数据库后备，避免后端重启后丢失历史会话。
"""

from __future__ import annotations

from typing import Any, Optional

from sqlalchemy.orm import Session

from .models import AttributionSession, get_db


def build_session_data_from_db(session_id: str, db: Session) -> Optional[dict[str, Any]]:
    """从数据库构建报告所需的会话数据.

    Args:
        session_id: 会话ID
        db: 数据库会话

    Returns:
        格式化的会话数据字典；若会话不存在则返回 None
    """
    from datetime import datetime

    session = db.query(AttributionSession).filter(AttributionSession.session_id == session_id).first()
    if not session:
        return None

    # 构建步骤数据
    steps = []
    for step in sorted(session.steps, key=lambda s: s.step_number):
        steps.append({
            "step_number": step.step_number,
            "node_id": step.node_id,
            "node_name": step.node_name,
            "node_type": step.node_type,
            "selected_dimension": step.selected_dimension,
            "selected_child": step.selected_child,
            "entropy_results": step.entropy_results or [],
            "cross_dimension_results": step.cross_dimension_results or [],
            "contributions": step.contributions or {},
        })

    # 构建结论数据
    conclusion = None
    if session.conclusion:
        conclusion = {
            "reason_type": session.conclusion.reason_type,
            "detailed_explanation": session.conclusion.detailed_explanation,
            "involved_departments": session.conclusion.involved_departments or [],
            "suggested_actions": session.conclusion.suggested_actions,
            "confidence_level": session.conclusion.confidence_level,
            "referenced_files": session.conclusion.referenced_files or [],
        }

    return {
        "session_id": session_id,
        "analysis_mode": session.analysis_mode or "-",
        "current_state": session.current_state or "-",
        "start_date": session.start_date or "-",
        "end_date": session.end_date or "-",
        "comparison_period": session.comparison_period or "-",
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "steps": steps,
        "conclusion": conclusion,
    }

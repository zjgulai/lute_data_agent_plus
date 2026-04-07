"""数据库模型定义.

定义 GMV 归因系统的核心数据表结构。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

Base = declarative_base()


def generate_uuid() -> str:
    """生成 UUID 字符串."""
    return str(uuid.uuid4())


class AttributionSession(Base):
    """归因会话表.

    存储一次完整的归因分析任务。
    """

    __tablename__ = "attribution_sessions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False)
    user_role = Column(String(20), nullable=False)  # manager / business

    # 分析配置
    analysis_mode = Column(String(10), nullable=False)  # auto / manual
    indicator_tree_config = Column(Text, nullable=False)  # YAML 配置

    # 分析周期
    start_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    end_date = Column(String(10), nullable=False)
    comparison_period = Column(String(20), nullable=False)  # prev_month / yoy

    # 状态
    current_state = Column(String(30), nullable=False, default="INIT")
    status = Column(String(20), nullable=False, default="running")  # running / completed / error / terminated

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 关联数据
    steps = relationship("AttributionStep", back_populates="session", cascade="all, delete-orphan")
    conclusion = relationship("AttributionConclusion", back_populates="session", uselist=False)
    uploaded_files = relationship("UploadedFile", back_populates="session", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "user_role": self.user_role,
            "analysis_mode": self.analysis_mode,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "comparison_period": self.comparison_period,
            "current_state": self.current_state,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class AttributionStep(Base):
    """归因步骤表.

    存储每个步骤的计算结果。
    """

    __tablename__ = "attribution_steps"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(50), ForeignKey("attribution_sessions.session_id"), nullable=False)
    step_number = Column(Integer, nullable=False)  # 1-4

    # 节点信息
    node_id = Column(String(100), nullable=False)
    node_name = Column(String(100), nullable=False)
    node_type = Column(String(20), nullable=False)  # organization / operation / action

    # 维度分析结果
    selected_dimension = Column(String(50), nullable=True)
    selected_child = Column(String(100), nullable=True)
    entropy_results = Column(JSON, nullable=True)  # 熵减计算结果

    # 交叉维度
    cross_dimension_results = Column(JSON, nullable=True)
    cross_dimension_completed = Column(Integer, default=1)  # 0=no, 1=yes

    # 贡献度
    contributions = Column(JSON, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    session = relationship("AttributionSession", back_populates="steps")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "step_number": self.step_number,
            "node_id": self.node_id,
            "node_name": self.node_name,
            "node_type": self.node_type,
            "selected_dimension": self.selected_dimension,
            "selected_child": self.selected_child,
            "entropy_results": self.entropy_results,
            "cross_dimension_results": self.cross_dimension_results,
            "cross_dimension_completed": bool(self.cross_dimension_completed),
            "contributions": self.contributions,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class AttributionConclusion(Base):
    """归因结论表.

    存储用户提交的结构化业务结论。
    """

    __tablename__ = "attribution_conclusions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(50), ForeignKey("attribution_sessions.session_id"), unique=True, nullable=False)
    user_id = Column(String(50), nullable=False)

    # 结构化结论
    reason_type = Column(String(50), nullable=False)  # 如：预算削减、竞品动作、政策变化
    detailed_explanation = Column(Text, nullable=False)
    involved_departments = Column(JSON, nullable=True)  # ["市场部", "销售部"]
    suggested_actions = Column(Text, nullable=True)
    confidence_level = Column(String(10), nullable=False)  # high / medium / low

    # 引用的外部文件
    referenced_files = Column(JSON, nullable=True)  # ["file_id_1", "file_id_2"]

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    session = relationship("AttributionSession", back_populates="conclusion")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "reason_type": self.reason_type,
            "detailed_explanation": self.detailed_explanation,
            "involved_departments": self.involved_departments,
            "suggested_actions": self.suggested_actions,
            "confidence_level": self.confidence_level,
            "referenced_files": self.referenced_files,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class UploadedFile(Base):
    """上传文件表.

    存储用户上传的外部文件信息。
    """

    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    session_id = Column(String(50), ForeignKey("attribution_sessions.session_id"), nullable=False)

    # 文件信息
    original_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(20), nullable=False)  # pdf / word / excel
    file_size = Column(Integer, nullable=False)  # bytes

    # 解析结果
    parsed_content = Column(Text, nullable=True)
    parse_status = Column(String(20), default="pending")  # pending / success / error

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    # 关联
    session = relationship("AttributionSession", back_populates="uploaded_files")

    def to_dict(self) -> dict[str, Any]:
        """转换为字典."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "parse_status": self.parse_status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# 数据库连接管理
_engine = None
_SessionLocal = None


def init_db(database_url: str) -> None:
    """初始化数据库连接.

    Args:
        database_url: 数据库连接字符串，如 postgresql://user:pass@localhost/dbname
    """
    global _engine, _SessionLocal
    _engine = create_engine(database_url)
    _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)
    Base.metadata.create_all(bind=_engine)


def get_db():
    """获取数据库会话."""
    if _SessionLocal is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")

    db = _SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_engine():
    """获取数据库引擎."""
    if _engine is None:
        raise RuntimeError("数据库未初始化，请先调用 init_db()")
    return _engine

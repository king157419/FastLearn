"""
Session Summary Model
=====================

会话摘要的 SQLAlchemy ORM 模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, JSON, ForeignKey, CheckConstraint
from sqlalchemy.orm import relationship
from src.services.memory.database import Base


class SessionSummary(Base):
    """会话摘要表 ORM 模型"""

    __tablename__ = "session_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(64), nullable=False)

    # 摘要内容
    core_topic = Column(Text, nullable=False)
    key_points = Column(JSON, nullable=False, default=list)

    resolved_questions = Column(JSON, default=list)
    unresolved_questions = Column(JSON, default=list)

    # 用户偏好（从对话中提取）
    user_preferences = Column(JSON, default=dict)

    # 薄弱知识点
    weak_points = Column(JSON, default=list)

    # 分区字段
    subject = Column(String(50))
    topic = Column(String(100))
    difficulty = Column(String(20))

    # 最近消息
    recent_messages = Column(JSON, default=list)

    # 元数据
    message_count = Column(Integer, default=0)
    token_count = Column(Integer, default=0)

    # 摘要质量指标
    summary_quality = Column(JSON, default=dict)

    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 约束
    __table_args__ = (
        CheckConstraint("LENGTH(session_id) > 0", name="session_summaries_session_id_not_empty"),
        CheckConstraint("LENGTH(user_id) > 0", name="session_summaries_user_id_not_empty"),
        CheckConstraint("LENGTH(core_topic) > 0", name="session_summaries_core_topic_not_empty"),
        CheckConstraint(
            "difficulty IN ('beginner', 'intermediate', 'advanced', NULL)",
            name="session_summaries_difficulty_check"
        ),
    )

    def __repr__(self):
        return f"<SessionSummary(session_id='{self.session_id}', user_id='{self.user_id}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "user_id": self.user_id,
            "core_topic": self.core_topic,
            "key_points": self.key_points,
            "resolved_questions": self.resolved_questions,
            "unresolved_questions": self.unresolved_questions,
            "user_preferences": self.user_preferences,
            "weak_points": self.weak_points,
            "subject": self.subject,
            "topic": self.topic,
            "difficulty": self.difficulty,
            "recent_messages": self.recent_messages,
            "message_count": self.message_count,
            "token_count": self.token_count,
            "summary_quality": self.summary_quality,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

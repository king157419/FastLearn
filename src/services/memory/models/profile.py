"""
User Profile Model
===================

用户画像的 SQLAlchemy ORM 模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, CheckConstraint
from sqlalchemy.orm import declarative_base
from src.services.memory.database import Base


class UserProfile(Base):
    """用户画像表 ORM 模型"""

    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(64), unique=True, nullable=False)

    # 学习偏好（JSONB）
    preferences = Column(JSON, nullable=False, default=dict)

    # 学习统计（JSONB）
    statistics = Column(JSON, default=dict)

    # 知识图谱（JSONB）
    knowledge_graph = Column(JSON, default=dict)

    # 兴趣领域（JSONB）
    interests = Column(JSON, default=list)

    # 薄弱知识点（JSONB）
    weak_points = Column(JSON, default=list)

    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 约束
    __table_args__ = (
        CheckConstraint("preferences IS NOT NULL", name="user_preferences_not_null"),
        CheckConstraint("LENGTH(user_id) > 0", name="user_id_not_empty"),
    )

    def __repr__(self):
        return f"<UserProfile(user_id='{self.user_id}')>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "preferences": self.preferences,
            "statistics": self.statistics,
            "knowledge_graph": self.knowledge_graph,
            "interests": self.interests,
            "weak_points": self.weak_points,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

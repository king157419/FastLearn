"""
CRUD Operations for Memory System
==================================

数据库增删改查操作
"""

from typing import Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from src.services.memory.models.profile import UserProfile
from src.services.memory.models.session import SessionSummary
from src.services.memory.models.embedding import MemoryEmbedding
from src.services.memory.schemas import (
    LearningPreferences,
    UserProfileCreate,
    UserProfileUpdate,
    SessionSummaryCreate,
    SessionSummaryUpdate,
)
from src.logging import get_logger

logger = get_logger("MemoryCRUD")


# ============================================
# UserProfile CRUD
# ============================================

def get_user_profile(session: Session, user_id: str) -> Optional[UserProfile]:
    """获取用户画像"""
    return session.query(UserProfile).filter(UserProfile.user_id == user_id).first()


def create_user_profile(
    session: Session,
    user_id: str,
    preferences: dict[str, Any] | None = None
) -> UserProfile:
    """创建用户画像"""
    default_preferences = {
        "learning_style": "textual",
        "difficulty_preference": "intermediate",
        "language": "zh-CN",
        "include_code": True,
        "include_math": True,
        "response_format": "html",
    }

    profile = UserProfile(
        user_id=user_id,
        preferences=preferences or default_preferences,
        statistics={
            "total_sessions": 0,
            "total_questions": 0,
            "active_days": 0,
            "avg_session_length": 0,
            "most_active_hour": None,
            "last_active_date": None,
        },
        knowledge_graph={},
        interests=[],
        weak_points=[],
    )
    session.add(profile)
    session.flush()

    logger.info(f"Created user profile: {user_id}")
    return profile


def update_user_profile(
    session: Session,
    user_id: str,
    update_data: UserProfileUpdate
) -> Optional[UserProfile]:
    """更新用户画像"""
    profile = get_user_profile(session, user_id)

    if profile is None:
        return None

    if update_data.preferences is not None:
        profile.preferences = update_data.preferences.model_dump()

    if update_data.interests is not None:
        profile.interests = update_data.interests

    profile.updated_at = datetime.utcnow()

    session.flush()

    logger.info(f"Updated user profile: {user_id}")
    return profile


def update_profile_preferences(
    session: Session,
    user_id: str,
    preferences_delta: dict[str, Any]
) -> Optional[UserProfile]:
    """更新用户偏好 (部分更新)"""
    profile = get_user_profile(session, user_id)

    if profile is None:
        profile = create_user_profile(session, user_id)

    # 合并偏好
    profile.preferences.update(preferences_delta)
    profile.updated_at = datetime.utcnow()

    session.flush()

    return profile


def increment_profile_statistics(
    session: Session,
    user_id: str,
    increment_sessions: bool = False,
    increment_questions: bool = False,
    increment_active_days: bool = False,
    session_length: float | None = None
) -> UserProfile:
    """更新用户统计数据"""
    profile = get_user_profile(session, user_id)

    if profile is None:
        profile = create_user_profile(session, user_id)

    # Get a reference to statistics and make a copy to ensure SQLAlchemy detects changes
    statistics = dict(profile.statistics)

    # Get old session count before incrementing
    old_total_sessions = statistics.get("total_sessions", 0)

    if increment_sessions:
        statistics["total_sessions"] = old_total_sessions + 1

    if increment_questions:
        statistics["total_questions"] = statistics.get("total_questions", 0) + 1

    if increment_active_days:
        # Count unique active days (simplified - just increment)
        statistics["active_days"] = statistics.get("active_days", 0) + 1

    if session_length is not None:
        # 更新平均会话长度 - use old session count for correct average
        new_total_sessions = old_total_sessions + 1
        current_avg = statistics.get("avg_session_length", 0)
        if new_total_sessions > 1:
            new_avg = (current_avg * old_total_sessions + session_length) / new_total_sessions
        else:
            new_avg = session_length
        statistics["avg_session_length"] = round(new_avg, 2)

    statistics["last_active_date"] = datetime.utcnow().isoformat()

    # Assign back to trigger SQLAlchemy's dirty tracking
    profile.statistics = statistics
    profile.updated_at = datetime.utcnow()

    session.flush()

    logger.info(f"Incremented statistics for {user_id}: sessions={statistics.get('total_sessions')}")
    return profile


def update_knowledge_graph(
    session: Session,
    user_id: str,
    concept: str,
    mastery_delta: float | None = None,
    interaction_delta: int = 1,
    confusion_delta: int | None = None,
    subject: str | None = None,
    topic: str | None = None,
    difficulty: str | None = None
) -> UserProfile:
    """更新知识图谱"""
    profile = get_user_profile(session, user_id)

    if profile is None:
        profile = create_user_profile(session, user_id)

    if concept not in profile.knowledge_graph:
        profile.knowledge_graph[concept] = {
            "mastery_level": 0.0,
            "last_reviewed": datetime.utcnow().isoformat(),
            "interaction_count": 0,
            "confusion_score": 0,
            "subject": subject,
            "topic": topic,
            "difficulty": difficulty,
        }

    # 更新掌握度
    if mastery_delta is not None:
        current = profile.knowledge_graph[concept]["mastery_level"]
        profile.knowledge_graph[concept]["mastery_level"] = max(0.0, min(1.0, current + mastery_delta))

    # 更新交互次数
    profile.knowledge_graph[concept]["interaction_count"] += interaction_delta

    # 更新困惑度
    if confusion_delta is not None:
        current = profile.knowledge_graph[concept]["confusion_score"]
        profile.knowledge_graph[concept]["confusion_score"] = max(0, min(100, current + confusion_delta))

    profile.knowledge_graph[concept]["last_reviewed"] = datetime.utcnow().isoformat()

    # 更新元数据
    if subject is not None:
        profile.knowledge_graph[concept]["subject"] = subject
    if topic is not None:
        profile.knowledge_graph[concept]["topic"] = topic
    if difficulty is not None:
        profile.knowledge_graph[concept]["difficulty"] = difficulty

    profile.updated_at = datetime.utcnow()

    session.flush()

    return profile


def update_weak_points(
    session: Session,
    user_id: str,
    weak_points_list: list[dict[str, Any]]
) -> UserProfile:
    """更新薄弱知识点"""
    profile = get_user_profile(session, user_id)

    if profile is None:
        profile = create_user_profile(session, user_id)

    existing_weak_points = {wp["concept"]: wp for wp in profile.weak_points}

    for new_wp in weak_points_list:
        concept = new_wp["concept"]

        if concept in existing_weak_points:
            # 更新现有薄弱点
            existing = existing_weak_points[concept]
            if new_wp.get("confusion_score", 0) > existing.get("confusion_score", 0):
                existing["confusion_score"] = new_wp["confusion_score"]
                existing["last_confused"] = new_wp.get("last_confused", datetime.utcnow().isoformat())
        else:
            # 添加新薄弱点
            profile.weak_points.append(new_wp)

    # 按困惑度排序
    profile.weak_points.sort(key=lambda x: x.get("confusion_score", 0), reverse=True)

    profile.updated_at = datetime.utcnow()

    session.flush()

    return profile


# ============================================
# SessionSummary CRUD
# ============================================

def get_session_summary(session: Session, session_id: str) -> Optional[SessionSummary]:
    """获取会话摘要"""
    return session.query(SessionSummary).filter(SessionSummary.session_id == session_id).first()


def create_session_summary(
    session: Session,
    summary_data: SessionSummaryCreate
) -> SessionSummary:
    """创建会话摘要"""
    summary = SessionSummary(
        session_id=summary_data.session_id,
        user_id=summary_data.user_id,
        core_topic=summary_data.core_topic,
        key_points=summary_data.key_points,
        resolved_questions=summary_data.resolved_questions,
        unresolved_questions=summary_data.unresolved_questions,
        user_preferences=summary_data.user_preferences,
        weak_points=summary_data.weak_points,
        subject=summary_data.subject,
        topic=summary_data.topic,
        difficulty=summary_data.difficulty,
        recent_messages=summary_data.recent_messages,
        message_count=summary_data.message_count,
        token_count=summary_data.token_count,
        summary_quality={
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": "SummarizerAgent",
        },
    )
    session.add(summary)
    session.flush()

    logger.info(f"Created session summary: {summary_data.session_id}")
    return summary


def update_session_summary(
    session: Session,
    session_id: str,
    update_data: SessionSummaryUpdate
) -> Optional[SessionSummary]:
    """更新会话摘要"""
    summary = get_session_summary(session, session_id)

    if summary is None:
        return None

    if update_data.core_topic is not None:
        summary.core_topic = update_data.core_topic

    if update_data.key_points is not None:
        summary.key_points = update_data.key_points

    if update_data.resolved_questions is not None:
        summary.resolved_questions = update_data.resolved_questions

    if update_data.unresolved_questions is not None:
        summary.unresolved_questions = update_data.unresolved_questions

    if update_data.weak_points is not None:
        summary.weak_points = update_data.weak_points

    summary.updated_at = datetime.utcnow()

    session.flush()

    logger.info(f"Updated session summary: {session_id}")
    return summary


def get_user_session_summaries(
    session: Session,
    user_id: str,
    days: int = 7,
    limit: int = 10
) -> list[SessionSummary]:
    """获取用户的会话摘要列表"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    return (
        session.query(SessionSummary)
        .filter(
            SessionSummary.user_id == user_id,
            SessionSummary.created_at >= cutoff_date
        )
        .order_by(SessionSummary.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_summaries_by_topic(
    session: Session,
    user_id: str,
    topic: str,
    days: int = 30
) -> list[SessionSummary]:
    """按主题获取用户的会话摘要"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    return (
        session.query(SessionSummary)
        .filter(
            SessionSummary.user_id == user_id,
            SessionSummary.topic == topic,
            SessionSummary.created_at >= cutoff_date
        )
        .order_by(SessionSummary.created_at.desc())
        .all()
    )


# ============================================
# MemoryEmbedding CRUD
# ============================================

def create_memory_embedding(
    session: Session,
    memory_id: int,
    user_id: str,
    session_id: str,
    embedding: list[float],
    metadata: dict[str, Any] | None = None
) -> MemoryEmbedding:
    """创建向量嵌入"""
    memory_emb = MemoryEmbedding(
        memory_id=memory_id,
        user_id=user_id,
        session_id=session_id,
        embedding=embedding,
        metadata=metadata or {},
    )
    session.add(memory_emb)
    session.flush()

    return memory_emb


def get_user_embeddings(
    session: Session,
    user_id: str,
    days: int = 7
) -> list[MemoryEmbedding]:
    """获取用户的向量嵌入"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    return (
        session.query(MemoryEmbedding)
        .filter(
            MemoryEmbedding.user_id == user_id,
            MemoryEmbedding.created_at >= cutoff_date
        )
        .order_by(MemoryEmbedding.created_at.desc())
        .all()
    )

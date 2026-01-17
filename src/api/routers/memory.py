"""
Memory System API Router
=========================

记忆系统的 API 路由
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from src.services.memory.database import get_db_session
from src.services.memory.crud import (
    get_user_profile,
    update_profile_preferences,
    get_user_session_summaries,
    create_session_summary,
    update_session_summary,
    get_session_summary,
)
from src.services.memory.schemas import (
    UserProfileResponse,
    UserProfileUpdate,
    SessionSummaryResponse,
    SessionSummaryCreate,
    SessionSummaryUpdate,
    MemoryContextResponse,
    MemorySearchRequest,
    SummaryTriggerRequest,
    SummaryTriggerResponse,
)
from src.agents.memory.summarizer_agent import SummarizerAgent
from src.agents.memory.profile_agent import ProfileAgent
from src.agents.memory.retrieval_agent import RetrievalAgent
from src.logging import get_logger

logger = get_logger("MemoryAPI")

router = APIRouter()


# ============================================
# 用户画像 API
# ============================================

@router.get("/profiles/{user_id}", response_model=UserProfileResponse)
async def get_profile(user_id: str) -> UserProfileResponse:
    """
    获取用户画像

    Args:
        user_id: 用户 ID

    Returns:
        用户画像数据
    """
    with get_db_session() as session:
        profile = get_user_profile(session, user_id)

        if profile is None:
            # 创建默认画像
            from src.services.memory.database import get_or_create_profile
            profile, _ = get_or_create_profile(session, user_id)

        return UserProfileResponse(**profile.to_dict())


@router.patch("/profiles/{user_id}/preferences")
async def update_preferences(
    user_id: str,
    update_data: UserProfileUpdate
) -> dict[str, Any]:
    """
    更新用户偏好

    Args:
        user_id: 用户 ID
        update_data: 更新数据

    Returns:
        更新结果
    """
    with get_db_session() as session:
        profile = update_profile_preferences(session, user_id, update_data)

        if profile is None:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "success": True,
            "message": "偏好已更新",
            "profile": profile.to_dict(),
        }


# ============================================
# 会话摘要 API
# ============================================

@router.get("/sessions/{session_id}/summary", response_model=SessionSummaryResponse)
async def get_session_summary_api(session_id: str) -> SessionSummaryResponse:
    """
    获取会话摘要

    Args:
        session_id: 会话 ID

    Returns:
        会话摘要数据
    """
    with get_db_session() as session:
        summary = get_session_summary(session, session_id)

        if summary is None:
            raise HTTPException(status_code=404, detail="会话摘要不存在")

        return SessionSummaryResponse(**summary.to_dict())


@router.post("/sessions/{session_id}/summarize")
async def trigger_summary(
    session_id: str,
    request: SummaryTriggerRequest
) -> SummaryTriggerResponse:
    """
    触发会话摘要生成

    Args:
        session_id: 会话 ID
        request: 摘要请求

    Returns:
        摘要生成结果
    """
    agent = SummarizerAgent()

    result = await agent.process(
        session_id=session_id,
        user_id=request.user_id,
        messages=request.messages,
        force=request.force
    )

    return SummaryTriggerResponse(**result)


@router.get("/sessions/{user_id}/list")
async def list_user_sessions(
    user_id: str,
    days: int = Query(default=7, ge=1, le=365),
    limit: int = Query(default=10, ge=1, le=100)
) -> dict[str, Any]:
    """
    获取用户的会话摘要列表

    Args:
        user_id: 用户 ID
        days: 最近几天
        limit: 返回数量限制

    Returns:
        会话摘要列表
    """
    with get_db_session() as session:
        summaries = get_user_session_summaries(session, user_id, days, limit)

        return {
            "success": True,
            "user_id": user_id,
            "days": days,
            "count": len(summaries),
            "sessions": [s.to_dict() for s in summaries],
        }


# ============================================
# 记忆检索 API
# ============================================

@router.get("/context", response_model=MemoryContextResponse)
async def get_memory_context(
    user_id: str = Query(..., description="用户 ID"),
    query: str = Query(..., description="查询内容"),
    days: int = Query(default=7, ge=1, le=365, description="检索最近几天的记忆"),
    subject: str | None = Query(default=None, description="学科过滤"),
    topic: str | None = Query(default=None, description="主题过滤")
) -> MemoryContextResponse:
    """
    获取跨会话上下文

    这是核心 API，用于在用户发起新对话时获取相关历史信息

    Args:
        user_id: 用户 ID
        query: 查询内容
        days: 检索最近几天的记忆
        subject: 学科过滤
        topic: 主题过滤

    Returns:
        上下文信息
    """
    agent = RetrievalAgent()

    result = await agent.process(
        user_id=user_id,
        query=query,
        days=days,
        subject=subject,
        topic=topic
    )

    return MemoryContextResponse(**result)


@router.post("/search")
async def search_memories(request: MemorySearchRequest) -> dict[str, Any]:
    """
    搜索用户记忆

    Args:
        request: 搜索请求

    Returns:
        搜索结果
    """
    agent = RetrievalAgent()

    result = await agent.process(
        user_id=request.user_id,
        query=request.query,
        days=request.days,
        subject=request.subject,
        topic=request.topic
    )

    return {
        "success": True,
        **result
    }


# ============================================
# 统计 API
# ============================================

@router.get("/stats/{user_id}")
async def get_user_stats(user_id: str) -> dict[str, Any]:
    """
    获取用户学习统计

    Args:
        user_id: 用户 ID

    Returns:
        学习统计数据
    """
    with get_db_session() as session:
        profile = get_user_profile(session, user_id)

        if profile is None:
            return {
                "user_id": user_id,
                "total_sessions": 0,
                "total_questions": 0,
                "active_days": 0,
            }

        stats = profile.statistics.copy()
        stats["user_id"] = user_id

        # 获取最近会话数
        recent_summaries = get_user_session_summaries(session, user_id, days=30, limit=100)
        stats["recent_sessions_30d"] = len(recent_summaries)

        # 统计薄弱知识点
        weak_points = profile.weak_points or []
        stats["weak_points_count"] = len(weak_points)
        stats["top_weak_points"] = weak_points[:5] if weak_points else []

        # 统计知识掌握度
        knowledge_graph = profile.knowledge_graph or {}
        mastered = sum(1 for v in knowledge_graph.values() if v.get("mastery_level", 0) > 0.7)
        stats["knowledge_points_count"] = len(knowledge_graph)
        stats["mastered_points_count"] = mastered

        return stats


# ============================================
# 健康检查
# ============================================

@router.get("/health")
async def health_check() -> dict[str, Any]:
    """
    健康检查

    Returns:
        健康状态
    """
    from src.services.memory.database import test_connection

    db_ok = test_connection()

    return {
        "status": "healthy" if db_ok else "degraded",
        "database": "connected" if db_ok else "disconnected",
    }

"""
Pydantic Schemas for Memory System
==================================

用于 API 请求和响应的 Pydantic 模型
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, field_validator


# ============================================
# 用户画像相关 Schemas
# ============================================

class LearningPreferences(BaseModel):
    """用户学习偏好"""

    learning_style: Literal["visual", "textual", "hands_on", "code_first"] = "textual"
    difficulty_preference: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    language: str = "zh-CN"
    include_code: bool = True
    include_math: bool = True
    response_format: Literal["text", "html", "markdown"] = "html"

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class LearningStatistics(BaseModel):
    """学习统计数据"""

    total_sessions: int = 0
    total_questions: int = 0
    active_days: int = 0
    avg_session_length: float = 0.0  # 分钟
    most_active_hour: int | None = None  # 24小时制
    last_active_date: str | None = None  # ISO format


class KnowledgePoint(BaseModel):
    """知识点掌握度"""

    mastery_level: float = Field(default=0.0, ge=0.0, le=1.0)
    last_reviewed: str | None = None  # ISO format
    interaction_count: int = 0
    confusion_score: int = Field(default=0, ge=0, le=100)
    subject: str | None = None
    topic: str | None = None
    difficulty: Literal["beginner", "intermediate", "advanced"] | None = None


class WeakPoint(BaseModel):
    """薄弱知识点"""

    concept: str
    confusion_score: int = Field(default=50, ge=0, le=100)
    last_confused: str | None = None  # ISO format
    subject: str | None = None
    topic: str | None = None


class UserProfileCreate(BaseModel):
    """创建用户画像请求"""

    user_id: str
    preferences: LearningPreferences | None = None


class UserProfileUpdate(BaseModel):
    """更新用户画像请求"""

    preferences: LearningPreferences | None = None
    interests: list[str] | None = None


class UserProfileResponse(BaseModel):
    """用户画像响应"""

    id: int
    user_id: str
    preferences: dict[str, Any]
    statistics: dict[str, Any]
    knowledge_graph: dict[str, Any] = Field(default_factory=dict)
    interests: list[str] = Field(default_factory=list)
    weak_points: list[dict[str, Any]] = Field(default_factory=list)
    created_at: str | None = None
    updated_at: str | None = None


# ============================================
# 会话摘要相关 Schemas
# ============================================

class SessionSummaryCreate(BaseModel):
    """创建会话摘要请求"""

    session_id: str
    user_id: str
    core_topic: str
    key_points: list[str]
    resolved_questions: list[str] = Field(default_factory=list)
    unresolved_questions: list[str] = Field(default_factory=list)
    user_preferences: dict[str, Any] = Field(default_factory=dict)
    weak_points: list[dict[str, Any]] = Field(default_factory=list)
    subject: str | None = None
    topic: str | None = None
    difficulty: Literal["beginner", "intermediate", "advanced"] | None = None
    recent_messages: list[dict[str, Any]] = Field(default_factory=list)
    message_count: int = 0
    token_count: int = 0


class SessionSummaryResponse(BaseModel):
    """会话摘要响应"""

    id: int
    session_id: str
    user_id: str
    core_topic: str
    key_points: list[str]
    resolved_questions: list[str]
    unresolved_questions: list[str]
    user_preferences: dict[str, Any]
    weak_points: list[dict[str, Any]]
    subject: str | None = None
    topic: str | None = None
    difficulty: str | None = None
    recent_messages: list[dict[str, Any]]
    message_count: int
    token_count: int
    summary_quality: dict[str, Any]
    created_at: str | None = None
    updated_at: str | None = None


class SessionSummaryUpdate(BaseModel):
    """更新会话摘要请求"""

    core_topic: str | None = None
    key_points: list[str] | None = None
    resolved_questions: list[str] | None = None
    unresolved_questions: list[str] | None = None
    weak_points: list[dict[str, Any]] | None = None


# ============================================
# 记忆检索相关 Schemas
# ============================================

class MemorySearchRequest(BaseModel):
    """记忆检索请求"""

    user_id: str
    query: str
    subject: str | None = None
    topic: str | None = None
    days: int = Field(default=7, ge=1, le=365)
    limit: int = Field(default=10, ge=1, le=100)
    use_semantic_search: bool = True


class MemoryContextResponse(BaseModel):
    """记忆上下文响应"""

    context: str
    source_memories: list[dict[str, Any]]
    user_profile: dict[str, Any] | None = None
    weak_points: list[dict[str, Any]] = Field(default_factory=list)


# ============================================
# Agent 通信相关 Schemas
# ============================================

class SummaryTriggerRequest(BaseModel):
    """触发摘要生成请求"""

    session_id: str
    user_id: str
    messages: list[dict[str, str]]
    force: bool = False


class SummaryTriggerResponse(BaseModel):
    """触发摘要生成响应"""

    success: bool
    summary_id: int | None = None
    message: str
    should_summarize: bool = False


class ProfileUpdateRequest(BaseModel):
    """更新画像请求 (内部 Agent 使用)"""

    user_id: str
    preferences_delta: dict[str, Any] | None = None
    increment_sessions: bool = False
    increment_questions: bool = False
    update_knowledge_graph: dict[str, Any] | None = None
    update_weak_points: list[dict[str, Any]] | None = None

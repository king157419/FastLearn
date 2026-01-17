"""
Database Connection Module
==========================

PostgreSQL 数据库连接和会话管理
"""

from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from src.logging import get_logger

logger = get_logger("MemoryDatabase")

# 创建 Base 类
Base = declarative_base()

# 全局 engine 和 session maker
_engine = None
_SessionLocal = None


def get_engine():
    """
    获取数据库引擎 (单例模式)

    Returns:
        SQLAlchemy Engine
    """
    global _engine

    if _engine is None:
        # 从 .env.memory 加载配置
        from pathlib import Path
        import os
        from dotenv import load_dotenv

        project_root = Path(__file__).parent.parent.parent
        env_file = project_root / ".env.memory"

        if env_file.exists():
            load_dotenv(env_file)

        database_url = os.getenv(
            "DATABASE_URL",
            "postgresql://deeptutor:deeptutor_password@localhost:5433/deeptutor_memory"
        )

        pool_size = int(os.getenv("DB_POOL_SIZE", 20))
        max_overflow = int(os.getenv("DB_MAX_OVERFLOW", 10))
        pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", 30))
        pool_recycle = int(os.getenv("DB_POOL_RECYCLE", 3600))

        # 创建 engine
        _engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_timeout=pool_timeout,
            pool_recycle=pool_recycle,
            echo=False,
        )

        logger.info(
            "Database engine created",
            extra={
                "url": database_url.split("@")[-1] if "@" in database_url else database_url[:30],
                "pool_size": pool_size,
            }
        )

    return _engine


def get_session_factory():
    """
    获取 Session 工厂 (单例模式)

    Returns:
        sessionmaker
    """
    global _SessionLocal

    if _SessionLocal is None:
        _SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )

    return _SessionLocal


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话 (上下文管理器)

    使用方式:
        with get_db_session() as session:
            session.query(UserProfile).first()

    Yields:
        Session: SQLAlchemy 会话
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def init_database():
    """
    初始化数据库 (创建表)

    此函数不会删除现有数据，仅创建不存在的表
    """
    try:
        engine = get_engine()

        # 导入所有模型
        from src.services.memory.models.profile import UserProfile
        from src.services.memory.models.session import SessionSummary
        from src.services.memory.models.embedding import MemoryEmbedding

        # 创建所有表
        Base.metadata.create_all(bind=engine)

        logger.info("Database tables created/verified")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def test_connection() -> bool:
    """
    测试数据库连接

    Returns:
        bool: 连接是否成功
    """
    try:
        from sqlalchemy import text

        with get_db_session() as session:
            # 执行简单查询
            session.execute(text("SELECT 1"))

        logger.info("Database connection test successful")
        return True

    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


# ============================================
# 数据库操作辅助函数
# ============================================

def get_or_create_profile(session: Session, user_id: str) -> tuple:
    """
    获取或创建用户画像

    Args:
        session: 数据库会话
        user_id: 用户 ID

    Returns:
        (UserProfile, created) 元组，created 表示是否新创建
    """
    from src.services.memory.models.profile import UserProfile

    profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()

    if profile is None:
        profile = UserProfile(
            user_id=user_id,
            preferences={
                "learning_style": "textual",
                "difficulty_preference": "intermediate",
                "language": "zh-CN",
                "include_code": True,
                "include_math": True,
                "response_format": "html",
            },
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

        return profile, True

    return profile, False


def get_session_summary(
    session: Session,
    session_id: str
) -> object | None:
    """
    获取会话摘要

    Args:
        session: 数据库会话
        session_id: 会话 ID

    Returns:
        SessionSummary 对象或 None
    """
    from src.services.memory.models.session import SessionSummary

    return (
        session.query(SessionSummary)
        .filter(SessionSummary.session_id == session_id)
        .first()
    )


def get_recent_summaries(
    session: Session,
    user_id: str,
    days: int = 7,
    limit: int = 10
) -> list:
    """
    获取最近的会话摘要

    Args:
        session: 数据库会话
        user_id: 用户 ID
        days: 最近几天
        limit: 返回数量限制

    Returns:
        SessionSummary 对象列表
    """
    from src.services.memory.models.session import SessionSummary
    from datetime import datetime, timedelta

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


# 测试
if __name__ == "__main__":
    # 测试数据库连接
    if test_connection():
        print("Database connection successful!")

        # 测试获取/创建用户画像
        with get_db_session() as session:
            profile, created = get_or_create_profile(session, "test_user_001")
            print(f"Profile {'created' if created else 'retrieved'}: {profile}")

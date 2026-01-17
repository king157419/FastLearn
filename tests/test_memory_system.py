"""
Memory System Database Connection Test
=======================================

测试数据库连接和基本操作
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.memory.database import (
    get_db_session,
    test_connection,
    get_or_create_profile,
    init_database,
)
from src.services.memory.config import get_config


def test_config_loading():
    """测试配置加载"""
    print("\n" + "=" * 50)
    print("Test 1: Configuration Loading")
    print("=" * 50)

    config = get_config()

    print(f"Database URL: {config.database.database_url}")
    print(f"Embedding Provider: {config.embedding.embedding_provider}")
    print(f"Embedding Model: {config.embedding.embedding_model}")
    print(f"Summary Trigger Rounds: {config.summary.summary_trigger_rounds}")
    print("Configuration loaded successfully!")


def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("Test 2: Database Connection")
    print("=" * 50)

    if test_connection():
        print("Database connection successful!")
        return True
    else:
        print("Database connection failed!")
        return False


def test_create_profile():
    """测试创建用户画像"""
    print("\n" + "=" * 50)
    print("Test 3: Create User Profile")
    print("=" * 50)

    try:
        with get_db_session() as session:
            profile, created = get_or_create_profile(session, "test_user_001")

            print(f"Profile {'created' if created else 'retrieved'}: {profile}")
            print(f"User ID: {profile.user_id}")
            print(f"Preferences: {profile.preferences}")
            print(f"Statistics: {profile.statistics}")

            return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def test_session_summary():
    """测试会话摘要"""
    print("\n" + "=" * 50)
    print("Test 4: Session Summary Operations")
    print("=" * 50)

    try:
        from src.services.memory.crud import (
            create_session_summary,
            get_session_summary,
            get_user_session_summaries,
        )
        from src.services.memory.schemas import SessionSummaryCreate

        with get_db_session() as session:
            # 创建测试摘要
            summary_data = SessionSummaryCreate(
                session_id="test_session_001",
                user_id="test_user_001",
                core_topic="测试主题",
                key_points=["知识点1", "知识点2", "知识点3"],
                resolved_questions=["问题1"],
                unresolved_questions=["问题2"],
                subject="计算机",
                topic="测试",
                difficulty="intermediate",
                message_count=10,
                token_count=500,
            )

            created = create_session_summary(session, summary_data)
            print(f"Created summary: {created.id}")

            # 检索摘要
            retrieved = get_session_summary(session, "test_session_001")
            print(f"Retrieved summary: {retrieved.core_topic if retrieved else 'None'}")

            # 获取用户摘要列表
            summaries = get_user_session_summaries(session, "test_user_001", days=7)
            print(f"User summaries count: {len(summaries)}")

            return True

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """运行所有测试"""
    print("\n" + "=" * 50)
    print("DeepTutor Memory System - Connection Tests")
    print("=" * 50)

    results = []

    # Test 1: Configuration
    try:
        test_config_loading()
        results.append(("Configuration", True))
    except Exception as e:
        print(f"Configuration test failed: {e}")
        results.append(("Configuration", False))

    # Test 2: Database Connection
    db_ok = test_database_connection()
    results.append(("Database Connection", db_ok))

    if not db_ok:
        print("\n" + "=" * 50)
        print("Database connection failed. Skipping remaining tests.")
        print("Please ensure PostgreSQL is running:")
        print("  docker compose -f docker-compose.pgvector.yml up -d")
        print("=" * 50)
        return

    # Test 3: Create Profile
    try:
        test_create_profile()
        results.append(("Create Profile", True))
    except Exception as e:
        print(f"Create profile test failed: {e}")
        results.append(("Create Profile", False))

    # Test 4: Session Summary
    try:
        test_session_summary()
        results.append(("Session Summary", True))
    except Exception as e:
        print(f"Session summary test failed: {e}")
        results.append(("Session Summary", False))

    # Summary
    print("\n" + "=" * 50)
    print("Test Summary")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"  {name}: {status}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("All tests passed!")
    else:
        print(f"Warning: {total - passed} test(s) failed")


if __name__ == "__main__":
    main()

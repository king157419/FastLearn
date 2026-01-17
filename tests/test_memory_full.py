"""
Memory System 完整测试
=====================

测试记忆系统的所有功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


async def test_memory_system():
    """测试记忆系统完整流程"""

    print("=" * 60)
    print("DeepTutor Memory System - 完整测试")
    print("=" * 60)

    # 测试 1: 数据库连接
    print("\n[测试 1] 数据库连接...")
    try:
        from src.services.memory.database import test_connection, init_database

        if test_connection():
            print("  [OK] 数据库连接成功")
        else:
            print("  [FAIL] 数据库连接失败，请先启动：")
            print("     docker compose -f docker-compose.pgvector.yml up -d")
            return
    except Exception as e:
        print(f"  [FAIL] 数据库连接错误: {e}")
        return

    # 测试 2: 创建用户画像
    print("\n[测试 2] 创建用户画像...")
    try:
        from src.services.memory.database import get_db_session
        from src.services.memory.crud import get_user_profile

        with get_db_session() as session:
            profile = get_user_profile(session, "test_user_001")

            if profile:
                print(f"  [OK] 用户画像已存在: {profile.user_id}")
            else:
                print("  [WARN]  用户画像为空，将创建新画像")

            # 显示用户信息
            if profile:
                print(f"  - 学习风格: {profile.preferences.get('learning_style', 'N/A')}")
                print(f"  - 难度偏好: {profile.preferences.get('difficulty_preference', 'N/A')}")
                print(f"  - 总会话数: {profile.statistics.get('total_sessions', 0)}")

    except Exception as e:
        print(f"  [FAIL] 用户画像测试失败: {e}")

    # 测试 3: 创建会话摘要
    print("\n[测试 3] 创建会话摘要...")
    try:
        from src.agents.memory.summarizer_agent import SummarizerAgent

        agent = SummarizerAgent()

        # 模拟对话消息
        messages = [
            {"role": "user", "content": "什么是梯度下降？"},
            {"role": "assistant", "content": "梯度下降是一种优化算法，通过计算梯度来更新参数。"},
            {"role": "user", "content": "那 SGD 呢？"},
            {"role": "assistant", "content": "SGD 是随机梯度下降，每次只用一个样本更新。"},
            {"role": "user", "content": "Adam 呢？"},
            {"role": "assistant", "content": "Adam 结合了动量和自适应学习率。"},
        ]

        # 添加更多消息以触发摘要
        for i in range(8):
            messages.append({"role": "user", "content": f"问题 {i+6}"})
            messages.append({"role": "assistant", "content": f"回答 {i+6}"})

        result = await agent.process(
            session_id="test_session_001",
            user_id="test_user_001",
            messages=messages,
            force=True
        )

        if result.get("success"):
            print("  [OK] 会话摘要生成成功")
            print(f"  - 核心主题: {result['summary'].get('core_topic', 'N/A')}")
            print(f"  - 关键知识点: {result['summary'].get('key_points', [])[:2]}")
            print(f"  - 摘要 ID: {result.get('summary_id')}")
        else:
            print(f"  [FAIL] 会话摘要生成失败: {result.get('message')}")

    except Exception as e:
        print(f"  [FAIL] 会话摘要测试失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试 4: 获取用户画像
    print("\n[测试 4] 获取用户画像...")
    try:
        from src.agents.memory.profile_agent import get_user_profile

        profile = await get_user_profile("test_user_001")

        if profile:
            print("  [OK] 用户画像获取成功")
            print(f"  - 用户 ID: {profile.get('user_id')}")
            print(f"  - 学习风格: {profile.get('preferences', {}).get('learning_style', 'N/A')}")
            print(f"  - 兴趣领域: {profile.get('interests', [])}")
        else:
            print("  [WARN]  用户画像为空")

    except Exception as e:
        print(f"  [FAIL] 获取用户画像失败: {e}")

    # 测试 5: 记忆检索
    print("\n[测试 5] 记忆检索...")
    try:
        from src.agents.memory.retrieval_agent import get_memory_context

        context = await get_memory_context(
            user_id="test_user_001",
            query="梯度下降",
            days=7
        )

        print("  [OK] 记忆检索成功")
        print(f"  - 上下文长度: {len(context)} 字符")
        print(f"  - 上下文预览: {context[:100]}...")

    except Exception as e:
        print(f"  [FAIL] 记忆检索失败: {e}")
        import traceback
        traceback.print_exc()

    # 测试 6: 统计数据
    print("\n[测试 6] 获取统计数据...")
    try:
        from src.services.memory.database import get_db_session
        from src.services.memory.crud import get_user_session_summaries

        with get_db_session() as session:
            summaries = get_user_session_summaries(session, "test_user_001", days=30)

            print(f"  [OK] 统计数据获取成功")
            print(f"  - 最近会话数: {len(summaries)}")

    except Exception as e:
        print(f"  [FAIL] 统计数据获取失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_memory_system())

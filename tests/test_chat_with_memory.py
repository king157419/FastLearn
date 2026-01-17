"""
Test Chat with Memory System
=============================

测试聊天与记忆系统的集成
"""

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.chat import ChatAgent


async def test_chat_with_memory():
    """测试带记忆的聊天"""

    print("=" * 60)
    print("测试聊天 + 记忆系统")
    print("=" * 60)

    # 创建一个测试用户
    user_id = "test_chat_user_001"
    session_id = "test_chat_session_001"

    # 初始化 Agent
    agent = ChatAgent(
        language="zh",
        user_id=user_id,
        session_id=session_id,
        enable_memory=True
    )

    # 第一次对话 - 关于梯度下降
    print("\n[第1次对话] 询问梯度下降...")
    response1 = await agent.process(
        message="什么是梯度下降？请用简单的话解释。",
        history=[],
        stream=False
    )

    print(f"回复: {response1['response'][:200]}...")
    print(f"来源: {list(response1.get('sources', {}).keys())}")

    # 第二次对话 - 继续讨论
    print("\n[第2次对话] 询问 SGD...")
    response2 = await agent.process(
        message="那 SGD 和普通梯度下降有什么区别？",
        history=[
            {"role": "user", "content": "什么是梯度下降？"},
            {"role": "assistant", "content": response1['response']}
        ],
        stream=False
    )

    print(f"回复: {response2['response'][:200]}...")
    print(f"来源: {list(response2.get('sources', {}).keys())}")

    # 检查记忆上下文
    if agent._memory_context:
        print(f"\n[记忆上下文] {agent._memory_context[:200]}...")

    # 第三次对话 - 测试记忆检索
    print("\n[第3次对话] 提到之前的话题...")
    response3 = await agent.process(
        message="刚才说的那个算法，它的学习率怎么设置？",
        history=[
            {"role": "user", "content": "什么是梯度下降？"},
            {"role": "assistant", "content": response1['response']},
            {"role": "user", "content": "那 SGD 和普通梯度下降有什么区别？"},
            {"role": "assistant", "content": response2['response']}
        ],
        stream=False
    )

    print(f"回复: {response3['response'][:200]}...")
    print(f"来源: {list(response3.get('sources', {}).keys())}")

    # 触发会话摘要
    print("\n[会话结束] 触发摘要生成...")
    summary_result = await agent.end_session(
        history=[
            {"role": "user", "content": "什么是梯度下降？"},
            {"role": "assistant", "content": response1['response']},
            {"role": "user", "content": "那 SGD 和普通梯度下降有什么区别？"},
            {"role": "assistant", "content": response2['response']},
            {"role": "user", "content": "刚才说的那个算法，它的学习率怎么设置？"},
            {"role": "assistant", "content": response3['response']}
        ]
    )

    print(f"摘要结果: {summary_result.get('success', False)}")
    print(f"是否生成摘要: {summary_result.get('should_summarize', False)}")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_chat_with_memory())

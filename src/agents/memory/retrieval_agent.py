"""
Retrieval Agent
===============

记忆检索 Agent - 检索相关历史记忆并生成上下文
"""

import json
from datetime import datetime, timedelta
from typing import Any

from src.agents.base_agent import BaseAgent
from src.logging import get_logger
from src.services.memory.database import get_db_session, get_or_create_profile
from src.services.memory.crud import (
    get_user_profile,
    get_user_session_summaries,
    update_knowledge_graph,
)
from src.services.memory.config import get_config

logger = get_logger("RetrievalAgent")


class RetrievalAgent(BaseAgent):
    """
    记忆检索 Agent

    功能：
    1. 根据用户查询检索相关历史记忆
    2. 生成结构化的上下文信息
    3. 支持按时间、主题过滤
    """

    def __init__(self, **kwargs):
        super().__init__(
            module_name="memory",
            agent_name="retrieval_agent",
            **kwargs
        )
        self.config = get_config()

    async def process(
        self,
        user_id: str,
        query: str,
        days: int = 7,
        subject: str | None = None,
        topic: str | None = None,
    ) -> dict[str, Any]:
        """
        处理记忆检索请求

        Args:
            user_id: 用户 ID
            query: 查询内容
            days: 检索最近几天的记忆
            subject: 学科过滤
            topic: 主题过滤

        Returns:
            检索结果字典
        """
        # 获取用户画像
        with get_db_session() as session:
            profile_obj = get_user_profile(session, user_id)
            profile = profile_obj.to_dict() if profile_obj else {}

            # 检索会话摘要
            summaries = get_user_session_summaries(session, user_id, days=days, limit=20)

            # 格式化为上下文
            memories_text = self._format_summaries(summaries)

            # 生成上下文
            context = await self._generate_context(
                query,
                profile,
                memories_text,
                days
            )

        return {
            "success": True,
            "context": context.get("suggested_context", ""),
            "source_memories": context.get("relevant_memories", []),
            "user_profile": profile,
            "weak_points": profile.get("weak_points", []),
        }

    def _format_summaries(self, summaries: list) -> str:
        """格式化摘要列表为文本"""
        if not summaries:
            return "暂无历史记忆"

        formatted = []
        for s in summaries:
            formatted.append(f"""
会话ID: {s.session_id}
日期: {s.created_at.strftime('%Y-%m-%d %H:%M') if s.created_at else 'N/A'}
核心主题: {s.core_topic}
关键知识点: {', '.join(s.key_points[:3])}
已解决问题: {', '.join(s.resolved_questions[:2])}
未解决问题: {', '.join(s.unresolved_questions[:2])}
---
            """.strip())

        return "\n\n".join(formatted)

    async def _generate_context(
        self,
        query: str,
        profile: dict[str, Any],
        memories_text: str,
        days: int
    ) -> dict[str, Any]:
        """生成上下文信息"""
        # 如果没有记忆，返回基础上下文
        if not memories_text or "暂无历史记忆" in memories_text:
            return {
                "suggested_context": self._get_basic_context(profile),
                "relevant_memories": [],
                "follow_up_suggestions": [],
            }

        # 获取提示词
        system_prompt = self.get_prompt("system", fallback="你是一个智能记忆检索助手。")
        user_prompt = self.get_prompt("user", fallback="请检索相关记忆。")

        # 使用字符串替换避免 JSON 中的 {} 被误解析
        try:
            profile_json = json.dumps(profile, ensure_ascii=False, indent=2)
            user_prompt = user_prompt.replace("{query}", str(query))
            user_prompt = user_prompt.replace("{profile}", profile_json)
            user_prompt = user_prompt.replace("{memories}", str(memories_text[-4000:]))
            user_prompt = user_prompt.replace("{days}", str(days))
        except Exception:
            # 如果替换失败，手动构造提示词
            user_prompt = f"""请根据用户画像和历史记忆，为以下查询生成上下文。

查询: {query}

用户画像:
{json.dumps(profile, ensure_ascii=False, indent=2)}

历史记忆:
{memories_text[-4000:]}

返回 JSON 格式，包含:
- suggested_context: 建议的上下文
- relevant_memories: 相关记忆列表
- follow_up_suggestions: 后续问题建议
"""

        try:
            # 调用 LLM
            response = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"},
                stage="retrieve_memory"
            )

            # 解析响应
            result = json.loads(response)
            return result

        except Exception as e:
            self.logger.error(f"Failed to generate context: {e}")
            # 返回基础上下文
            return {
                "suggested_context": self._get_basic_context(profile),
                "relevant_memories": [],
                "follow_up_suggestions": [],
            }

    def _get_basic_context(self, profile: dict[str, Any]) -> str:
        """获取基础上下文（当没有历史记忆时）"""
        preferences = profile.get("preferences", {})

        context_parts = []

        # 学习风格
        learning_style = preferences.get("learning_style", "textual")
        style_map = {
            "visual": "视觉型学习者（偏好图表、图像）",
            "textual": "文字型学习者（偏好文字解释）",
            "hands_on": "动手型学习者（偏好实践操作）",
            "code_first": "代码优先学习者（偏好先看代码示例）",
        }
        context_parts.append(f"- 学习风格：{style_map.get(learning_style, learning_style)}")

        # 难度偏好
        difficulty = preferences.get("difficulty_preference", "intermediate")
        difficulty_map = {
            "beginner": "初学者",
            "intermediate": "中级",
            "advanced": "高级",
        }
        context_parts.append(f"- 难度偏好：{difficulty_map.get(difficulty, difficulty)}")

        # 其他偏好
        if preferences.get("include_code"):
            context_parts.append("- 喜欢包含代码示例")
        if preferences.get("include_math"):
            context_parts.append("- 可以包含数学公式")

        # 薄弱知识点
        weak_points = profile.get("weak_points", [])
        if weak_points:
            top_weak = weak_points[:3]
            weak_list = [f"{wp.get('concept', '')}（困惑度{wp.get('confusion_score', 0)}）" for wp in top_weak]
            context_parts.append(f"- 薄弱知识点：{', '.join(weak_list)}")

        return "## 用户画像\n" + "\n".join(context_parts) if context_parts else "新用户，暂无画像信息"

    async def get_injection_context(
        self,
        user_id: str,
        query: str,
        days: int = 7
    ) -> str:
        """
        获取用于注入到 System Prompt 的上下文

        这是主要的使用场景：在用户发起新对话时，自动调用此方法
        获取相关上下文，然后注入到 LLM 的 System Prompt 中
        """
        result = await self.process(user_id, query, days)
        return result["context"]


# 便捷函数
async def get_memory_context(
    user_id: str,
    query: str,
    days: int = 7
) -> str:
    """便捷函数：获取记忆上下文"""
    agent = RetrievalAgent()
    return await agent.get_injection_context(user_id, query, days)


async def retrieve_memories(
    user_id: str,
    query: str,
    days: int = 7,
    subject: str | None = None,
    topic: str | None = None,
) -> dict[str, Any]:
    """便捷函数：检索记忆"""
    agent = RetrievalAgent()
    return await agent.process(user_id, query, days, subject, topic)

"""
Profile Agent
=============

用户画像 Agent - 隐式学习用户偏好并更新画像
"""

import json
from typing import Any

from src.agents.base_agent import BaseAgent
from src.logging import get_logger
from src.services.memory.database import get_db_session, get_or_create_profile
from src.services.memory.crud import update_profile_preferences

logger = get_logger("ProfileAgent")


class ProfileAgent(BaseAgent):
    """
    用户画像 Agent

    功能：
    1. 隐式地学习用户的学习偏好
    2. 更新用户画像
    3. 统计学习数据
    """

    def __init__(self, **kwargs):
        super().__init__(
            module_name="memory",
            agent_name="profile_agent",
            **kwargs
        )

    async def process(
        self,
        user_id: str,
        messages: list[dict[str, str]],
        update_statistics: bool = True
    ) -> dict[str, Any]:
        """
        处理用户画像更新请求

        Args:
            user_id: 用户 ID
            messages: 对话消息列表
            update_statistics: 是否更新统计数据

        Returns:
            处理结果字典
        """
        # 从对话中推断偏好
        preferences = await self._infer_preferences(messages)

        # 更新用户画像
        with get_db_session() as session:
            profile, created = get_or_create_profile(session, user_id)

            # 合并偏好（置信度高的覆盖）
            if preferences.get("confidence", 0) > 0.5:
                update_profile_preferences(session, user_id, preferences)

            # 返回更新后的画像
            profile_dict = profile.to_dict()

        return {
            "success": True,
            "profile": profile_dict,
            "inferred_preferences": preferences,
            "created": created,
        }

    async def _infer_preferences(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """从对话中推断用户偏好"""
        if not messages:
            return {}

        # 格式化消息
        messages_text = self._format_messages_for_inference(messages)

        # 获取提示词
        system_prompt = self.get_prompt("system")
        user_prompt = self.get_prompt("user", fallback="分析用户偏好。")

        # 使用字符串替换避免 JSON 中的 {} 被误解析
        try:
            user_prompt = user_prompt.replace("{messages}", str(messages_text[-3000:]))
        except Exception:
            user_prompt = f"{user_prompt}\\n\\n对话内容:\\n{messages_text[-3000:]}"

        try:
            # 调用 LLM
            response = await self.call_llm(
                user_prompt=user_prompt,
                system_prompt=system_prompt,
                response_format={"type": "json_object"},
                stage="infer_preferences"
            )

            # 解析响应
            preferences = json.loads(response)
            return preferences

        except Exception as e:
            self.logger.error(f"Failed to infer preferences: {e}")
            # 返回默认值
            return {}

    def _format_messages_for_inference(self, messages: list[dict[str, str]]) -> str:
        """格式化消息用于偏好推断"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if content:
                formatted.append(f"[{role.upper()}]: {content}")
        return "\n\n".join(formatted)

    async def get_profile(self, user_id: str) -> dict[str, Any]:
        """获取用户画像"""
        with get_db_session() as session:
            profile, _ = get_or_create_profile(session, user_id)
            return profile.to_dict()

    async def update_preferences(
        self,
        user_id: str,
        preferences: dict[str, Any]
    ) -> dict[str, Any]:
        """显式更新用户偏好"""
        with get_db_session() as session:
            profile = update_profile_preferences(session, user_id, preferences)
            return profile.to_dict() if profile else {}


# 便捷函数
async def get_user_profile(user_id: str) -> dict[str, Any]:
    """便捷函数：获取用户画像"""
    agent = ProfileAgent()
    return await agent.get_profile(user_id)


async def update_user_preferences(
    user_id: str,
    preferences: dict[str, Any]
) -> dict[str, Any]:
    """便捷函数：更新用户偏好"""
    agent = ProfileAgent()
    return await agent.update_preferences(user_id, preferences)

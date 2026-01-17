"""
Summarizer Agent
================

会话摘要 Agent - 自动压缩长对话，生成结构化摘要
"""

import json
from typing import Any

from src.agents.base_agent import BaseAgent
from src.logging import get_logger
from src.services.memory.database import get_db_session
from src.services.memory.crud import (
    create_session_summary,
    get_session_summary,
    update_profile_preferences,
    update_knowledge_graph,
    update_weak_points,
    increment_profile_statistics,
)
from src.services.memory.schemas import SessionSummaryCreate
from src.services.memory.config import get_config

logger = get_logger("SummarizerAgent")


class SummarizerAgent(BaseAgent):
    """
    会话摘要 Agent

    功能：
    1. 分析长对话，提取关键信息
    2. 生成结构化摘要（JSON 格式）
    3. 识别用户的学习偏好
    4. 识别薄弱知识点
    5. 保存到数据库
    """

    def __init__(self, **kwargs):
        super().__init__(
            module_name="memory",
            agent_name="summarizer_agent",
            **kwargs
        )
        self.config = get_config()

    async def process(
        self,
        session_id: str,
        user_id: str,
        messages: list[dict[str, str]],
        force: bool = False
    ) -> dict[str, Any]:
        """
        处理会话摘要请求

        Args:
            session_id: 会话 ID
            user_id: 用户 ID
            messages: 对话消息列表
            force: 是否强制生成摘要

        Returns:
            处理结果字典
        """
        # 检查是否需要生成摘要
        should_summarize = self._should_trigger_summary(messages, force)

        if not should_summarize:
            return {
                "success": True,
                "should_summarize": False,
                "message": "摘要生成条件未满足",
            }

        # 生成摘要
        summary_data = await self._generate_summary(session_id, user_id, messages)

        # 保存到数据库
        with get_db_session() as session:
            # 检查是否已存在摘要
            existing = get_session_summary(session, session_id)

            if existing:
                # 更新现有摘要
                from src.services.memory.crud import update_session_summary
                from src.services.memory.schemas import SessionSummaryUpdate

                update_data = SessionSummaryUpdate(
                    core_topic=summary_data["core_topic"],
                    key_points=summary_data["key_points"],
                    resolved_questions=summary_data["resolved_questions"],
                    unresolved_questions=summary_data["unresolved_questions"],
                    weak_points=summary_data["weak_points"],
                )
                updated = update_session_summary(session, session_id, update_data)
                summary_id = updated.id if updated else existing.id
            else:
                # 创建新摘要
                create_data = SessionSummaryCreate(
                    session_id=session_id,
                    user_id=user_id,
                    **summary_data
                )
                created = create_session_summary(session, create_data)
                summary_id = created.id

            # 更新用户画像
            await self._update_user_profile(
                session,
                user_id,
                summary_data
            )

        return {
            "success": True,
            "should_summarize": True,
            "summary_id": summary_id,
            "message": "摘要已生成",
            "summary": summary_data,
        }

    def _should_trigger_summary(
        self,
        messages: list[dict[str, str]],
        force: bool = False
    ) -> bool:
        """检查是否应该触发摘要生成"""
        if force:
            return True

        # 检查消息数量
        message_count = len(messages)
        trigger_rounds = self.config.summary.summary_trigger_rounds

        if message_count >= trigger_rounds * 2:  # 每轮包含 user + assistant
            return True

        # 检查 token 数量（简单估算）
        total_chars = sum(len(m.get("content", "")) for m in messages)
        estimated_tokens = total_chars // 2  # 粗略估算
        trigger_tokens = self.config.summary.summary_trigger_tokens

        if estimated_tokens >= trigger_tokens:
            return True

        return False

    async def _generate_summary(
        self,
        session_id: str,
        user_id: str,
        messages: list[dict[str, str]]
    ) -> dict[str, Any]:
        """生成会话摘要"""
        # 格式化消息为文本
        messages_text = self._format_messages(messages)

        # 获取提示词
        system_prompt = self.get_prompt("system")
        user_prompt = self.get_prompt("user", fallback="分析以下对话并生成JSON摘要：\\n\\n{messages}")

        # 使用模板替换（避免 JSON 中的 {} 被误解析）
        try:
            user_prompt = user_prompt.replace("{messages}", str(messages_text[-5000:]))
        except Exception:
            # 如果替换失败，直接追加消息
            user_prompt = f"{user_prompt}\\n\\n{messages_text[-5000:]}"

        # 调用 LLM
        response = await self.call_llm(
            user_prompt=user_prompt,
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
            stage="summarize"
        )

        # 解析 JSON 响应
        try:
            summary = json.loads(response)

            # 保留最近的消息
            keep_recent = self.config.summary.summary_keep_recent
            summary["recent_messages"] = messages[-keep_recent:] if len(messages) > keep_recent else messages
            summary["message_count"] = len(messages)

            return summary

        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse summary JSON: {e}")
            # 返回默认摘要
            return self._get_default_summary(messages)

    def _format_messages(self, messages: list[dict[str, str]]) -> str:
        """格式化消息为文本"""
        formatted = []
        for i, msg in enumerate(messages):
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            formatted.append(f"{i+1}. [{role.upper()}]: {content}")
        return "\n".join(formatted)

    def _get_default_summary(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """获取默认摘要（当 LLM 失败时）"""
        # 从最后几条消息中推断主题
        recent_content = " ".join(m.get("content", "") for m in messages[-3:])

        return {
            "core_topic": "学习对话",
            "key_points": [
                "讨论了相关概念",
                "进行了一些问题解答",
            ],
            "resolved_questions": [],
            "unresolved_questions": [],
            "user_preferences": {
                "learning_style": "textual",
                "difficulty_preference": "intermediate",
                "include_code": True,
                "include_math": True,
            },
            "weak_points": [],
            "subject": None,
            "topic": None,
            "difficulty": None,
            "recent_messages": messages[-5:] if len(messages) > 5 else messages,
            "message_count": len(messages),
            "token_count": 0,
        }

    async def _update_user_profile(
        self,
        session,
        user_id: str,
        summary: dict[str, Any]
    ) -> None:
        """更新用户画像"""
        # 更新偏好
        if "user_preferences" in summary:
            update_profile_preferences(session, user_id, summary["user_preferences"])

        # 更新薄弱点
        if "weak_points" in summary and summary["weak_points"]:
            weak_points = [
                {
                    **wp,
                    "last_confused": summary.get("created_at") or summary.get("generated_at"),
                    "subject": wp.get("subject") or summary.get("subject"),
                    "topic": wp.get("topic") or summary.get("topic"),
                }
                for wp in summary["weak_points"]
            ]
            update_weak_points(session, user_id, weak_points)

        # 更新统计数据
        # Calculate resolved questions count
        resolved_count = len(summary.get("resolved_questions", []))
        unresolved_count = len(summary.get("unresolved_questions", []))
        total_questions = resolved_count + unresolved_count

        increment_profile_statistics(
            session,
            user_id,
            increment_sessions=True,
            increment_questions=(total_questions > 0),
            increment_active_days=True,  # Each summary represents a day of activity
            session_length=summary.get("message_count", 0),  # Use actual message count
        )

        # 更新知识图谱（从关键知识点中推断）
        if "key_points" in summary:
            for point in summary["key_points"]:
                # 提取概念（简单处理，取前几个词作为概念）
                concept = point.split()[0:5]
                concept = " ".join(concept) if isinstance(concept, list) else str(concept)

                update_knowledge_graph(
                    session,
                    user_id,
                    concept=concept[:50],  # 限制长度
                    mastery_delta=0.1,  # 学习了，增加掌握度
                    subject=summary.get("subject"),
                    topic=summary.get("topic"),
                    difficulty=summary.get("difficulty"),
                )


# 便捷函数
async def summarize_session(
    session_id: str,
    user_id: str,
    messages: list[dict[str, str]],
    force: bool = False
) -> dict[str, Any]:
    """
    便捷函数：生成会话摘要

    Args:
        session_id: 会话 ID
        user_id: 用户 ID
        messages: 对话消息列表
        force: 是否强制生成

    Returns:
        处理结果
    """
    agent = SummarizerAgent()
    return await agent.process(session_id, user_id, messages, force)

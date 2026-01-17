"""
Memory System Services
======================

记忆系统的核心服务模块。

Modules:
    - config: 配置管理
    - embedding: Embedding 服务
    - database: 数据库连接（待实现）
    - retrieval: 检索服务（待实现）
"""

from .config import get_config, MemorySystemConfig
from .embedding import get_embedding_service, EmbeddingService

__all__ = [
    "get_config",
    "MemorySystemConfig",
    "get_embedding_service",
    "EmbeddingService",
]

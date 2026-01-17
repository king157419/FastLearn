"""
Memory System Configuration
===========================

配置管理类，用于加载环境变量和配置文件。
"""

import os
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseConfig(BaseSettings):
    """数据库配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 数据库连接
    database_url: str = "postgresql://deeptutor:deeptutor_password@localhost:5433/deeptutor_memory"
    postgres_host: str = "localhost"
    postgres_port: int = 5433
    postgres_user: str = "deeptutor"
    postgres_password: str = "deeptutor_password"
    postgres_db: str = "deeptutor_memory"

    # 连接池
    db_pool_size: int = 20
    db_max_overflow: int = 10
    db_pool_timeout: int = 30
    db_pool_recycle: int = 3600

    @property
    def sqlalchemy_url(self) -> str:
        """SQLAlchemy 连接 URL"""
        return self.database_url


class EmbeddingConfig(BaseSettings):
    """Embedding 模型配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Embedding 提供商
    embedding_provider: Literal["openai", "deepseek", "jina"] = "openai"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    # OpenAI
    openai_api_key: str = ""
    openai_embedding_base_url: str = "https://api.openai.com/v1"

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Jina
    jina_api_key: str = ""


class VectorIndexConfig(BaseSettings):
    """向量索引配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 索引类型
    vector_index_type: Literal["ivfflat", "hnsw"] = "ivfflat"

    # IVFFlat 参数
    ivfflat_lists: int = 100

    # HNSW 参数
    hnsw_m: int = 16
    hnsw_ef_construction: int = 64


class SummaryConfig(BaseSettings):
    """摘要 Agent 配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 触发条件
    summary_trigger_rounds: int = 10
    summary_trigger_tokens: int = 4000

    # 保留消息数
    summary_keep_recent: int = 5


class RetrievalConfig(BaseSettings):
    """检索配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Top-K
    memory_retrieval_top_k: int = 10
    semantic_retrieval_top_k: int = 10
    hybrid_retrieval_top_k: int = 7

    # 时间过滤
    memory_time_filter_days: int = 7

    # 重排序权重
    rerank_keyword_weight: float = 0.4
    rerank_semantic_weight: float = 0.4
    rerank_profile_weight: float = 0.2


class CacheConfig(BaseSettings):
    """缓存配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    cache_ttl: int = 3600


class LoggingConfig(BaseSettings):
    """日志配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    log_level: str = "INFO"
    log_file: str = "logs/memory_system.log"

    @property
    def log_level_int(self) -> int:
        """转换为整数日志级别"""
        levels = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40}
        return levels.get(self.log_level.upper(), 20)


class MemorySystemConfig(BaseSettings):
    """内存系统总配置"""

    model_config = SettingsConfigDict(
        env_file=".env.memory",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # 环境标识
    environment: Literal["development", "production"] = "development"

    # API 配置
    api_host: str = "0.0.0.0"
    api_port: int = 8001
    api_workers: int = 4

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    # 子配置
    database: DatabaseConfig = DatabaseConfig()
    embedding: EmbeddingConfig = EmbeddingConfig()
    vector_index: VectorIndexConfig = VectorIndexConfig()
    summary: SummaryConfig = SummaryConfig()
    retrieval: RetrievalConfig = RetrievalConfig()
    cache: CacheConfig = CacheConfig()
    logging: LoggingConfig = LoggingConfig()

    @property
    def cors_origins_list(self) -> list[str]:
        """CORS 允许的源列表"""
        return [origin.strip() for origin in self.cors_origins.split(",")]


# 全局配置实例
_config: MemorySystemConfig | None = None


def get_config() -> MemorySystemConfig:
    """获取配置实例（单例模式）"""
    global _config
    if _config is None:
        _config = MemorySystemConfig()
    return _config


# 测试
if __name__ == "__main__":
    config = get_config()
    print("=" * 50)
    print("DeepTutor Memory System Configuration")
    print("=" * 50)
    print(f"Environment: {config.environment}")
    print(f"Database URL: {config.database.database_url}")
    print(f"Embedding Provider: {config.embedding.embedding_provider}")
    print(f"Embedding Model: {config.embedding.embedding_model}")
    print(f"Embedding Dimensions: {config.embedding.embedding_dimensions}")
    print(f"Vector Index Type: {config.vector_index.vector_index_type}")
    print(f"Summary Trigger Rounds: {config.summary.summary_trigger_rounds}")
    print(f"Retrieval Top-K: {config.retrieval.hybrid_retrieval_top_k}")
    print("=" * 50)

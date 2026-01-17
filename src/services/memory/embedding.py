"""
Embedding Service
=================

统一的 Embedding 服务，支持多个提供商：
- OpenAI (text-embedding-3-small/large)
- DeepSeek (deepseek-embeddings)
- Jina (jina-embeddings-v2)
"""

from typing import Literal
import numpy as np
from src.logging import get_logger
from src.services.memory.config import get_config, EmbeddingConfig

logger = get_logger("EmbeddingService")


class EmbeddingService:
    """统一的 Embedding 服务"""

    def __init__(self, config: EmbeddingConfig | None = None):
        """
        初始化 Embedding 服务

        Args:
            config: Embedding 配置，如果为 None 则从环境变量加载
        """
        self.config = config or get_config().embedding
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """初始化对应提供商的客户端"""
        provider = self.config.embedding_provider

        if provider == "openai":
            self._init_openai()
        elif provider == "deepseek":
            self._init_deepseek()
        elif provider == "jina":
            self._init_jina()
        else:
            raise ValueError(f"Unsupported embedding provider: {provider}")

        logger.info(
            f"Initialized {provider} embedding service",
            extra={
                "provider": provider,
                "model": self.config.embedding_model,
                "dimensions": self.config.embedding_dimensions
            }
        )

    def _init_openai(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.config.openai_api_key,
                base_url=self.config.openai_embedding_base_url
            )
            self._embed_func = self._embed_openai
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Install it with: pip install openai"
            )

    def _init_deepseek(self):
        """初始化 DeepSeek 客户端"""
        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.config.deepseek_api_key,
                base_url=self.config.deepseek_base_url
            )
            self._embed_func = self._embed_openai  # DeepSeek 使用 OpenAI 兼容 API
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Install it with: pip install openai"
            )

    def _init_jina(self):
        """初始化 Jina 客户端"""
        try:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.config.jina_api_key,
                base_url="https://api.jina.ai/v1"
            )
            self._embed_func = self._embed_openai  # Jina 使用 OpenAI 兼容 API
        except ImportError:
            raise ImportError(
                "OpenAI package not installed. "
                "Install it with: pip install openai"
            )

    def _embed_openai(self, text: str) -> list[float]:
        """
        使用 OpenAI 兼容 API 生成嵌入

        Args:
            text: 输入文本

        Returns:
            向量嵌入（list of floats）
        """
        response = self._client.embeddings.create(
            model=self.config.embedding_model,
            input=text
        )

        embedding = response.data[0].embedding
        return embedding

    async def embed(self, text: str) -> list[float]:
        """
        生成单个文本的嵌入向量（异步）

        Args:
            text: 输入文本

        Returns:
            向量嵌入（list of floats，维度 = embedding_dimensions）
        """
        try:
            embedding = self._embed_func(text)

            # 验证维度
            if len(embedding) != self.config.embedding_dimensions:
                logger.warning(
                    f"Embedding dimension mismatch: expected {self.config.embedding_dimensions}, "
                    f"got {len(embedding)}"
                )

            return embedding

        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise

    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """
        批量生成嵌入向量（异步）

        Args:
            texts: 输入文本列表

        Returns:
            嵌入向量列表
        """
        embeddings = []

        for text in texts:
            embedding = await self.embed(text)
            embeddings.append(embedding)

        return embeddings

    def embed_sync(self, text: str) -> list[float]:
        """
        生成单个文本的嵌入向量（同步）

        Args:
            text: 输入文本

        Returns:
            向量嵌入
        """
        import asyncio

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # 没有运行中的事件循环，可以安全地运行同步代码
            return asyncio.run(self.embed(text))
        else:
            # 有运行中的事件循环，不能使用 asyncio.run
            raise RuntimeError(
                "Cannot call embed_sync from within an async context. "
                "Use await embed(...) instead."
            )

    async def compute_similarity(
        self,
        text1: str,
        text2: str
    ) -> float:
        """
        计算两个文本的余弦相似度

        Args:
            text1: 文本1
            text2: 文本2

        Returns:
            相似度（0-1，1表示完全相同）
        """
        # 生成嵌入
        embedding1 = await self.embed(text1)
        embedding2 = await self.embed(text2)

        # 计算余弦相似度
        similarity = self._cosine_similarity(embedding1, embedding2)

        return similarity

    def _cosine_similarity(
        self,
        vec1: list[float],
        vec2: list[float]
    ) -> float:
        """
        计算余弦相似度

        Args:
            vec1: 向量1
            vec2: 向量2

        Returns:
            相似度（0-1）
        """
        # 转为 numpy 数组
        a = np.array(vec1)
        b = np.array(vec2)

        # 计算点积
        dot_product = np.dot(a, b)

        # 计算模
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)

        # 余弦相似度
        similarity = dot_product / (norm_a * norm_b)

        return float(similarity)


# 全局单例
_embedding_service: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """
    获取 Embedding 服务实例（单例模式）

    Returns:
        EmbeddingService 实例
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


# 测试
if __name__ == "__main__":
    import asyncio

    async def test():
        service = get_embedding_service()

        # 测试单个嵌入
        text = "深度学习是人工智能的一个分支"
        embedding = await service.embed(text)
        print(f"Embedding dimensions: {len(embedding)}")
        print(f"First 5 values: {embedding[:5]}")

        # 测试相似度
        text1 = "机器学习是人工智能的一个分支"
        text2 = "深度学习是机器学习的一个分支"
        similarity = await service.compute_similarity(text1, text2)
        print(f"Similarity: {similarity:.3f}")

    asyncio.run(test())

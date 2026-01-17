"""
Memory Embedding Model
======================

向量嵌入的 SQLAlchemy ORM 模型
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, TIMESTAMP, JSON, ForeignKey, BigInteger
from sqlalchemy.orm import relationship
from src.services.memory.database import Base


class MemoryEmbedding(Base):
    """向量嵌入表 ORM 模型"""

    __tablename__ = "memory_embeddings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    memory_id = Column(Integer, nullable=False)
    user_id = Column(String(64), nullable=False)
    session_id = Column(String(64))

    # 向量嵌入 (存储为字符串，实际使用时转换为向量)
    embedding_str = Column(String(8192), nullable=False)

    # 元数据 (meta_data 避免与 SQLAlchemy 保留名冲突)
    meta_data = Column("metadata", JSON, default=dict)

    # 时间戳
    created_at = Column(TIMESTAMP, default=datetime.utcnow)
    updated_at = Column(TIMESTAMP, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def embedding(self) -> list[float]:
        """获取向量嵌入列表"""
        if self.embedding_str:
            return [float(x) for x in self.embedding_str.split(",")]
        return []

    @embedding.setter
    def embedding(self, value: list[float]):
        """设置向量嵌入"""
        self.embedding_str = ",".join(str(x) for x in value)

    def __repr__(self):
        return f"<MemoryEmbedding(id={self.id}, user_id='{self.user_id}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "id": self.id,
            "memory_id": self.memory_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "embedding": self.embedding,
            "metadata": self.meta_data,  # 暴露为 metadata
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

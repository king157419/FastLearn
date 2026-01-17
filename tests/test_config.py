"""
测试数据库连接
"""
import sys
sys.path.insert(0, 'D:/DeepTutor')

from src.services.memory.config import get_config

try:
    config = get_config()
    print("=" * 60)
    print("✅ 配置加载成功！")
    print("=" * 60)
    print(f"数据库地址: {config.database.postgres_host}:{config.database.postgres_port}")
    print(f"数据库名称: {config.database.postgres_db}")
    print(f"Embedding 提供商: {config.config.embedding_provider}")
    print(f"环境: {config.environment}")
    print("=" * 60)
    print("\n⚠️  请在 .env.memory 文件中填写以下 API Keys：")
    print("  1. OPENAI_API_KEY 或 DEEPSEEK_API_KEY（Embedding）")
    print("  2. DEEPSEEK_API_KEY 或 OPENAI_API_KEY（LLM）")
    print("\n📝 编辑命令:")
    print("  notepad D:\\DeepTutor\\.env.memory")
    print("\n填写后，可以运行完整测试:")
    print("  python tests/test_memory_system.py")
except Exception as e:
    print(f"❌ 配置加载失败: {e}")
    sys.exit(1)

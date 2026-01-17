# DeepTutor Memory System - 快速启动指南

## 📋 目录

1. [环境准备](#环境准备)
2. [启动向量数据库](#启动向量数据库)
3. [配置 Embedding 模型](#配置-embedding-模型)
4. [验证配置](#验证配置)
5. [下一步](#下一步)

---

## 环境准备

### 前置要求

- Docker & Docker Compose（推荐）
- 或者 PostgreSQL 16+ 本地安装
- Python 3.10+

### 可选项

- Redis（缓存，可选）
- pgAdmin（数据库管理工具，可选）

---

## 启动向​​量数据库

### 方式 1: Docker Compose（推荐）⭐

#### 步骤 1: 启动容器

```bash
# 进入 DeepTutor 目录
cd D:/DeepTutor

# 使用 pgvector 配置启动
docker-compose -f docker-compose.pgvector.yml up -d

# 查看日志
docker-compose -f docker-compose.pgvector.yml logs -f postgres
```

#### 步骤 2: 等待数据库就绪

```bash
# 等待看到以下日志：
# PostgreSQL init process complete; ready for start up.
# database system is ready to accept connections
```

#### 步骤 3: 执行数据库迁移

```bash
# 进入 PostgreSQL 容器
docker exec -it deeptutor-memory-db psql -U deeptutor -d deeptutor_memory

# 或者从主机执行迁移脚本
docker exec -i deeptutor-memory-db psql -U deeptutor -d deeptutor_memory < migrations/001_create_memory_system_tables.sql
```

#### 步骤 4: 验证安装

```bash
# 连接到数据库
docker exec -it deeptutor-memory-db psql -U deeptutor -d deeptutor_memory

# 检查 pgvector 扩展
\dx

# 应该看到：
# name    | version |   schema   |           description
# ----------+---------+------------+-----------------------------------------------
-- plpgsql   | 1.0     | pg_catalog | PL/pgSQL procedural language
-- vector    | 0.5.0   | public     | vector data type and ivfflat/hnsw access methods

# 检查表
\dt

# 应该看到：
-- public | memory_embeddings        | table | postgres
-- public | session_summaries        | table | postgres
-- public | user_profiles            | table | postgres

# 退出
\q
```

#### 步骤 5: 访问 pgAdmin（可选）

浏览器打开：http://localhost:5050

- Email: `admin@deeptutor.ai`
- Password: `pgadmin_password`

---

### 方式 2: 本地安装 PostgreSQL

#### 步骤 1: 安装 PostgreSQL 16

**Windows**:
```bash
# 下载安装器
https://www.postgresql.org/download/windows/

# 安装时记住密码
```

**macOS**:
```bash
brew install postgresql@16
brew services start postgresql@16
```

**Linux**:
```bash
sudo apt update
sudo apt install postgresql-16 postgresql-contrib-16
sudo systemctl start postgresql
```

#### 步骤 2: 安装 pgvector 扩展

**从源码编译**（推荐）:

```bash
# 克隆仓库
git clone --branch v0.5.0 https://github.com/pgvector/pgvector.git
cd pgvector

# 编译安装
export PATH=/usr/local/pgsql/bin:$PATH
make
make install # 可能需要 sudo

# 验证安装
pg_config --version
```

#### 步骤 3: 创建数据库和扩展

```bash
# 创建用户
createuser deeptutor -P

# 创建数据库
createdb deeptutor_memory -O deeptutor

# 连接到数据库
psql -U deeptutor -d deeptutor_memory

# 启用 pgvector 扩展
CREATE EXTENSION vector;

# 退出
\q
```

#### 步骤 4: 执行迁移脚本

```bash
psql -U deeptutor -d deeptutor_memory -f migrations/001_create_memory_system_tables.sql
```

---

## 配置 Embedding 模型

### 选项 1: OpenAI Embeddings（推荐）⭐

#### 优点
- 质量最好
- 中文支持好
- 稳定可靠

#### 配置

```bash
# 复制环境配置文件
cp .env.memory.example .env.memory

# 编辑 .env.memory
EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_DIMENSIONS=1536
OPENAI_API_KEY=sk-your-key-here
```

#### 成本
- $0.02 / 1M tokens
- 非常便宜

---

### 选项 2: DeepSeek Embeddings（中文优化）

#### 优点
- 成本极低
- 中文优化
- 速度快

#### 配置

```bash
EMBEDDING_PROVIDER=deepseek
EMBEDDING_MODEL=deepseek-embeddings
EMBEDDING_DIMENSIONS=1024
DEEPSEEK_API_KEY=sk-your-key-here
```

#### 成本
- 约 $0.001 / 1M tokens
- 比OpenAI便宜20倍

---

### 选项 3: Jina Embeddings（开源）

#### 优点
- 开源免费
- 可本地部署
- 隐私保护

#### 配置

```bash
EMBEDDING_PROVIDER=jina
EMBEDDING_MODEL=jina-embeddings-v2
EMBEDDING_DIMENSIONS=768
JINA_API_KEY=your-key-here
```

---

## 验证配置

### 测试数据库连接

```bash
# Python 测试脚本
python -c "
from src.services.memory.config import get_config
config = get_config()
print('Database URL:', config.database.database_url)
print('Test connection...')
"
```

### 测试 pgvector 扩展

```python
# 测试向量搜索
import psycopg2
from src.services.memory.config import get_config

config = get_config()

# 连接数据库
conn = psycopg2.connect(config.database.database_url)
cur = conn.cursor()

# 测试向量操作
cur.execute("""
    SELECT 1::vector
""")

result = cur.fetchone()
print('Vector test:', result)

conn.close()
```

### 测试 Embedding 模型

```python
# 测试 OpenAI Embeddings
from openai import OpenAI
from src.services.memory.config import get_config

config = get_config()
client = OpenAI(api_key=config.embedding.openai_api_key)

# 测试嵌入
response = client.embeddings.create(
    model=config.embedding.embedding_model,
    input="测试文本"
)

embedding = response.data[0].embedding
print(f"Embedding dimensions: {len(embedding)}")
print(f"First 5 values: {embedding[:5]}")
```

---

## Memory System API 使用

### 用户画像 API

```python
# 获取用户画像
GET /api/memory/profiles/{user_id}

# 更新用户偏好
PATCH /api/memory/profiles/{user_id}/preferences
{
  "learning_style": "code_first",
  "difficulty_preference": "intermediate"
}
```

### 会话摘要 API

```python
# 获取会话摘要
GET /api/memory/sessions/{session_id}/summary

# 触发摘要生成
POST /api/memory/sessions/{session_id}/summarize
{
  "user_id": "user_123",
  "messages": [...],
  "force": false
}

# 获取用户会话列表
GET /api/memory/sessions/{user_id}/list?days=7&limit=10
```

### 记忆检索 API

```python
# 获取上下文（用于新对话）
GET /api/memory/context?user_id={user_id}&query={query}&days=7

# 搜索记忆
POST /api/memory/search
{
  "user_id": "user_123",
  "query": "梯度下降",
  "days": 7
}
```

### Python 代码示例

```python
from src.agents.memory import (
    summarize_session,
    get_user_profile,
    update_user_preferences,
    get_memory_context
)

# 生成会话摘要
result = await summarize_session(
    session_id="sess_123",
    user_id="user_001",
    messages=[
        {"role": "user", "content": "什么是梯度下降？"},
        {"role": "assistant", "content": "梯度下降是..."},
    ],
    force=True
)

# 获取用户画像
profile = await get_user_profile("user_001")

# 更新用户偏好
await update_user_preferences(
    user_id="user_001",
    preferences={"learning_style": "code_first"}
)

# 获取记忆上下文
context = await get_memory_context(
    user_id="user_001",
    query="Adam 优化器",
    days=7
)
```

---

## 进度更新

### ✅ 已完成
- [x] 数据库 Schema 设计
- [x] 向量数据库配置
- [x] Embedding 模型配置
- [x] 数据模型（UserProfile, SessionSummary, MemoryEmbedding）
- [x] CRUD 操作
- [x] SummarizerAgent
- [x] ProfileAgent
- [x] RetrievalAgent
- [x] API 路由

### 📋 待办
- [ ] 前端偏好设置页面
- [ ] 集成到 Chat/Solve/Guide 模块
- [ ] 端到端测试
- [ ] 向量检索优化（Phase 2）

---

## 🆘 故障排除

### 问题 1: Docker 容器无法启动

```bash
# 检查端口占用
netstat -ano | findstr :5433

# 如果被占用，修改 docker-compose.pgvector.yml 中的端口映射
ports:
  - "5434:5432"  # 改成其他端口
```

### 问题 2: pgvector 扩展未安装

```bash
# 检查扩展
\dx

# 如果没有 vector，手动安装
CREATE EXTENSION vector;
```

### 问题 3: 无法连接数据库

```bash
# 检查容器状态
docker ps | grep deeptutor

# 查看日志
docker logs deeptutor-memory-db

# 重启容器
docker-compose -f docker-compose.pgvector.yml restart
```

---

## 📚 参考资料

- [pgvector GitHub](https://github.com/pgvector/pgvector)
- [OpenAI Embeddings](https://platform.openai.com/docs/guides/embeddings)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

**准备好后，继续执行 Phase 1.3！** 🚀

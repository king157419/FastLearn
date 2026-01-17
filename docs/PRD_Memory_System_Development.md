# DeepTutor 智能记忆系统 PRD（开发版）

> **项目代号**: Memory-X
> **版本**: v1.0-MVP
> **创建日期**: 2026-01-17
> **目标**: 2 周 MVP，核心功能上线

---

## 📋 目录

1. [项目概述](#项目概述)
2. [核心功能列表](#核心功能列表)
3. [用户故事](#用户故事)
4. [技术架构](#技术架构)
5. [数据模型](#数据模型)
6. [API 设计](#api-设计)
7. [开发任务清单](#开发任务清单)

---

## 项目概述

### 目标

**为 DeepTutor 添加跨会话的智能记忆系统，让 AI 能够记住用户的学习历程。**

### MVP 范围（2 周）

**包含**：
- ✅ 会话自动摘要
- ✅ 用户画像存储
- ✅ 跨会话上下文注入
- ✅ 基础 API 接口

**不包含**（后续版本）：
- ❌ 薄弱知识点追踪（Phase 2）
- ❌ 向量检索（Phase 2）
- ❌ 学习路径生成（Phase 3）

---

## 核心功能列表

### 功能 1：会话摘要系统

**优先级**: P0（必须有）

**描述**：每 10 轮对话或 4000 tokens 时，自动压缩历史消息为摘要。

**输入**：
```python
messages = [
    {"role": "user", "content": "问题1"},
    {"role": "assistant", "content": "答案1"},
    # ... 50 轮对话
]
```

**输出**：
```python
summary = {
    "core_topic": "深度学习优化算法",
    "key_points": [
        "梯度下降是基础优化器",
        "SGD 是随机梯度下降",
        "Adam 结合了动量和自适应学习率"
    ],
    "resolved_questions": [
        "什么是梯度",
        "SGD 和 GD 的区别"
    ],
    "unresolved_questions": [
        "Adam 和 SGD 的具体区别"
    ],
    "user_preferences": {
        "style": "代码优先",
        "difficulty": "中等深度"
    }
}

recent_messages = messages[-5:]  # 保留最近 5 条
```

**价值**：
- Token 节省 40%
- 响应速度提升
- 保留关键信息

---

### 功能 2：用户画像存储

**优先级**: P0（必须有）

**描述**：记录用户的学习偏好和基本统计。

**数据结构**：
```python
user_profile = {
    "user_id": "user_123",
    "preferences": {
        "learning_style": "visual",  # visual | textual | hands_on
        "difficulty_level": "intermediate",
        "language": "zh-CN",
        "include_code": True,
        "include_math": True
    },
    "statistics": {
        "total_sessions": 42,
        "total_questions": 156,
        "active_days": 15
    },
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-17T10:30:00Z"
}
```

**API**：
- `GET /api/memory/profile/{user_id}` - 获取画像
- `PATCH /api/memory/profile/{user_id}/preferences` - 更新偏好

---

### 功能 3：跨会话上下文注入

**优先级**: P0（必须有）

**描述**：新对话开始时，自动注入相关历史信息。

**工作流程**：
```python
# 1. 用户发起新对话
user_input = "Adam 优化器怎么用？"

# 2. 检索用户画像
profile = get_user_profile(user_id)

# 3. 检索相关历史（最近 7 天）
memories = search_recent_memories(user_id, days=7)

# 4. 构建上下文
context = f"""
## 用户画像
- 学习风格：{profile.learning_style}
- 难度偏好：{profile.difficulty_level}

## 相关学习历史（最近 7 天）
{format_memories(memories)}
"""

# 5. 注入到 System Prompt
system_prompt = f"""
你是一个 AI 学习助手。

{context}

请基于以上信息，为用户提供个性化的学习帮助。
"""
```

**效果**：
- 用户不需要重复解释背景
- 主动关联已学知识
- 个性化回复

---

### 功能 4：会话记忆 API

**优先级**: P0（必须有）

**描述**：提供 RESTful API 管理会话记忆。

**API 列表**：
```python
# 1. 获取会话摘要
GET /api/memory/sessions/{session_id}/summary
Response: {"summary": {...}, "recent_messages": [...]}

# 2. 手动触发摘要
POST /api/memory/sessions/{session_id}/summarize
Request: {"force": true}

# 3. 获取跨会话上下文
GET /api/memory/context?user_id={user_id}&query={query}
Response: {"context": "...", "source_memories": [...]}
```

---

## 用户故事

### Epic 1: 会话摘要

#### Story 1.1: 自动摘要触发

**As a** 用户
**I want** 系统自动压缩长对话
**So that** 我可以节省 Token 成本，同时保留关键信息

**验收标准**：
- [ ] 当对话达到 10 轮时，自动触发摘要
- [ ] 当对话达到 4000 tokens 时，自动触发摘要
- [ ] 摘要包含：核心主题、关键知识点、已解决问题、未解决问题
- [ ] 保留最近 5 条完整消息
- [ ] 摘要质量 BLEU > 0.7

---

#### Story 1.2: 手动触发摘要

**As a** 用户
**I want** 手动触发对话摘要
**So that** 我可以在任何时候保存关键信息

**验收标准**：
- [ ] 提供 "生成摘要" 按钮
- [ ] 点击后立即生成摘要
- [ ] 显示摘要内容预览
- [ ] 允许用户编辑摘要

---

### Epic 2: 用户画像

#### Story 2.1: 设置学习偏好

**As a** 用户
**I want** 设置我的学习偏好
**So that** 系统能提供更符合我习惯的解释方式

**验收标准**：
- [ ] 提供偏好设置页面
- [ ] 可设置：学习风格、难度、语言、是否包含代码/数学
- [ ] 保存后立即生效
- [ ] 后续对话自动应用偏好

---

#### Story 2.2: 查看学习统计

**As a** 用户
**I want** 查看我的学习统计
**So that** 我能了解自己的学习进度

**验收标准**：
- [ ] 显示：总对话次数、总问题数、活跃天数
- [ ] 数据实时更新
- [ ] 可视化展示（可选）

---

### Epic 3: 跨会话上下文

#### Story 3.1: 自动注入历史信息

**As a** 用户
**I want** 系统自动记住我之前的对话
**So that** 我不需要重复解释背景

**验收标准**：
- [ ] 新对话自动注入最近 7 天的相关历史
- [ ] 注入的信息包含：用户画像、相关对话、关键知识点
- [ ] 注入的信息不影响正常对话速度（< 500ms）

---

#### Story 3.2: 查看历史记忆

**As a** 用户
**I want** 查看我的历史学习记录
**So that** 我能回顾之前学过的内容

**验收标准**：
- [ ] 提供"历史记录"页面
- [ ] 按时间倒序展示
- [ ] 可按主题搜索
- [ ] 点击查看详情

---

## 技术架构

### 系统架构图

```
┌──────────────────────────────────────────┐
│          前端 (Next.js)                   │
│  学习进度面板、偏好设置、历史记录          │
└──────────────┬───────────────────────────┘
               │ HTTP/WebSocket
┌──────────────▼───────────────────────────┐
│          API 层 (FastAPI)                 │
│  /api/memory/*                           │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│       Agent 层 (新增)                     │
│  ┌──────────────┐  ┌──────────────┐      │
│  │SummarizerAgent│  │ProfileAgent │      │
│  └──────────────┘  └──────────────┘      │
└──────────────┬───────────────────────────┘
               │
┌──────────────▼───────────────────────────┐
│       存储层 (新增)                       │
│  ┌──────────┐  ┌──────────┐             │
│  │PostgreSQL│  │  JSON    │             │
│  │ (画像)   │  │ (摘要)   │             │
│  └──────────┘  └──────────┘             │
└──────────────────────────────────────────┘
```

---

### 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | Next.js 16 | 已有 |
| **后端** | FastAPI | 已有 |
| **Agent** | BaseAgent | 已有框架 |
| **数据库** | PostgreSQL | 新增（用户画像） |
| **存储** | JSON 文件 | 已有（会话摘要） |
| **LLM** | Qwen2.5-14B | 已有配置 |

---

## 数据模型

### 1. 用户画像表 (user_profiles)

```sql
CREATE TABLE user_profiles (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(64) UNIQUE NOT NULL,

    -- 偏好设置
    preferences JSONB NOT NULL,
    /*
    {
        "learning_style": "visual",
        "difficulty_level": "intermediate",
        "language": "zh-CN",
        "include_code": true,
        "include_math": true
    }
    */

    -- 统计数据
    statistics JSONB DEFAULT '{}',
    /*
    {
        "total_sessions": 0,
        "total_questions": 0,
        "active_days": 0
    }
    */

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 索引
    INDEX idx_user_id (user_id)
);
```

---

### 2. 会话摘要 (session_summaries)

```sql
CREATE TABLE session_summaries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(64) UNIQUE NOT NULL,
    user_id VARCHAR(64) NOT NULL,

    -- 摘要内容
    core_topic TEXT,
    key_points JSONB,  -- ["要点1", "要点2"]
    resolved_questions JSONB,
    unresolved_questions JSONB,
    user_preferences JSONB,

    -- 消息
    recent_messages JSONB,  -- 最近 5 条

    -- 元数据
    message_count INT DEFAULT 0,
    token_count INT DEFAULT 0,

    -- 时间戳
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- 索引
    INDEX idx_session_id (session_id),
    INDEX idx_user_id (user_id),
    INDEX idx_created_at (created_at)
);
```

---

### 3. 扩展现有会话表

```sql
-- 在现有 chat_sessions 基础上添加
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS summary_id VARCHAR(64);
ALTER TABLE chat_sessions ADD COLUMN IF NOT EXISTS has_summary BOOLEAN DEFAULT FALSE;
```

---

## API 设计

### 1. 会话摘要 API

#### 1.1 获取会话摘要

```http
GET /api/memory/sessions/{session_id}/summary
```

**Response**:
```json
{
  "summary_id": "sum_001",
  "session_id": "sess_123",
  "core_topic": "深度学习优化算法",
  "key_points": [
    "梯度下降是基础优化器",
    "SGD 是随机梯度下降",
    "Adam 结合了动量和自适应学习率"
  ],
  "resolved_questions": [
    "什么是梯度",
    "SGD 和 GD 的区别"
  ],
  "unresolved_questions": [
    "Adam 和 SGD 的具体区别"
  ],
  "user_preferences": {
    "style": "代码优先",
    "difficulty": "中等深度"
  },
  "recent_messages": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ],
  "created_at": "2025-01-17T10:30:00Z"
}
```

---

#### 1.2 手动触发摘要

```http
POST /api/memory/sessions/{session_id}/summarize
Content-Type: application/json

{
  "force": true  // 强制重新生成
}
```

**Response**:
```json
{
  "success": true,
  "summary_id": "sum_001",
  "message": "摘要已生成"
}
```

---

### 2. 用户画像 API

#### 2.1 获取用户画像

```http
GET /api/memory/profiles/{user_id}
```

**Response**:
```json
{
  "user_id": "user_123",
  "preferences": {
    "learning_style": "visual",
    "difficulty_level": "intermediate",
    "language": "zh-CN",
    "include_code": true,
    "include_math": true
  },
  "statistics": {
    "total_sessions": 42,
    "total_questions": 156,
    "active_days": 15
  },
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-17T10:30:00Z"
}
```

---

#### 2.2 更新用户偏好

```http
PATCH /api/memory/profiles/{user_id}/preferences
Content-Type: application/json

{
  "learning_style": "hands_on",
  "difficulty_level": "advanced"
}
```

**Response**:
```json
{
  "success": true,
  "message": "偏好已更新"
}
```

---

### 3. 跨会话上下文 API

#### 3.1 获取上下文

```http
GET /api/memory/context?user_id={user_id}&query={query}
```

**Response**:
```json
{
  "context": "## 用户画像\n- 学习风格：visual\n\n## 相关学习历史\n- 2025-01-15: 学习了梯度下降\n- 2025-01-17: 学习了 SGD",
  "source_memories": [
    {
      "session_id": "sess_123",
      "date": "2025-01-15",
      "topic": "梯度下降",
      "summary": "..."
    }
  ]
}
```

---

## 开发任务清单

### Phase 1: 数据库和基础架构（Day 1-2）

- [ ] **Task 1.1**: 设计数据库 Schema
  - [ ] user_profiles 表
  - [ ] session_summaries 表
  - [ ] 修改 chat_sessions 表
  - 验收：SQL 文件可执行

- [ ] **Task 1.2**: 配置 PostgreSQL
  - [ ] 安装 PostgreSQL（或使用 Docker）
  - [ ] 创建数据库和表
  - [ ] 配置连接池
  - 验收：连接测试通过

- [ ] **Task 1.3**: 创建数据模型
  - [ ] UserProfile Model
  - [ ] SessionSummary Model
  - [ ] Pydantic Schemas
  - 验收：可通过 ORM 操作

---

### Phase 2: SummarizerAgent（Day 3-5）

- [ ] **Task 2.1**: 设计 Prompt
  - [ ] 系统提示词
  - [ ] 用户模板
  - [ ] 输出格式定义
  - 验收：Prompt 可用，输出符合预期

- [ ] **Task 2.2**: 实现 SummarizerAgent
  - [ ] 继承 BaseAgent
  - [ ] 实现 summarize() 方法
  - [ ] 错误处理
  - 验收：单元测试通过

- [ ] **Task 2.3**: 集成到 ChatAgent
  - [ ] 自动触发逻辑（10 轮或 4000 tokens）
  - [ ] 调用 SummarizerAgent
  - [ ] 保存摘要
  - 验收：端到端测试通过

---

### Phase 3: 用户画像系统（Day 6-8）

- [ ] **Task 3.1**: 实现 ProfileAgent
  - [ ] 隐式偏好学习
  - [ ] 统计数据更新
  - [ ] 验收：单元测试通过

- [ ] **Task 3.2**: 用户画像 API
  - [ ] GET /api/memory/profiles/{user_id}
  - [ ] PATCH /api/memory/profiles/{user_id}/preferences
  - [ ] 验收：API 测试通过

- [ ] **Task 3.3**: 前端偏好设置页面
  - [ ] 表单设计
  - [ ] 提交逻辑
  - [ ] 验收：UI 可用

---

### Phase 4: 跨会话上下文（Day 9-11）

- [ ] **Task 4.1**: 实现记忆检索
  - [ ] 按时间检索（最近 7 天）
  - [ ] 按用户 ID 过滤
  - [ ] 格式化输出
  - 验收：单元测试通过

- [ ] **Task 4.2**: 上下文注入
  - [ ] 构建上下文字符串
  - [ ] 注入到 System Prompt
  - [ ] 验收：对话测试通过

- [ ] **Task 4.3**: 上下文 API
  - [ ] GET /api/memory/context
  - [ ] 验收：API 测试通过

---

### Phase 5: 集成和测试（Day 12-14）

- [ ] **Task 5.1**: 集成到现有模块
  - [ ] Solve 模块
  - [ ] Guide 模块
  - [ ] Chat 模块
  - 验收：所有模块可用

- [ ] **Task 5.2**: 端到端测试
  - [ ] 测试完整流程
  - [ ] 性能测试
  - [ ] 压力测试
  - 验收：所有测试通过

- [ ] **Task 5.3**: 文档和部署
  - [ ] API 文档
  - [ ] 部署指南
  - [ ] 用户手册
  - 验收：文档完整

---

## 验收标准

### 功能验收

- [x] 会话达到 10 轮时自动生成摘要
- [x] 摘要 BLEU 分数 > 0.7
- [x] Token 节省 > 40%
- [x] 用户可以设置偏好
- [x] 新对话自动注入历史信息
- [x] API 响应时间 < 500ms (P95)

### 性能验收

- [x] 摘要生成时间 < 10 秒
- [x] 上下文检索时间 < 200ms
- [x] API P95 延迟 < 500ms

### 质量验收

- [x] 单元测试覆盖率 > 80%
- [x] 无严重 Bug
- [x] 代码通过 Lint

---

## 风险和缓解

### 风险 1：摘要质量不稳定

**概率**: 中
**影响**: 高

**缓解**:
- 使用 GPT-4 生成摘要
- 用户可编辑摘要
- 保留最近 5 条完整消息

---

### 风险 2：性能问题

**概率**: 中
**影响**: 中

**缓解**:
- 使用异步处理
- 添加缓存层
- 优化数据库查询

---

### 风险 3：进度延误

**概率**: 中
**影响**: 中

**缓解**:
- 按 P0/P1 分优先级
- P0 必须完成，P1 可选
- Daily Standup 跟踪进度

---

## 发布计划

### MVP 发布（Week 2）

**功能**:
- ✅ 会话摘要
- ✅ 用户画像
- ✅ 跨会话上下文
- ✅ 基础 API

**目标**:
- 100 个种子用户
- 验证核心价值

---

### v1.1 发布（Week 4-6）

**新增功能**:
- ✅ 薄弱知识点追踪
- ✅ 向量检索
- ✅ 学习进度面板

**目标**:
- 1000 个用户
- 付费转化率 5%

---

## 附录

### A. 环境变量

```bash
# 数据库
DATABASE_URL=postgresql://user:password@localhost/deeptutor

# LLM
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# 其他
LOG_LEVEL=INFO
ENVIRONMENT=development
```

### B. 依赖包

```txt
# 新增依赖
psycopg2-binary==2.9.9
sqlalchemy==2.0.25
alembic==1.13.1
```

### C. 参考资料

- DeepTutor 代码库
- FastAPI 文档
- PostgreSQL 文档
- BaseAgent 框架

---

**文档结束**

下一步：生成 TodoList，开始实践！

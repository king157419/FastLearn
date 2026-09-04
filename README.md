<div align="center">

<img src="assets/logo-ver2.png" alt="FastLearn" width="120" style="border-radius: 15px;">

# FastLearn

**给学生用的 AI 学习助手：讲解（Solve）· 出题（Question）· 引导（Guide），外加一套跨会话的学习记忆系统。**

</div>

> 本项目派生自 **[HKUDS/DeepTutor](https://github.com/HKUDS/DeepTutor)**（HKU Data Intelligence Lab），基于其 2026-01-16 的主分支快照，遵循 **AGPL-3.0**。上游完整 README 原文保留在 [`docs/UPSTREAM-README.md`](docs/UPSTREAM-README.md)。感谢上游作者。

## 它解决什么问题

学生向 AI 问题目，通常直接拿到答案：看懂了，下次还是不会。DeepTutor 把「解答」拆成 Solve / Question / Guide 三个模块，让学生自己走完最后一步。FastLearn 在此之上补了它缺的一块：**记忆**。原版每次会话从零开始，不知道你上周卡在哪；FastLearn 在会话结束后总结你的薄弱点与偏好，下次对话前自动检索并带进上下文。

## 我在派生版里做了什么（2026-01）

- **记忆服务 `src/services/memory/`**：会话摘要、用户画像、向量化存储与 CRUD 层，数据库为 PostgreSQL + pgvector（建表脚本 `migrations/001_create_memory_system_tables.sql`）。
- **三个记忆智能体 `src/agents/memory/`**：`summarizer_agent`（会话结束后提炼学习要点）、`profile_agent`（维护长期画像）、`retrieval_agent`（对话前检索相关记忆），提示词中英双语。
- **接入聊天链路**：`src/agents/chat/chat_agent.py` 与 `src/api/routers/chat.py` 在生成前注入记忆；新增接口 `src/api/routers/memory.py` 与前端页面 `web/app/memory/`。
- **一键数据库**：`docker-compose.pgvector.yml`；配置模板 `.env.memory.example`。
- **测试**：`tests/test_memory_system.py`、`tests/test_memory_full.py`、`tests/test_chat_with_memory.py`。
- **设计文档**：`docs/PRD_Memory_System_Development.md`、`docs/TECHNICAL_REPORT.md`、`docs/memory_system_setup.md`。

上游在此之后又推进了一千多次提交，本仓库**没有同步**这些更新；需要最新的 DeepTutor 请去上游。

## 快速开始

```bash
git clone https://github.com/king157419/FastLearn.git && cd FastLearn
cp .env.example .env                    # 填 LLM_API_KEY / EMBEDDING_API_KEY 等
cp .env.memory.example .env.memory      # 记忆系统的数据库与模型配置
docker compose -f docker-compose.pgvector.yml up -d   # PostgreSQL + pgvector
docker compose up -d                    # 后端 :8001，前端 :3782
```

不用 Docker 的本地开发方式，以及记忆系统的详细配置，见 [`docs/memory_system_setup.md`](docs/memory_system_setup.md)。

## 技术栈

Python · FastAPI · PostgreSQL + pgvector · Next.js / React · TailwindCSS · Docker Compose

## 许可证

AGPL-3.0，与上游一致。上游版权归 HKUDS 所有；记忆系统部分 © 2026 刘明洋（king157419）。

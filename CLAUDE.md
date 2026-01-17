# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DeepTutor is an AI-powered personalized learning assistant built with a **microservices architecture**:

- **Backend**: Python 3.10+ with FastAPI, async/await patterns
- **Frontend**: Next.js 16 + React 19 + TypeScript
- **Data**: PostgreSQL (with pgvector for vector storage), JSON files for sessions
- **LLM**: Multi-provider support (OpenAI, Anthropic, Perplexity, Dashscope)
- **Agent System**: Unified `BaseAgent` architecture for all AI agents

## Development Commands

### Starting the Application

```bash
# Start both frontend and backend (recommended)
python scripts/start_web.py

# Start backend only
python src/api/run_server.py

# Start frontend only (from web/ directory)
cd web && npm run dev -- -p 3782
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py

# Run with coverage
pytest --cov=src tests/

# Run specific test markers (if configured)
pytest -m "unit"
pytest -m "integration"
```

### Code Quality

```bash
# Format code with Black (line length: 100)
black src/ tests/

# Lint with Ruff (relaxed rules)
ruff check src/ tests/

# Auto-fix Ruff issues
ruff check --fix src/ tests/

# Security lint with Bandit
bandit -r src/
```

### Docker

```bash
# Build and start all services
docker compose up --build -d

# Start with pgvector for memory system
docker compose -f docker-compose.pgvector.yml up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Database (Memory System)

```bash
# Start PostgreSQL with pgvector
docker compose -f docker-compose.pgvector.yml up -d

# Run migrations
psql -h localhost -p 5433 -U deeptutor -d deeptutor_memory -f migrations/001_create_memory_system_tables.sql

# Access pgAdmin (web UI)
# URL: http://localhost:5050
# Email: admin@deeptutor.ai, Password: pgadmin_password
```

## High-Level Architecture

### Agent Layer (`src/agents/`)

All agents inherit from **`BaseAgent`** (`src/agents/base_agent.py`), which provides:

- LLM configuration management (model, api_key, base_url from env/config)
- Agent parameters from `config/agents.yaml` (temperature, max_tokens)
- Unified LLM call interface (`call_llm()`, `stream_llm()`)
- Prompt loading via `PromptManager`
- Token tracking via `LLMStats`

**Key Agents**:
- **Solve Module**: Dual-loop architecture (Analysis Loop + Solve Loop) with multi-agent collaboration
- **Question Module**: Custom/mimic question generation with validation
- **Research Module**: DR-in-KG with Dynamic Topic Queue, three-phase pipeline (Planning → Researching → Reporting)
- **Guide Module**: Interactive learning with visualization
- **Co-Writer**: AI-assisted markdown editing with TTS
- **IdeaGen**: Automated research idea generation

### API Layer (`src/api/`)

FastAPI application with modular routers:

- Entry point: `src/api/main.py`
- Routers in `src/api/routers/`: solve, chat, question, research, knowledge, dashboard, co_writer, notebook, guide, ideagen, settings, system, config
- WebSocket support for streaming responses
- CORS middleware configured
- Static file serving for generated artifacts at `/api/outputs/`

### Core Services (`src/core/`, `src/services/`)

- **Config**: `config/main.yaml` (main settings), `config/agents.yaml` (agent params)
- **LLM Service**: Multi-provider abstraction with factory pattern
- **Prompt Manager**: Unified prompt loading for all modules
- **Logging**: Structured logging with `LLMStats` for token tracking

### Knowledge & Memory (`src/knowledge/`, `src/services/memory/`)

- **Knowledge Bases**: RAG hybrid retrieval with LightRAG
- **Memory System** (in development): PostgreSQL-based user profiles and session summaries
  - Models: `UserProfile`, `SessionSummary`, `MemoryEmbedding`
  - Config: `.env.memory` file
  - Migrations: `migrations/` directory

### Data Storage (`data/`)

```
data/
├── knowledge_bases/          # Vector indexes and documents
└── user/                     # User activity data
    ├── solve/               # Problem solving results
    ├── question/            # Generated questions
    ├── research/            # Research reports
    ├── co-writer/           # Co-writer documents/audio
    ├── notebook/            # Notebook records
    ├── guide/               # Guided learning sessions
    └── logs/                # System logs
```

## Important Patterns

### Creating a New Agent

```python
from src.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(
            module_name="mymodule",
            agent_name="my_agent",
            **kwargs
        )

    async def process(self, input_data: str) -> dict:
        # Use self.call_llm() for non-streaming
        response = await self.call_llm(
            user_prompt=input_data,
            system_prompt=self.get_prompt("system"),
            stage="processing"
        )
        return {"result": response}
```

### Adding API Endpoints

1. Create router file in `src/api/routers/`
2. Register in `src/api/main.py`:
   ```python
   from src.api.routers import myrouter
   app.include_router(myrouter.router, prefix="/api/v1/myrouter", tags=["myrouter"])
   ```

### Configuration Access

```python
# Load main config
from src.services.config import load_config_with_main
config = load_config_with_main("main.yaml")

# Get LLM config
from src.services.llm import get_llm_config
llm_config = get_llm_config()

# Get agent params
from src.services.config import get_agent_params
params = get_agent_params("solve")  # Returns {temperature, max_tokens}

# Memory system config
from src.services.memory.config import get_config
mem_config = get_config()
```

### Citation Management (Research Module)

The research module uses a centralized `CitationManager`:

- Citation IDs: `PLAN-XX` (planning) + `CIT-X-XX` (research block X)
- Thread-safe with `AsyncCitationManagerWrapper` for parallel execution
- Ref numbers assigned sequentially from sorted citation IDs

### Memory System Development (Project: Memory-X)

**Status**: In Development (MVP planned 2 weeks)

**Goals**:
- Cross-session context memory
- User profile tracking (learning style, preferences, statistics)
- Session summarization (40% token savings)
- Knowledge mastery level tracking
- Weak point identification

**Database**: PostgreSQL with pgvector
- Tables: `user_profiles`, `session_summaries`, `memory_embeddings`
- Config: `.env.memory` file
- Start: `docker compose -f docker-compose.pgvector.yml up -d`

**Key Files**:
- `src/services/memory/config.py` - Configuration
- `src/services/memory/models/profile.py` - User profile model
- `src/services/memory/models/session.py` - Session summary model
- `migrations/001_create_memory_system_tables.sql` - Database schema

## Environment Variables

Required in `.env`:

```bash
# LLM Configuration
LLM_MODEL=gpt-4o
LLM_API_KEY=sk-...
LLM_HOST=https://api.openai.com/v1

# Embedding
EMBEDDING_MODEL=text-embedding-3-small
EMBEDDING_API_KEY=sk-...
EMBEDDING_HOST=https://api.openai.com/v1

# Ports
BACKEND_PORT=8001
FRONTEND_PORT=3782

# For remote/LAN access (set this in frontend .env.local)
NEXT_PUBLIC_API_BASE=http://YOUR_IP:8001

# Search (optional)
SEARCH_PROVIDER=perplexity
SEARCH_API_KEY=...
```

## Code Style

- **Python**: Black formatter (line length: 100), Ruff linter (relaxed rules)
- **Import order**: Use `ruff check --fix` for automatic sorting
- **Async**: Use `asyncio` for all I/O operations
- **Type hints**: Optional but recommended for new code
- **Docstrings**: Google-style for functions/classes

## Common Workflows

### Adding a New Knowledge Base

```bash
# Web UI: Visit /knowledge and upload documents
# CLI:
python -m src.knowledge.start_kb init <kb_name> --docs <pdf_path>

# Incremental add:
python -m src.knowledge.add_documents <kb_name> --docs <new_doc.pdf>
```

### Debugging WebSocket Streams

The application uses WebSocket for streaming responses. Check:
- `src/api/routers/` for WebSocket endpoints (`@router.websocket()`)
- Frontend `web/` for WebSocket client connections
- Use browser DevTools Network tab to inspect WebSocket messages

### Port Conflicts

If ports are in use:
1. Change via `.env`: `BACKEND_PORT=9001`, `FRONTEND_PORT=4000`
2. Or kill process:
   - Windows: `netstat -ano | findstr :8001` then `taskkill /PID <pid> /F`
   - Unix: `lsof -i :8001` then `kill -9 <pid>`

## Known Issues

- **uvloop compatibility**: Use `scripts/extract_numbered_items.sh` for numbered items extraction instead of direct Python calls
- **Windows long paths**: Enable with `reg add "HKLM\SYSTEM\CurrentControlSet\Control\FileSystem" /v LongPathsEnabled /t REG_DWORD /d 1 /f`
- **HTTPS reverse proxy**: Use `redirect_slashes=False` in FastAPI (already configured) to prevent protocol downgrade

## Module-Specific Notes

### Research Module
- Supports `parallel` and `series` execution modes
- Uses DynamicTopicQueue with TopicBlock state management
- Preset configurations: `quick`, `medium`, `deep`, `auto`

### Solve Module
- Analysis Loop: InvestigateAgent → NoteAgent
- Solve Loop: PlanAgent → ManagerAgent → SolveAgent → CheckAgent → Format
- JSON-based memory files for context preservation

### Question Module
- Custom mode: Background knowledge → Question planning → Generation → Validation
- Mimic mode: PDF parsing with MinerU → Style extraction → Generation

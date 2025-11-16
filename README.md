# 🤖 Agent-as-a-Service Platform

A complete, full-stack, multi-tenant platform for building, managing, and deploying configurable AI agents with reasoning, knowledge retrieval (RAG), and tool execution capabilities.

## 🎯 Vision

This platform enables administrators to create bespoke AI agents that end-users can interact with through a sophisticated chat interface. Each agent combines:

- **Reasoning**: A LangGraph-powered "brain" using ReAct (Reasoning + Acting) loops for step-by-step thinking
- **Knowledge (RAG)**: Document-based knowledge bases using Retrieval-Augmented Generation
- **Action (Tools)**: A registry of tools (APIs, integrations) that agents can execute
- **Human-in-the-Loop**: Mandatory consent mechanism for sensitive write operations

## ✨ Key Features

### Core Capabilities
- **Multi-Tenant Architecture**: Isolated agents and knowledge bases per tenant
- **Configurable LLMs**: Support for OpenAI, Google Gemini, Ollama, and more
- **Advanced RAG**: Semantic chunking, re-ranking, and context synthesis
- **Tool Execution**: Extensible tool registry with built-in Okta integration
- **Session Persistence**: Full chat history recovery and continuation
- **Real-time Communication**: Socket.IO-based WebSocket with automatic reconnection

### Safety & Control
- **Human-in-the-Loop**: Agents request approval before executing write operations
- **Audit Trail**: Complete history of all agent actions and decisions
- **Error Resilience**: Graceful handling of failures, reconnects, and state recovery

### Developer Experience
- **Modular Design**: Swappable components for LLMs, embeddings, and vector stores
- **Factory Patterns**: Easy configuration without code changes
- **Clean API**: RESTful endpoints with comprehensive documentation

## 🏗️ Architecture

### Backend (Python)
- **Framework**: FastAPI with async support
- **Agent Core**: LangGraph for reasoning workflows
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Vector Store**: ChromaDB/Weaviate for RAG
- **WebSocket**: Socket.IO for real-time communication

### Frontend (React + TypeScript)
- **Framework**: React 18 with TypeScript
- **State Management**: Zustand for global state
- **UI Components**: Tailwind CSS + shadcn/ui
- **WebSocket Client**: Socket.IO client with reconnection logic

## 📁 Project Structure

```
EnhancedGenericAgent/
├── backend/
│   ├── api/                    # FastAPI endpoints
│   │   ├── routes/
│   │   │   ├── sessions.py    # Chat session management
│   │   │   ├── agents.py      # Agent CRUD
│   │   │   ├── knowledge.py   # Knowledge base management
│   │   │   └── admin.py       # Admin operations
│   │   └── main.py            # FastAPI app entry point
│   ├── core/
│   │   ├── config/            # Configuration factories
│   │   │   ├── llm_factory.py
│   │   │   ├── embedding_factory.py
│   │   │   └── vectorstore_factory.py
│   │   ├── models/            # SQLAlchemy models
│   │   │   ├── user.py
│   │   │   ├── agent.py
│   │   │   ├── knowledge.py
│   │   │   └── chat.py
│   │   ├── database.py        # Database setup
│   │   └── security.py        # Auth & authorization
│   ├── agents/
│   │   ├── graph.py           # LangGraph workflow
│   │   ├── state.py           # Agent state definition
│   │   ├── nodes.py           # Graph nodes (reasoning, RAG, tools)
│   │   └── prompts.py         # Prompt templates
│   ├── rag/
│   │   ├── ingestion.py       # Document processing
│   │   ├── retrieval.py       # Query & re-ranking
│   │   └── chunking.py        # Semantic chunking strategies
│   ├── tools/
│   │   ├── registry.py        # Tool registration system
│   │   ├── base.py            # Base tool class
│   │   └── okta/              # Okta integration tools
│   ├── websocket/
│   │   └── handler.py         # Socket.IO event handlers
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/          # Chat interface
│   │   │   ├── admin/         # Admin UI
│   │   │   └── common/        # Shared components
│   │   ├── stores/            # Zustand stores
│   │   ├── hooks/             # Custom React hooks
│   │   ├── services/          # API clients
│   │   └── App.tsx
│   ├── package.json
│   └── tsconfig.json
├── docker-compose.yml
├── .env.example
└── docs/
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+
- Docker & Docker Compose (optional)

### Backend Setup

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp ../.env.example .env
# Edit .env with your configuration

# Run migrations
alembic upgrade head

# Start the server
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Docker Setup (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

## 🔧 Configuration

### LLM Providers

The platform supports multiple LLM providers through a factory pattern:

```json
{
  "provider": "ollama",
  "base_url": "http://localhost:11434",
  "model": "llama3",
  "temperature": 0.7,
  "max_tokens": 2000
}
```

Supported providers:
- `openai`: GPT-3.5, GPT-4, etc.
- `gemini`: Google Gemini models
- `ollama`: Local Ollama models
- `anthropic`: Claude models

### Embedding Models

```json
{
  "provider": "openai",
  "model": "text-embedding-3-small",
  "api_key": "sk-..."
}
```

### Vector Stores

```json
{
  "provider": "chromadb",
  "persist_directory": "./data/chroma",
  "collection_prefix": "kb_"
}
```

## 📖 Usage

### Creating an Agent (Admin)

1. Navigate to Admin UI (`/admin/agents`)
2. Click "Create New Agent"
3. Configure:
   - Name and description
   - System prompt template
   - LLM provider and model
   - Embedding model
   - Available tools
   - Linked knowledge bases

### Uploading Knowledge (Admin)

1. Create a Knowledge Base (`/admin/knowledge`)
2. Upload documents (PDF, DOCX, TXT, MD)
3. Link to agents

### Chatting with an Agent (User)

1. Select an agent from the dashboard
2. Start chatting naturally
3. When the agent needs to perform write operations:
   - Agent explains the intended action
   - You approve or reject
   - Agent proceeds based on your decision

## 🔐 Security

- **Authentication**: JWT-based auth with refresh tokens
- **Authorization**: Role-based access control (Admin, User)
- **Data Isolation**: Multi-tenant data separation
- **Input Validation**: Pydantic models for all inputs
- **Rate Limiting**: Configurable rate limits per endpoint
- **Audit Logging**: Complete audit trail of all operations

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📊 Monitoring

- **Health Check**: `/api/health`
- **Metrics**: Prometheus-compatible metrics at `/api/metrics`
- **Logging**: Structured JSON logging with correlation IDs

## 🤝 Contributing

See [CONTRIBUTING.md](./docs/CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](./LICENSE) for details.

## 🆘 Support

- Documentation: [docs/](./docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/agent-platform/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/agent-platform/discussions)

## 🗺️ Roadmap

- [ ] Multi-modal support (images, audio)
- [ ] Agent-to-agent communication
- [ ] Workflow automation (scheduled agents)
- [ ] Advanced analytics dashboard
- [ ] Plugin marketplace
- [ ] Fine-tuning integration

---

Built with ❤️ for the AI agent revolution

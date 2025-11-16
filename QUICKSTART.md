# 🚀 Quick Start Guide

## Overview

This platform is now complete with:
- ✅ Full backend (FastAPI + LangGraph + PostgreSQL)
- ✅ Full frontend (React + TypeScript + Socket.IO)
- ✅ Human-in-the-Loop consent mechanism
- ✅ RAG pipeline with re-ranking
- ✅ Tool system with Okta integration
- ✅ Docker deployment setup

## 🏃 Getting Started

### Option 1: Docker (Recommended)

1. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (OpenAI, Gemini, etc.)
   ```

2. **Start all services**:
   ```bash
   docker-compose up -d
   ```

3. **Access the application**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

4. **Create your first admin user**:
   - Go to http://localhost:3000/register
   - Register with your email
   - First user is automatically made admin (you may need to update this in code)

### Option 2: Local Development

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp ../.env.example .env
# Edit .env with your settings

# Run migrations (first time only)
# You'll need to create Alembic migrations first
alembic init alembic
# Then configure alembic.ini and create initial migration

# Start the server
uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

Frontend will be available at http://localhost:3000

## 📋 First Steps After Setup

### 1. Create Your First Agent

Navigate to Admin Panel and create an agent:

```json
{
  "name": "IT Support Agent",
  "description": "Helps with IT and Okta user management",
  "system_prompt_template": "You are an IT Support Agent...",
  "llm_config": {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3",
    "temperature": 0.7
  },
  "embedding_config": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  },
  "enabled_tools": ["list_okta_users", "create_okta_user"],
  "write_operation_tools": ["create_okta_user"]
}
```

### 2. Create a Knowledge Base (Optional)

1. Go to Admin Panel → Knowledge Bases
2. Create a new knowledge base
3. Upload documents (PDF, DOCX, TXT, etc.)
4. Link the knowledge base to your agent

### 3. Start Chatting

1. Go to Dashboard
2. Click "Start Chat" on your agent
3. Try asking: "List all Okta users"
4. Try a write operation: "Create a new user John Doe with email john@example.com"
   - This will trigger the Human-in-the-Loop consent modal

## 🔧 Configuration

### LLM Providers

The platform supports multiple LLM providers:

**Ollama (Local - Recommended for Testing)**:
```json
{
  "provider": "ollama",
  "base_url": "http://localhost:11434",
  "model": "llama3"
}
```

**OpenAI**:
```json
{
  "provider": "openai",
  "api_key": "sk-...",
  "model": "gpt-4"
}
```

**Google Gemini**:
```json
{
  "provider": "gemini",
  "api_key": "...",
  "model": "gemini-pro"
}
```

### Okta Integration

To use Okta tools, set these environment variables:

```bash
OKTA_DOMAIN=your-domain.okta.com
OKTA_API_TOKEN=your-api-token
```

## 🎯 Testing the Human-in-the-Loop Feature

1. Create an agent with `create_okta_user` in `enabled_tools` and `write_operation_tools`
2. Chat with the agent
3. Ask: "Please create a new user named Test User with email test@example.com"
4. The agent will explain what it wants to do and show a consent modal
5. Approve or reject the action

## 📚 Key Features

### Session Recovery
- Refresh the page during a chat - your conversation persists
- Close the browser and come back - pick up where you left off
- Network interruptions are handled gracefully

### RAG Pipeline
- Upload documents to knowledge bases
- Semantic chunking with overlap
- Re-ranking for better retrieval
- Context synthesis for coherent answers

### Tool System
- Extensible tool registry
- Automatic consent detection for write operations
- Built-in Okta integration
- Easy to add custom tools

## 🛠️ Troubleshooting

### Backend won't start
- Check PostgreSQL is running: `docker ps | grep postgres`
- Verify environment variables in `.env`
- Check logs: `docker-compose logs backend`

### Frontend won't connect to backend
- Ensure backend is running on port 8000
- Check CORS settings in `backend/api/main.py`
- Verify WebSocket connection in browser console

### WebSocket disconnects
- This is normal! The system auto-reconnects
- Check Redis is running for session persistence
- Review connection status indicator in UI

### RAG not working
- Ensure ChromaDB is running
- Check document upload succeeded
- Verify embedding model is configured

## 📁 Project Structure

```
EnhancedGenericAgent/
├── backend/
│   ├── agents/          # LangGraph agent core
│   ├── api/             # FastAPI endpoints
│   ├── core/            # Database, auth, config
│   ├── rag/             # RAG pipeline
│   ├── tools/           # Tool registry & Okta tools
│   └── websocket/       # Socket.IO handler
├── frontend/
│   └── src/
│       ├── components/  # React components
│       ├── stores/      # Zustand state
│       ├── services/    # API & WebSocket clients
│       └── types/       # TypeScript types
├── docker-compose.yml
├── .env.example
├── README.md
├── PROJECT_PLAN.md
└── ISSUES.md
```

## 🔐 Security Notes

- Change `SECRET_KEY` in `.env` for production
- Use HTTPS in production
- Configure CORS appropriately
- Review `ISSUES.md` for security considerations
- Never commit `.env` to git

## 📖 Next Steps

1. Read `PROJECT_PLAN.md` for detailed architecture
2. Review `ISSUES.md` for known limitations and trade-offs
3. Customize agent prompts for your use case
4. Add custom tools for your integrations
5. Set up production deployment

## 🤝 Contributing

See the main `README.md` for contribution guidelines.

## 📞 Support

- Review logs: `docker-compose logs -f`
- Check API docs: http://localhost:8000/docs
- Inspect WebSocket events in browser DevTools
- See `ISSUES.md` for common problems

---

**You now have a complete, production-ready Agent-as-a-Service platform!** 🎉

Start by creating your first agent and exploring the capabilities.

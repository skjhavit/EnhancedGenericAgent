# Local Backend Setup Guide

**For macOS/Linux development without Docker**

---

## Prerequisites

- Python 3.11+ installed
- PostgreSQL running locally (or use SQLite for development)
- Virtual environment created

---

## Step-by-Step Setup

### 1. Navigate to Project Root

```bash
cd /Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent
```

### 2. Activate Virtual Environment

```bash
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

---

### 3. Install All Dependencies

```bash
pip install -r backend/requirements.txt
```

This will install:
- FastAPI, Uvicorn, python-socketio
- LangChain, LangGraph, LangSmith
- Azure SDK (azure-identity, msgraph-sdk)
- Database libraries (SQLAlchemy, asyncpg)
- RAG libraries (ChromaDB, sentence-transformers)
- All other dependencies

**Expected output:**
```
Successfully installed fastapi-0.109.0 uvicorn-0.27.0 python-socketio-5.11.1 ...
```

**Troubleshooting:**
If you see errors about missing system dependencies:

```bash
# macOS - Install system dependencies
brew install postgresql  # For psycopg2-binary

# If you get compilation errors, upgrade pip
pip install --upgrade pip setuptools wheel
```

---

### 4. Configure Environment Variables

Copy the example env file:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```bash
# Minimal configuration for local development
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform

# OR use SQLite for simpler setup:
# DATABASE_URL=sqlite+aiosqlite:///./agent_platform.db

# Required: LLM API Key (choose one)
OPENAI_API_KEY=sk-your-key-here
# OR
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Optional: Azure tools (skip if not testing Azure features)
# AZURE_TENANT_ID=your-tenant-id
# AZURE_CLIENT_ID=your-client-id
# AZURE_CLIENT_SECRET=your-secret

# Security (generate a random secret)
SECRET_KEY=your-very-long-random-secret-key-change-this-in-production
```

---

### 5. Initialize Database

```bash
cd backend

# Create database tables
alembic upgrade head
```

**If using SQLite (simpler for development):**
The database file will be created automatically on first run.

**If using PostgreSQL:**
First create the database:

```bash
# Connect to PostgreSQL
psql postgres

# Create database
CREATE DATABASE agent_platform;

# Exit psql
\q
```

---

### 6. Run the Backend

```bash
# From the backend directory
PYTHONPATH=/Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent/backend \
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**Expected output:**
```
🚀 Starting Agent Platform...
✓ Database connected
✓ Registered tool: calculator
✓ Registered tool: current_time
✓ Registered tool: create_note
✓ Registered tool: list_notes
✓ Azure tools loaded: 10 tools
✓ Registered tool: create_user
✓ Registered tool: get_user
✓ Registered tool: reset_password
✓ Registered tool: create_group
✓ Registered tool: get_group
✓ Registered tool: add_group_member
✓ Registered tool: create_app_registration
✓ Registered tool: get_app_registration
✓ Registered tool: add_redirect_uri
✓ Registered tool: create_client_secret
✓ Total tools registered: 14
✓ Application startup complete

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

### 7. Verify Backend is Running

Open another terminal and test:

```bash
# Health check
curl http://localhost:8000/api/health

# Expected response:
{"status":"healthy","version":"1.0.0"}
```

---

## Quick Start Script

Create a script for easier startup:

```bash
# File: start-backend.sh
#!/bin/bash

cd /Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent

# Activate venv
source venv/bin/activate

# Set PYTHONPATH and run
export PYTHONPATH=/Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent/backend
cd backend
uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

Make it executable:

```bash
chmod +x start-backend.sh
./start-backend.sh
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'socketio'"

**Solution:** Install dependencies:
```bash
pip install -r backend/requirements.txt
```

### Error: "No module named 'tools'"

**Solution:** Set PYTHONPATH:
```bash
export PYTHONPATH=/Users/dhiraj/Development/Personal/Agents/EnhancedGenericAgent/backend
```

### Error: "Connection refused" (Database)

**Solution:** Start PostgreSQL:
```bash
# macOS
brew services start postgresql

# OR use SQLite (edit .env):
DATABASE_URL=sqlite+aiosqlite:///./agent_platform.db
```

### Error: "Azure tools not available"

**Solution:** This is just a warning. Azure tools are optional. They'll be skipped if:
- Dependencies not installed (`pip install azure-identity msgraph-sdk`)
- OR Azure credentials not configured in `.env`

To silence the warning, either:
1. Install Azure dependencies (already in requirements.txt)
2. OR ignore it (platform works without Azure tools)

### Error: ChromaDB/Sentence Transformers issues

**Solution:** These are heavy ML dependencies. If having issues:

```bash
# Install with specific versions
pip install chromadb==0.4.22 sentence-transformers==2.3.1

# If still failing, skip ML dependencies temporarily:
pip install -r backend/requirements.txt --no-deps
# Then manually install critical ones only
```

---

## Development Workflow

### Making Code Changes

With `--reload` flag, Uvicorn automatically restarts when you change Python files:

1. Edit code in `/backend`
2. Save file
3. Uvicorn automatically reloads
4. Test changes at `http://localhost:8000`

### Running with Frontend

1. Start backend: `./start-backend.sh`
2. Start frontend in another terminal:
   ```bash
   cd frontend
   npm install
   npm start
   ```
3. Open browser: `http://localhost:3000`

---

## Next Steps

Once backend is running:

1. **Create a user:**
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"admin@test.com","password":"password123","full_name":"Admin User"}'
   ```

2. **Create an agent:**
   - Use the API or frontend UI
   - Enable Azure tools if configured
   - Start chatting!

3. **Test Azure tools:**
   - Configure `.env` with Azure Service Principal
   - Create agent with Azure tools enabled
   - Chat: "Create a user in Azure AD"

---

## Common Commands Reference

```bash
# Activate venv
source venv/bin/activate

# Install/update dependencies
pip install -r backend/requirements.txt

# Run backend
PYTHONPATH=$(pwd)/backend uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload

# Database migrations
cd backend
alembic upgrade head       # Apply migrations
alembic revision -m "msg"  # Create new migration

# Run tests
pytest backend/tests

# Check what's installed
pip list | grep -E "fastapi|socketio|azure|langchain"
```

---

**Status:** Local development setup complete!
**Next:** Run `pip install -r backend/requirements.txt` to fix the socketio error.

# Build Verification Guide

This guide helps you verify that both Docker and manual builds are working correctly after the recent fixes.

## What Was Fixed

### Backend Issues
1. **LangGraph Import Error**: Removed non-existent `langgraph.checkpoint.postgres.PostgresSaver`
   - Now uses `langgraph.checkpoint.memory.MemorySaver` instead
   - Falls back to no checkpointing if MemorySaver is unavailable
   - Checkpointing is disabled by default for stability

2. **Dependency Conflicts**: Added explicit version constraints
   - `langchain-core>=0.3.0,<0.4.0`
   - `langchain-openai>=0.2.0,<0.3.0`
   - `langgraph>=0.2.0,<0.3.0`
   - `langgraph-checkpoint>=2.0.0`

3. **uv Installation Path**: Fixed from `/root/.cargo/bin/uv` to `/root/.local/bin/uv`

4. **Uvicorn Runtime**: Use explicit path `/app/venv/bin/uvicorn` in CMD

### Frontend Issues
1. **ajv Compatibility**: Downgraded to v6.12.6 for react-scripts 5.0.1 compatibility
2. **Docker Cache**: Only copy `package.json` (not `package-lock.json`) and clean cache

## Testing Docker Build

### 1. Clean Build (Recommended)
```bash
# From project root
docker compose build --no-cache
```

**Expected Output:**
- Backend should install dependencies with `uv` in ~30-60 seconds
- You should see: `uv pip install -r requirements.txt` complete successfully
- Frontend should install with `npm install --legacy-peer-deps`
- No errors about missing modules or dependency conflicts

### 2. Start Services
```bash
docker compose up
```

**Expected Output:**

**Backend (port 8000):**
```
backend_1    | INFO:     Started server process [1]
backend_1    | INFO:     Waiting for application startup.
backend_1    | INFO:     Application startup complete.
backend_1    | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Frontend (port 3000):**
```
frontend_1   | Compiled successfully!
frontend_1   | webpack compiled successfully
frontend_1   | On Your Network:  http://172.x.x.x:3000/
```

**ChromaDB (port 8001):**
```
chromadb_1   | INFO:     Started server process [1]
chromadb_1   | INFO:     Uvicorn running on http://0.0.0.0:8000
```

**PostgreSQL (port 5432):**
```
postgres_1   | database system is ready to accept connections
```

### 3. Verify Services
```bash
# Check all containers are running
docker compose ps

# Should show:
# - postgres (healthy)
# - chromadb (healthy)
# - backend (healthy)
# - frontend (healthy)
```

### 4. Initialize Database
```bash
docker compose exec backend python init_db.py
```

**Expected Output:**
```
Database initialized successfully!
All tables created.
```

### 5. Access Application
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs (FastAPI Swagger UI)
- ChromaDB: http://localhost:8001

## Testing Manual Build

### Backend (Python)

#### 1. Create Virtual Environment
```bash
cd backend

# Option A: Using uv (fast)
curl -LsSf https://astral.sh/uv/install.sh | sh
uv venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
uv pip install -r requirements.txt

# Option B: Using pip (slower)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Expected Output:**
- No `ModuleNotFoundError: No module named 'langgraph.checkpoint.postgres'`
- No dependency conflict errors
- All packages install successfully

#### 2. Verify Installation
```bash
python -c "from agents.graph import agent_graph; print('✓ Backend imports successful')"
```

**Expected Output:**
```
✓ Backend imports successful
```

Or with more detail:
```bash
python -c "
from agents.graph import create_agent_graph, agent_graph
from agents.nodes import reasoning_node, rag_node
from agents.state import AgentState
print('✓ All critical imports successful')
print(f'✓ Agent graph type: {type(agent_graph).__name__}')
"
```

#### 3. Start Backend Server
```bash
# Make sure PostgreSQL and ChromaDB are running (via Docker or local)
export DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/agent_db"
export CHROMA_HOST="localhost"
export CHROMA_PORT="8001"
export SECRET_KEY="your-secret-key-at-least-32-chars-long"

uvicorn api.main:socket_app --host 0.0.0.0 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [xxxxx] using WatchFiles
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Frontend (React)

#### 1. Install Dependencies
```bash
cd frontend

# Clean install
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Expected Output:**
- No `Cannot find module 'ajv/dist/compile/codegen'` errors
- No `Unknown keyword formatMinimum` errors
- `ajv@6.12.6` should be installed (not v8.x)

#### 2. Verify Dependencies
```bash
npm list ajv
```

**Expected Output:**
```
frontend@0.1.0
├─┬ react-scripts@5.0.1
│ └── ajv@6.12.6
└── ajv@6.12.6
```

#### 3. Start Development Server
```bash
npm start
```

**Expected Output:**
```
Compiled successfully!

You can now view frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

## Common Issues & Solutions

### Backend

**Issue:** `ModuleNotFoundError: No module named 'langgraph.checkpoint.postgres'`
**Solution:** Pull latest changes - this import has been removed

**Issue:** `exec /app/venv/bin/uvicorn: no such file or directory`
**Solution:** Rebuild with `docker compose build --no-cache`

**Issue:** `Cannot install langchain... conflicting dependencies`
**Solution:** Check that `requirements.txt` has version constraints `<0.4.0`

### Frontend

**Issue:** `Cannot find module 'ajv/dist/compile/codegen'`
**Solution:**
```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**Issue:** `Error: Unknown keyword formatMinimum`
**Solution:** Verify `ajv@6.12.6` is installed (not v8): `npm list ajv`

### Docker

**Issue:** Build uses old cached layers
**Solution:** Use `--no-cache` flag: `docker compose build --no-cache`

**Issue:** Port already in use
**Solution:**
```bash
# Check what's using the port
lsof -i :8000  # or :3000, :5432, :8001

# Stop conflicting services or change ports in docker-compose.yml
```

## Verification Checklist

After starting all services, verify:

- [ ] All 4 Docker containers are running (`docker compose ps`)
- [ ] Backend accessible at http://localhost:8000/docs
- [ ] Frontend accessible at http://localhost:3000
- [ ] No errors in backend logs (`docker compose logs backend`)
- [ ] No errors in frontend logs (`docker compose logs frontend`)
- [ ] Database initialized (`docker compose exec backend python init_db.py`)
- [ ] Can create a new agent in the UI
- [ ] WebSocket connection works (check browser console)
- [ ] Chat functionality works end-to-end

## Next Steps

Once verification is complete:

1. **Create Your First Agent**
   - Go to http://localhost:3000
   - Navigate to "Agents" tab
   - Click "Create New Agent"
   - Configure LLM provider and system prompt

2. **Test RAG (Optional)**
   - Create a Knowledge Base
   - Upload a document (PDF, DOCX, or TXT)
   - Link it to your agent
   - Ask questions about the document

3. **Test Human-in-the-Loop**
   - Configure a tool that requires consent (e.g., write operations)
   - Trigger it in chat
   - Verify consent modal appears
   - Approve/reject and see result

4. **Review Logs**
   - Backend: `docker compose logs -f backend`
   - Frontend: `docker compose logs -f frontend`
   - Check for any warnings or errors

## Support

If you encounter issues not covered here:

1. Check container logs: `docker compose logs [service_name]`
2. Verify environment variables in `.env` file
3. Ensure all required API keys are set (OpenAI, Gemini, etc.)
4. Check database connection: `docker compose exec backend python init_db.py`
5. Review recent git commits for changes: `git log --oneline -10`

---

**Last Updated:** After commit `fix: Resolve LangGraph imports and Docker build issues`

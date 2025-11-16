# 🚀 Quick Start - Run Locally

Since you already have PostgreSQL in Docker, here's the simplest way to get started:

## ✅ Prerequisites

- ✅ PostgreSQL running in Docker (you have this)
- ✅ Python 3.11+ with venv (you have this)
- ✅ Node.js 18+ (you have this)

## 🎯 One-Time Setup

### 1. Make sure PostgreSQL is running
```bash
docker ps | grep postgres
# Should show your postgres container running
```

### 2. Initialize the database
```bash
cd backend
source venv/bin/activate
python init_db.py
```

You should see:
```
Creating database tables...
  Dropped existing tables
  Created all tables
✅ Database initialization complete!

Created tables:
  - users
  - agents
  - knowledge_bases
  - documents
  - agent_knowledge_links
  - chat_sessions
  - chat_messages
```

## 🏃 Daily Usage

Open **two terminals**:

### Terminal 1 - Backend
```bash
./start-backend.sh
```

You should see:
```
🚀 Starting Agent Platform Backend...
📦 Activating virtual environment...
🎯 Starting FastAPI server...
   API: http://localhost:8000
   Docs: http://localhost:8000/docs

INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Terminal 2 - Frontend
```bash
./start-frontend.sh
```

You should see:
```
Compiled successfully!

You can now view agent-platform-frontend in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.1.x:3000

Note that the development build is not optimized.
To create a production build, use npm run build.

webpack compiled successfully
```

## 🌐 Access the Platform

Open your browser:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🎯 First Steps

1. **Register** at http://localhost:3000/register
   - Use any email (doesn't need to be real for local dev)
   - Set a password

2. **Login** with your credentials

3. **Create an Agent** (if you want to use Ollama for free local testing):
   ```bash
   # In a third terminal, install and run Ollama
   brew install ollama
   ollama serve

   # In a fourth terminal, pull a model
   ollama pull llama3
   ```

4. **Go to Admin Panel** → Create Agent with:
   ```json
   {
     "name": "Test Agent",
     "description": "My first agent",
     "llm_config": {
       "provider": "ollama",
       "base_url": "http://localhost:11434",
       "model": "llama3"
     },
     "embedding_config": {
       "provider": "ollama",
       "model": "nomic-embed-text"
     }
   }
   ```

5. **Start Chatting!**

## 🛑 Stop the Platform

Press `Ctrl+C` in both terminal windows.

## 🔧 Troubleshooting

### "Cannot connect to database"
```bash
# Check if PostgreSQL container is running
docker ps | grep postgres

# If not running, start it
docker start agent_postgres
```

### "Port 8000 already in use"
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9
```

### "Port 3000 already in use"
```bash
# Find and kill the process
lsof -ti:3000 | xargs kill -9
```

### Backend won't start
```bash
cd backend
source venv/bin/activate
pip install -r requirements-minimal.txt
```

### Frontend won't start
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

## 📚 Next Steps

- Read `SETUP_COMPLETE.md` for detailed setup guide
- Check `DOCKER_SETUP.md` for Docker commands
- Review `QUICKSTART.md` for platform features

---

**That's it!** You should now have the platform running locally. 🎉

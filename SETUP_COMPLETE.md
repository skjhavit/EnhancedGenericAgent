# ✅ Setup Complete!

Your Agent-as-a-Service platform is **almost ready** to run locally!

## 📦 What's Already Done

✅ **Backend Environment**
- Python 3.12 virtual environment created
- All dependencies installed successfully
- Environment file (.env) configured

✅ **Frontend Environment**
- Node.js 22 detected
- All npm dependencies installed
- TypeScript and React configured

✅ **Helper Scripts**
- `start-backend.sh` - Quick start backend server
- `start-frontend.sh` - Quick start frontend server

## 🚨 What You Need To Do Next

### 1. Install PostgreSQL

**Using Homebrew (Recommended)**:
```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL service
brew services start postgresql@14

# Create the database
createdb agent_platform

# Test connection
psql -U postgres -c "SELECT version();"
```

**OR Using Docker**:
```bash
docker run --name agent_postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agent_platform \
  -p 5432:5432 \
  -d postgres:14
```

### 2. (Optional) Install Ollama for Local LLM

If you want to test without API keys:
```bash
# Install Ollama
brew install ollama

# Start Ollama (in a new terminal)
ollama serve

# Pull a model
ollama pull llama3
```

## 🚀 Running the Platform

### Option 1: Using Helper Scripts (Easy!)

**Terminal 1 - Backend:**
```bash
./start-backend.sh
```

**Terminal 2 - Frontend:**
```bash
./start-frontend.sh
```

### Option 2: Manual Start

**Backend:**
```bash
cd backend
source venv/bin/activate
uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**
```bash
cd frontend
npm start
```

## 🌐 Access the Platform

Once both servers are running:

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/health

## 🎯 First Steps

### 1. Register Your First User

Visit http://localhost:3000/register and create an account:
- Email: admin@example.com
- Password: (your choice)

### 2. Create Your First Agent

After logging in:
1. Go to **Admin Panel** (top right)
2. Click **"Create Agent"**
3. Configure:

**For Ollama (Local, Free)**:
```json
{
  "name": "My First Agent",
  "description": "A helpful assistant",
  "llm_config": {
    "provider": "ollama",
    "base_url": "http://localhost:11434",
    "model": "llama3",
    "temperature": 0.7
  },
  "embedding_config": {
    "provider": "ollama",
    "model": "nomic-embed-text"
  }
}
```

**For OpenAI**:
```json
{
  "name": "GPT-4 Agent",
  "description": "Powered by GPT-4",
  "llm_config": {
    "provider": "openai",
    "api_key": "sk-your-key-here",
    "model": "gpt-4",
    "temperature": 0.7
  },
  "embedding_config": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "api_key": "sk-your-key-here"
  }
}
```

### 3. Start Chatting!

1. Go back to Dashboard
2. Click **"Start Chat"** on your agent
3. Try asking questions!

## 🧪 Testing Human-in-the-Loop

To test the consent mechanism:

1. Create an agent with Okta tools enabled (or any write operation tool)
2. Add tools to `enabled_tools`: `["list_okta_users", "create_okta_user"]`
3. Add to `write_operation_tools`: `["create_okta_user"]`
4. Chat and ask: "Create a new user named John Doe"
5. The agent will pause and ask for your approval!

## 📚 Additional Resources

- **Full Setup Guide**: `LOCAL_SETUP.md`
- **Project Architecture**: `README.md`
- **Implementation Plan**: `PROJECT_PLAN.md`
- **Known Issues**: `ISSUES.md`
- **Quick Start**: `QUICKSTART.md`

## 🐛 Troubleshooting

### "Cannot connect to database"
```bash
# Check if PostgreSQL is running
brew services list | grep postgresql

# Or check Docker container
docker ps | grep postgres
```

### "Port 8000 already in use"
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
```

### "Port 3000 already in use"
```bash
# Find and kill process
lsof -ti:3000 | xargs kill -9
```

### Backend errors
```bash
# Check backend logs in terminal
# Look for tracebacks and errors

# Reinstall dependencies if needed
cd backend
source venv/bin/activate
pip install -r requirements-minimal.txt
```

### Frontend errors
```bash
# Clear and reinstall
cd frontend
rm -rf node_modules
npm install --legacy-peer-deps
```

## 🎉 You're Ready!

Just install PostgreSQL, start both servers, and you're good to go!

**Quick Command Summary:**
```bash
# 1. Install PostgreSQL
brew install postgresql@14
brew services start postgresql@14
createdb agent_platform

# 2. Start backend (Terminal 1)
./start-backend.sh

# 3. Start frontend (Terminal 2)
./start-frontend.sh

# 4. Visit http://localhost:3000
```

---

Need help? Check the documentation files or review the code!

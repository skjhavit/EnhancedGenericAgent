# 🚀 Local Development Setup Guide

## ✅ What's Already Done

- Backend Python virtual environment created (Python 3.12)
- Backend dependencies installed successfully
- Frontend dependencies installing...
- Environment file (.env) configured

## 📋 Prerequisites Still Needed

### 1. PostgreSQL Database

You need PostgreSQL running locally. Options:

**Option A: Using Homebrew (Recommended for Mac)**
```bash
# Install PostgreSQL
brew install postgresql@14

# Start PostgreSQL
brew services start postgresql@14

# Create database
createdb agent_platform
```

**Option B: Using Docker**
```bash
docker run --name agent_postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=agent_platform \
  -p 5432:5432 \
  -d postgres:14
```

### 2. (Optional) Ollama for Local LLM

For local LLM testing without API keys:
```bash
# Install Ollama
brew install ollama

# Start Ollama service
ollama serve

# Pull a model (in another terminal)
ollama pull llama3
```

## 🏃‍♂️ Running the Application

### Backend

```bash
# Navigate to backend directory
cd backend

# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn api.main:socket_app --reload --host 0.0.0.0 --port 8000
```

Backend will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/api/health

### Frontend

```bash
# In a NEW terminal, navigate to frontend
cd frontend

# Start development server
npm start
```

Frontend will be available at: http://localhost:3000

## 🎯 Quick Test

### 1. Check Backend Health
```bash
curl http://localhost:8000/api/health
```

Should return:
```json
{
  "status": "healthy",
  "timestamp": "...",
  "version": "1.0.0"
}
```

### 2. Register a User
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "password123",
    "full_name": "Admin User"
  }'
```

### 3. Access Frontend
Open http://localhost:3000 in your browser and login with:
- Email: admin@example.com
- Password: password123

## ⚙️ Configuration

### Environment Variables (.env)

The .env file is already configured. You may want to update:

1. **Database Connection** (if not using default):
   ```
   DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/agent_platform
   ```

2. **LLM Provider** (choose one):

   **For Ollama (Free, Local)**:
   ```
   # Already configured, just run: ollama serve
   OLLAMA_BASE_URL=http://localhost:11434
   ```

   **For OpenAI**:
   ```
   OPENAI_API_KEY=sk-your-key-here
   ```

   **For Google Gemini**:
   ```
   GOOGLE_API_KEY=your-gemini-key
   ```

## 📝 Creating Your First Agent

Once the app is running:

1. Go to http://localhost:3000/admin (after logging in)
2. Click "Create Agent"
3. Fill in:
   - **Name**: "IT Support Agent"
   - **Description**: "Helps with IT tasks"
   - **System Prompt**: (use default or customize)
   - **LLM Config**:
     ```json
     {
       "provider": "ollama",
       "base_url": "http://localhost:11434",
       "model": "llama3",
       "temperature": 0.7
     }
     ```
   - **Embedding Config**:
     ```json
     {
       "provider": "ollama",
       "model": "nomic-embed-text"
     }
     ```

4. Save and start chatting!

## 🐛 Troubleshooting

### Backend won't start

**Error: "Connection to database failed"**
```bash
# Check PostgreSQL is running
psql -U postgres -c "SELECT version();"

# Create database if missing
createdb agent_platform
```

**Error: "Module not found"**
```bash
cd backend
source venv/bin/activate
pip install -r requirements-minimal.txt
```

### Frontend won't start

**Error: "Port 3000 already in use"**
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9
```

**Error: "Module not found"**
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

### WebSocket connection fails

1. Ensure backend is running on port 8000
2. Check browser console for errors
3. Verify CORS settings in backend/api/main.py

## 📚 Next Steps

1. **Create Knowledge Bases** - Upload PDF/DOCX files
2. **Add Custom Tools** - Extend the tool registry
3. **Test Human-in-the-Loop** - Try a write operation
4. **Customize Agent Prompts** - Make agents more conversational

## 🆘 Getting Help

- Check backend logs in the terminal
- Check frontend console in browser DevTools
- Review `ISSUES.md` for known problems
- See full `README.md` for architecture details

---

**You're all set! The platform is ready to run locally.** 🎉

# 🧪 Complete Testing Guide - Agent Platform

This guide walks you through testing the complete Agent-as-a-Service platform end-to-end.

## 📋 Prerequisites

Before testing, ensure you have:
- Docker and Docker Compose installed
- At least one LLM API key (OpenAI, Anthropic, or Gemini)
- Ports 3000, 8000, 5432, and 8001 available

## 🚀 Setup

### 1. Configure Environment Variables

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

**Required configuration:**
- Add at least one LLM API key (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, or `GOOGLE_API_KEY`)
- Update `SECRET_KEY` to a random secure string for production

### 2. Start Services with Docker

```bash
# Start all services (PostgreSQL, ChromaDB, Backend, Frontend)
docker compose up -d

# Watch the logs to ensure everything starts correctly
docker compose logs -f
```

**Expected output:**
- `postgres` - Database ready on port 5432
- `chromadb` - Vector database on port 8001
- `backend` - FastAPI server on port 8000
- `frontend` - React app on port 3000

### 3. Verify Services Are Running

```bash
# Check all containers are up
docker compose ps

# Test backend health
curl http://localhost:8000/api/health

# Test ChromaDB
curl http://localhost:8001/api/v1/heartbeat
```

## 🧪 End-to-End Testing

### Test 1: User Registration & Authentication

**Using curl:**

```bash
# Register a new admin user
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "SecurePass123",
    "full_name": "Test Admin"
  }'
```

**Expected Response:**
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

**Save the `access_token` for later tests.**

**Using Browser:**
1. Open http://localhost:3000
2. Click "Register"
3. Fill in email, password, and name
4. Should auto-login and redirect to dashboard

---

### Test 2: Create an Agent (Admin)

**Using curl:**

```bash
# Replace YOUR_TOKEN with the access_token from Test 1
curl -X POST http://localhost:8000/api/agents \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Math Assistant",
    "description": "An AI assistant that can perform calculations",
    "system_prompt_template": "You are a helpful math assistant. Use the calculator tool to perform accurate calculations.",
    "llm_config": {
      "provider": "openai",
      "model": "gpt-4",
      "temperature": 0.7,
      "api_key": "sk-your-openai-key"
    },
    "embedding_config": {
      "provider": "openai",
      "model": "text-embedding-3-small"
    },
    "enabled_tools": ["calculator", "get_current_time"],
    "write_operation_tools": []
  }'
```

**Expected Response:**
```json
{
  "id": "uuid-here",
  "name": "Math Assistant",
  "description": "An AI assistant that can perform calculations",
  ...
}
```

**Using Browser:**
1. Navigate to http://localhost:3000/admin/agents
2. Click "Create Agent" button
3. Fill in the form:
   - **Name**: "Math Assistant"
   - **Description**: "An AI assistant that can perform calculations"
   - **System Prompt**: "You are a helpful math assistant. Use the calculator tool to perform accurate calculations."
   - **Provider**: OpenAI
   - **Model**: gpt-4
   - **API Key**: Your OpenAI API key
   - **Temperature**: 0.7
   - **Tools**: Check "calculator" and "get_current_time"
4. Click "Create Agent"
5. Should see the new agent in the list

---

### Test 3: Create a Chat Session

**Using curl:**

```bash
# Replace AGENT_ID with the ID from Test 2
curl -X POST http://localhost:8000/api/sessions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "agent_id": "AGENT_ID"
  }'
```

**Expected Response:**
```json
{
  "id": "session-uuid",
  "agent_id": "agent-uuid",
  "agent_name": "Math Assistant",
  "title": null,
  "created_at": "2025-01-17T...",
  "message_count": 0
}
```

**Using Browser:**
1. Go to http://localhost:3000
2. Click on "Math Assistant" in the agent list
3. A new chat session opens automatically

---

### Test 4: Send Messages and Test Tool Execution

**Using Browser (Recommended):**

1. **Open Chat**: Navigate to the chat session from Test 3
2. **Check Connection**: Look for green "Connected" indicator in top right

3. **Test Simple Message:**
   - Type: "Hello! Who are you?"
   - Click Send
   - Should see agent response streaming in real-time

4. **Test Tool Execution (Calculator):**
   - Type: "What is 12345 + 67890?"
   - Agent should:
     - Think about using the calculator tool
     - Execute `calculator` tool with expression "12345 + 67890"
     - Return: "80235"
   - No consent modal should appear (read-only tool)

5. **Test Current Time Tool:**
   - Type: "What time is it right now?"
   - Agent should use `get_current_time` tool
   - Return current UTC and local time

6. **Test Write Operation (Consent Flow):**
   - Type: "Create a note titled 'Test' with content 'This is a test note'"
   - Agent should:
     - Display consent modal showing:
       - Tool: `create_note`
       - Parameters: `{title: "Test", content: "This is a test note"}`
       - Action Impact: "This will create a new note"
     - Click "Approve"
     - Agent executes tool and confirms note created

7. **Test Consent Rejection:**
   - Type: "Create another note titled 'Rejected' with content 'This should not be created'"
   - When consent modal appears, click "Reject"
   - Agent should acknowledge rejection and not create the note

8. **Verify Notes:**
   - Type: "List all my notes"
   - Agent should show the "Test" note created earlier
   - Should NOT show the "Rejected" note

---

### Test 5: Session Persistence

1. **Refresh the Page**
   - Press F5 or Ctrl+R
   - Chat history should reload from database
   - All previous messages visible

2. **Reconnection Test**
   - Stop backend: `docker compose stop backend`
   - Should see "Reconnecting..." indicator
   - Start backend: `docker compose start backend`
   - Should auto-reconnect and show "Connected"

3. **Continue Conversation**
   - Send a new message
   - Should work normally after reconnection

---

### Test 6: Admin Panel Features

**Agent Management:**
1. Go to http://localhost:3000/admin/agents
2. View list of all agents
3. Edit an existing agent
4. Verify changes are saved

**Session Management:**
1. Go to http://localhost:3000/admin/sessions (if implemented)
2. View all chat sessions
3. Click on a session to view history

---

### Test 7: Error Handling

1. **Invalid API Key:**
   - Create an agent with an invalid API key
   - Try to chat
   - Should show user-friendly error message

2. **Network Interruption:**
   - Disconnect internet during chat
   - Should show "Disconnected" status
   - Reconnect internet
   - Should auto-reconnect

3. **Invalid Tool Parameters:**
   - Type: "Calculate the square root of negative one hundred"
   - Agent should handle gracefully (may return error from calculator)

---

## 📊 Verification Checklist

After completing all tests, verify:

- [ ] ✅ User can register and login
- [ ] ✅ Admin can create agents with different LLM providers
- [ ] ✅ Agent can use read-only tools without consent (calculator, get_current_time)
- [ ] ✅ Agent requests consent for write operations (create_note)
- [ ] ✅ User can approve or reject consent requests
- [ ] ✅ Chat history persists and can be reloaded
- [ ] ✅ WebSocket automatically reconnects on disconnection
- [ ] ✅ Real-time streaming of agent responses works
- [ ] ✅ Agent thoughts/reasoning visible during processing
- [ ] ✅ Messages display correctly (human vs AI)
- [ ] ✅ Connection status indicator works
- [ ] ✅ All frontend components compile without errors
- [ ] ✅ All backend routes respond correctly

---

## 🐛 Troubleshooting

### Backend won't start

```bash
# Check logs
docker compose logs backend

# Common issues:
# 1. Database not ready - wait for postgres healthcheck
# 2. Missing .env file - copy .env.example to .env
# 3. Invalid Python syntax - run: python -m py_compile backend/**/*.py
```

### Frontend won't build

```bash
# Check for TypeScript errors
cd frontend
npm run build

# Common issues:
# 1. Missing dependencies - run: npm install
# 2. Type errors - check src/types/index.ts
```

### WebSocket won't connect

```bash
# Verify backend is running socket_app (not just app)
docker compose logs backend | grep "socket_app"

# Should see: uvicorn api.main:socket_app

# Check CORS headers
curl -i http://localhost:8000/api/health

# Should include: access-control-allow-origin
```

### Tools not working

```bash
# Verify tools are registered at startup
docker compose logs backend | grep "Registered tool"

# Should see:
# ✓ Registered tool: calculator
# ✓ Registered tool: get_current_time
# ✓ Registered tool: create_note
# ✓ Registered tool: list_notes
```

### LangGraph errors

```bash
# Check agent configuration
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/agents/AGENT_ID

# Verify:
# - llm_config has valid provider and api_key
# - enabled_tools match registered tools
# - embedding_config is present
```

---

## 🎯 Performance Testing

### Load Testing with Apache Bench

```bash
# Test registration endpoint
ab -n 100 -c 10 -T application/json -p register.json \
  http://localhost:8000/api/auth/register

# Test chat endpoint (requires auth)
# Create a file with your token: auth_header.txt
ab -n 50 -c 5 -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:8000/api/sessions
```

### WebSocket Stress Test

Use a tool like `socket.io-client` to simulate multiple concurrent connections:

```javascript
// stress-test.js
const io = require('socket.io-client');

const NUM_CLIENTS = 50;
const clients = [];

for (let i = 0; i < NUM_CLIENTS; i++) {
  const socket = io('http://localhost:8000', {
    auth: { token: 'YOUR_TOKEN', sessionId: 'session-id' }
  });

  socket.on('connect', () => console.log(`Client ${i} connected`));
  clients.push(socket);
}
```

Run: `node stress-test.js`

---

## 🚀 Next Steps

Once all tests pass:

1. **Production Deployment:**
   - Update `SECRET_KEY` in .env
   - Use production database
   - Enable rate limiting
   - Set up monitoring (Prometheus/Grafana)

2. **Advanced Features:**
   - Add more tools (API integrations, Okta, etc.)
   - Implement RAG with document upload
   - Create custom agents for specific use cases
   - Add multi-modal support (images, audio)

3. **Security Hardening:**
   - Enable HTTPS
   - Set up API rate limiting
   - Implement audit logging
   - Add input sanitization

---

## 📞 Support

If you encounter issues:
1. Check this guide's Troubleshooting section
2. Review `COMPLETE_FIX.md` for CORS/password fixes
3. Check Docker logs: `docker compose logs -f`
4. Open an issue with full error logs

---

**Happy Testing! 🎉**

# 📋 Project Implementation Plan

## Overview

This document outlines the detailed implementation plan for the Agent-as-a-Service platform. The project is divided into 5 major phases, each building upon the previous one.

## Development Phases

### Phase 1: Backend Foundation & Configuration ✅ CURRENT
**Goal**: Establish the core backend architecture with database, API, and configuration systems.

#### 1.1 Project Structure Setup
- [x] Create project directory structure
- [ ] Initialize Python virtual environment
- [ ] Set up FastAPI application skeleton
- [ ] Configure SQLAlchemy with PostgreSQL
- [ ] Set up Alembic for migrations

#### 1.2 Database Models
**Files**: `backend/core/models/*.py`

- [ ] **User Model** (`user.py`)
  - Fields: id, email, hashed_password, full_name, role, created_at, updated_at
  - Relationships: chat_sessions

- [ ] **Agent Model** (`agent.py`)
  - Fields: id, name, description, system_prompt_template, llm_config (JSONB), embedding_config (JSONB), created_by, created_at, updated_at
  - Relationships: knowledge_bases (many-to-many), chat_sessions

- [ ] **KnowledgeBase Model** (`knowledge.py`)
  - Fields: id, name, description, vectorstore_config (JSONB), created_at, updated_at
  - Relationships: agents (many-to-many), documents

- [ ] **Document Model** (`knowledge.py`)
  - Fields: id, knowledge_base_id, filename, file_path, file_type, metadata (JSONB), uploaded_at

- [ ] **AgentKnowledgeLink Model** (`knowledge.py`)
  - Fields: agent_id, knowledge_base_id, created_at

- [ ] **ChatSession Model** (`chat.py`)
  - Fields: id, user_id, agent_id, title, created_at, updated_at, last_message_at
  - Relationships: messages, user, agent

- [ ] **ChatMessage Model** (`chat.py`)
  - Fields: id, session_id, message_type (enum: 'human', 'ai', 'system', 'tool', 'thought'), content (TEXT), metadata (JSONB), created_at
  - Indexes: session_id, created_at for fast retrieval

#### 1.3 Configuration Factories
**Files**: `backend/core/config/*.py`

- [ ] **LLM Factory** (`llm_factory.py`)
  ```python
  def get_llm_provider(config: dict) -> BaseChatModel:
      # Support: openai, gemini, ollama, anthropic
      # Return configured LLM instance
  ```

- [ ] **Embedding Factory** (`embedding_factory.py`)
  ```python
  def get_embedding_model(config: dict) -> Embeddings:
      # Support: openai, gemini, ollama, huggingface
      # Return configured embedding model
  ```

- [ ] **Vector Store Factory** (`vectorstore_factory.py`)
  ```python
  def get_vectorstore(config: dict, collection_name: str) -> VectorStore:
      # Support: chromadb, weaviate, pinecone
      # Return configured vector store
  ```

#### 1.4 Core API Endpoints
**Files**: `backend/api/routes/*.py`

- [ ] **Authentication** (`auth.py`)
  - POST `/api/auth/register`
  - POST `/api/auth/login`
  - POST `/api/auth/refresh`
  - GET `/api/auth/me`

- [ ] **Session Management** (`sessions.py`)
  - POST `/api/sessions` - Create new chat session
  - GET `/api/sessions` - List user's sessions
  - GET `/api/sessions/{session_id}` - Get session with messages
  - DELETE `/api/sessions/{session_id}` - Delete session
  - PATCH `/api/sessions/{session_id}` - Update session (e.g., title)

- [ ] **Health & Monitoring** (`health.py`)
  - GET `/api/health`
  - GET `/api/metrics`

### Phase 2: Agent Core (LangGraph) 🎯
**Goal**: Implement the agent reasoning engine with Human-in-the-Loop.

#### 2.1 Agent State Definition
**File**: `backend/agents/state.py`

```python
class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    user_id: str
    agent_id: str
    session_id: str
    agent_config: dict  # LLM config, tools, personality
    tool_manifest: list[dict]  # Available tools
    needs_consent: bool
    consent_data: dict  # Tool name, args, description
    iteration: int  # Loop prevention
    rag_context: str  # Retrieved context from knowledge base
```

#### 2.2 LangGraph Nodes
**File**: `backend/agents/nodes.py`

- [ ] **load_state_node**
  - Load agent configuration from database
  - Load tool manifest
  - Initialize state with session context

- [ ] **reasoning_node**
  - Build dynamic prompt from system_prompt_template
  - Inject tool manifest, chat history, personality
  - Call LLM to decide: respond, call_tool, or use_rag
  - Track iteration count

- [ ] **rag_node**
  - Query vector store for relevant documents
  - Re-rank results using FlashRank or CrossEncoder
  - Add top 3-5 documents to rag_context
  - Return to reasoning with context

- [ ] **consent_check_node**
  - Inspect tool call from LLM
  - Check if tool is in "write-ops" list (from agent_config)
  - If write-op:
    - Set needs_consent=True
    - Set consent_data with tool details
    - Interrupt graph (return for user approval)
  - If read-op:
    - Continue to tool_executor_node

- [ ] **tool_executor_node**
  - Execute approved tool
  - Capture result or error
  - Add tool result to messages
  - Return to reasoning_node

#### 2.3 LangGraph Workflow
**File**: `backend/agents/graph.py`

```python
def create_agent_graph() -> StateGraph:
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("load_state", load_state_node)
    workflow.add_node("reasoning", reasoning_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("consent_check", consent_check_node)
    workflow.add_node("tool_executor", tool_executor_node)

    # Define edges
    workflow.set_entry_point("load_state")
    workflow.add_edge("load_state", "reasoning")

    # Conditional edges from reasoning
    workflow.add_conditional_edges(
        "reasoning",
        route_reasoning,  # Function to decide next step
        {
            "rag": "rag",
            "tool": "consent_check",
            "respond": END
        }
    )

    workflow.add_edge("rag", "reasoning")

    # Conditional edges from consent_check
    workflow.add_conditional_edges(
        "consent_check",
        route_consent,
        {
            "needs_approval": "interrupt",  # Pause and wait
            "approved": "tool_executor"
        }
    )

    workflow.add_edge("tool_executor", "reasoning")

    return workflow.compile(
        checkpointer=PostgresSaver(...),  # For state persistence
        interrupt_before=["consent_check"]  # Can interrupt here
    )
```

#### 2.4 Prompt Engineering
**File**: `backend/agents/prompts.py`

- [ ] Create system prompt template builder
- [ ] Include tool manifest in prompt
- [ ] Add conversation history formatter
- [ ] Implement ReAct prompt structure
- [ ] Add consent request templates

**Example System Prompt Template**:
```
You are {{agent_name}}, a {{agent_role}}.

You are conversational, helpful, and think step-by-step before acting.

## Your Capabilities

### Tools
You have access to the following tools:
{{tool_manifest}}

### Knowledge Base
You can search these knowledge bases:
{{knowledge_base_names}}

## Conversation Rules
1. Always greet naturally and review chat history for context
2. Think: Use your internal reasoning to plan your approach
3. Observe: Review results from tools or knowledge retrieval
4. React: Formulate responses based on observations
5. Consent: For write operations (create, update, delete), you MUST:
   - Explain what you plan to do
   - Ask "Do you approve this action? (Yes/No)"
   - Wait for explicit approval before proceeding

## Chat History
{{messages}}
```

### Phase 3: WebSocket & Real-time Communication 🔌
**Goal**: Build robust WebSocket handler with session recovery.

#### 3.1 Backend WebSocket Handler
**File**: `backend/websocket/handler.py`

- [ ] Set up Socket.IO with FastAPI
- [ ] Implement authentication middleware
- [ ] Handle connection/disconnection events
- [ ] Implement message streaming

**Events to Handle**:
- `connect`: Authenticate, join session room
- `disconnect`: Clean up resources
- `chat_message`: Process user message through agent graph
- `consent_response`: Resume agent after user approval/rejection
- `typing`: Broadcast typing indicators

**Events to Emit**:
- `token`: Streaming LLM tokens
- `agent_thought`: Internal reasoning steps
- `consent_required`: Request user approval
- `tool_result`: Tool execution results
- `error`: Error messages
- `end_of_stream`: Message complete

#### 3.2 Message Streaming Strategy

```python
async def stream_agent_response(session_id: str, user_message: str):
    # 1. Save user message to DB
    await save_message(session_id, "human", user_message)

    # 2. Stream agent processing
    async for chunk in agent_graph.astream({...}):
        if chunk.type == "llm_token":
            await sio.emit("token", {"data": chunk.content}, room=session_id)
        elif chunk.type == "thought":
            await sio.emit("agent_thought", {"data": chunk.content}, room=session_id)
        elif chunk.type == "consent_required":
            await sio.emit("consent_required", {"data": chunk.data}, room=session_id)
            # Graph is interrupted, wait for user response
            break

    # 3. Save AI response to DB
    await save_message(session_id, "ai", final_response)
    await sio.emit("end_of_stream", room=session_id)
```

#### 3.3 Session Recovery Mechanism

- [ ] Implement checkpointing in LangGraph
- [ ] Store graph state in PostgreSQL
- [ ] On reconnect: Load last graph state
- [ ] Resume from interruption point

### Phase 4: RAG Pipeline 📚
**Goal**: Build advanced RAG with semantic chunking and re-ranking.

#### 4.1 Document Ingestion
**File**: `backend/rag/ingestion.py`

- [ ] **File Loaders**
  - PDF: PyPDFLoader
  - DOCX: UnstructuredFileLoader
  - TXT/MD: TextLoader
  - HTML: BeautifulSoupLoader

- [ ] **Chunking Strategy**
  ```python
  class SemanticChunker:
      def __init__(self, embedding_model):
          self.splitter = RecursiveCharacterTextSplitter(
              chunk_size=1500,
              chunk_overlap=300,
              separators=["\n\n", "\n", ". ", " ", ""]
          )

      def chunk_document(self, document):
          # Split into semantic chunks
          # Add metadata (source, page, chunk_id)
          # Return list of Documents
  ```

- [ ] **Embedding & Storage**
  ```python
  async def ingest_document(kb_id: str, file_path: str):
      # 1. Load document
      # 2. Chunk semantically
      # 3. Generate embeddings
      # 4. Store in vector DB with kb_id as collection
      # 5. Update Document model in PostgreSQL
  ```

#### 4.2 Retrieval & Re-ranking
**File**: `backend/rag/retrieval.py`

```python
class AdvancedRetriever:
    def __init__(self, vectorstore, reranker):
        self.vectorstore = vectorstore
        self.reranker = reranker  # FlashRank or CrossEncoder

    async def retrieve(self, query: str, k: int = 10):
        # 1. Initial retrieval (k=10)
        docs = await self.vectorstore.similarity_search(query, k=k)

        # 2. Re-rank
        reranked = self.reranker.rerank(query, docs, top_n=5)

        # 3. Return top 5 most relevant
        return reranked
```

#### 4.3 Context Synthesis

- [ ] Build synthesis prompt for LLM
- [ ] Instruct LLM to synthesize, not just list
- [ ] Handle case when context doesn't contain answer

### Phase 5: Frontend & Admin UI 🎨
**Goal**: Build intuitive React UI with session recovery.

#### 5.1 Frontend Project Setup
**Directory**: `frontend/`

- [ ] Initialize React + TypeScript + Vite
- [ ] Install dependencies:
  - socket.io-client
  - zustand
  - react-router-dom
  - tailwindcss
  - shadcn/ui
  - axios

#### 5.2 State Management
**File**: `frontend/src/stores/chatStore.ts`

```typescript
interface ChatState {
  sessionId: string | null
  chatHistory: Message[]
  isStreaming: boolean
  currentThought: string
  consentRequest: ConsentRequest | null
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting'

  // Actions
  setSessionId: (id: string) => void
  addMessage: (msg: Message) => void
  appendToken: (token: string) => void
  setConsentRequest: (req: ConsentRequest) => void
  loadHistoryFromDB: (sessionId: string) => Promise<void>
}
```

#### 5.3 Session Recovery Logic
**File**: `frontend/src/hooks/useChatSession.ts`

```typescript
function useChatSession(sessionId?: string) {
  useEffect(() => {
    if (sessionId) {
      // 1. Check if history is loaded
      if (chatHistory.length === 0) {
        // 2. Fetch from backend
        loadHistoryFromDB(sessionId)
      }

      // 3. Connect WebSocket with session_id
      socket.auth = { token: authToken, sessionId }
      socket.connect()
    }
  }, [sessionId])

  // Handle reconnection
  useEffect(() => {
    socket.on('connect', () => {
      setConnectionStatus('connected')
      // Rejoin session room
      socket.emit('join_session', { sessionId })
    })

    socket.on('disconnect', () => {
      setConnectionStatus('disconnected')
    })
  }, [])
}
```

#### 5.4 Chat Interface Components
**Directory**: `frontend/src/components/chat/`

- [ ] **ChatContainer.tsx**
  - Main chat layout
  - Message list
  - Input box
  - Typing indicators

- [ ] **Message.tsx**
  - Render different message types (human, ai, system, tool)
  - Markdown support
  - Code highlighting

- [ ] **ConsentModal.tsx**
  - Display when agent needs approval
  - Show tool name, args, description
  - Approve/Reject buttons

- [ ] **ThinkingIndicator.tsx**
  - Show agent's reasoning process
  - Collapsible thought bubbles

#### 5.5 Admin UI Components
**Directory**: `frontend/src/components/admin/`

- [ ] **AgentManager.tsx**
  - List all agents
  - Create/Edit/Delete agents
  - Configure LLM, embeddings, tools

- [ ] **AgentForm.tsx**
  - Name, description inputs
  - System prompt template editor (Monaco Editor)
  - LLM config dropdown
  - Tool selection checkboxes
  - Knowledge base linking

- [ ] **KnowledgeBaseManager.tsx**
  - List knowledge bases
  - Create new KB
  - Upload documents
  - View ingestion status

- [ ] **DocumentUpload.tsx**
  - Drag-and-drop file upload
  - Progress indicators
  - Chunking preview

### Phase 6: Tools & Integrations 🔧
**Goal**: Build extensible tool system with Okta integration.

#### 6.1 Tool Registry
**File**: `backend/tools/registry.py`

```python
class ToolRegistry:
    def __init__(self):
        self.tools = {}

    def register(self, tool: BaseTool):
        self.tools[tool.name] = tool

    def get_tool(self, name: str) -> BaseTool:
        return self.tools.get(name)

    def get_manifest(self) -> list[dict]:
        return [tool.to_manifest() for tool in self.tools.values()]
```

#### 6.2 Base Tool Class
**File**: `backend/tools/base.py`

```python
class BaseTool:
    name: str
    description: str
    parameters: dict  # JSON Schema
    is_write_operation: bool = False

    async def execute(self, **kwargs) -> ToolResult:
        raise NotImplementedError

    def to_manifest(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
            "requires_consent": self.is_write_operation
        }
```

#### 6.3 Okta Integration Tools
**Directory**: `backend/tools/okta/`

- [ ] **list_users.py**
  ```python
  class ListOktaUsersTool(BaseTool):
      name = "list_okta_users"
      description = "List all users in Okta"
      is_write_operation = False
  ```

- [ ] **get_user.py**
  ```python
  class GetOktaUserTool(BaseTool):
      name = "get_okta_user"
      description = "Get details of a specific Okta user"
      is_write_operation = False
  ```

- [ ] **create_user.py**
  ```python
  class CreateOktaUserTool(BaseTool):
      name = "create_okta_user"
      description = "Create a new user in Okta"
      is_write_operation = True  # Requires consent!
  ```

- [ ] **deactivate_user.py**
  ```python
  class DeactivateOktaUserTool(BaseTool):
      name = "deactivate_okta_user"
      description = "Deactivate an Okta user"
      is_write_operation = True  # Requires consent!
  ```

### Phase 7: Deployment & DevOps 🚀

#### 7.1 Docker Configuration
- [ ] **Backend Dockerfile**
- [ ] **Frontend Dockerfile**
- [ ] **docker-compose.yml** (PostgreSQL, Backend, Frontend, ChromaDB)

#### 7.2 Environment Configuration
- [ ] Create `.env.example`
- [ ] Document all environment variables
- [ ] Set up secrets management

#### 7.3 Database Migrations
- [ ] Alembic migration scripts
- [ ] Seed data for testing

#### 7.4 CI/CD
- [ ] GitHub Actions workflows
- [ ] Automated testing
- [ ] Deployment pipeline

## Known Challenges & Solutions

### 1. WebSocket Reconnection Race Conditions
**Problem**: Browser reload causes lost messages or duplicate connections.

**Solution**:
- Use Socket.IO's built-in reconnection logic
- Implement idempotent message handlers
- Store session state in database, not memory
- On reconnect, fetch last N messages from DB

### 2. LangGraph Infinite Loops
**Problem**: Agent gets stuck in tool-calling loop.

**Solution**:
- Track iteration count in state
- Set recursion_limit in graph compilation
- Add timeout to graph execution
- Emit "thinking too long" warning to user after 30s

### 3. RAG Context Window Overflow
**Problem**: Too many chunks exceed LLM context limit.

**Solution**:
- Limit to top 3-5 re-ranked chunks
- Use larger chunk sizes (1500 chars) with overlap
- Implement context compression/summarization

### 4. Tool Consent UX
**Problem**: Interrupting graph and waiting for user is complex.

**Solution**:
- Use LangGraph's interrupt_before feature
- Store graph state in PostgreSQL checkpointer
- Resume graph after user response via separate WebSocket event

## Testing Strategy

### Unit Tests
- Database models (CRUD operations)
- Configuration factories (LLM, embedding, vectorstore)
- Tool execution (mock external APIs)
- RAG chunking and retrieval

### Integration Tests
- Full chat flow (user message → agent response)
- Human-in-the-Loop consent flow
- Session recovery after disconnect
- Multi-tenant data isolation

### E2E Tests
- Complete user journey (signup → create agent → chat)
- Admin workflows (create KB → upload docs → link to agent)
- Error scenarios (network failures, timeouts)

## Performance Targets

- **Chat Latency**: < 2s for first token
- **WebSocket Reconnect**: < 1s
- **RAG Retrieval**: < 500ms
- **Document Ingestion**: < 5s per MB
- **Concurrent Users**: Support 1000+ simultaneous chats

## Security Checklist

- [ ] JWT authentication with short expiry
- [ ] Refresh token rotation
- [ ] SQL injection prevention (SQLAlchemy ORM)
- [ ] XSS prevention (React auto-escaping)
- [ ] CORS configuration
- [ ] Rate limiting on all endpoints
- [ ] Input validation with Pydantic
- [ ] Audit logging for admin actions
- [ ] Multi-tenant data isolation
- [ ] Secrets in environment variables (never in code)

## Success Metrics

1. **Reliability**: 99.9% uptime, graceful error handling
2. **User Experience**: Natural conversations, clear consent requests
3. **Developer Experience**: Easy to add new tools, LLMs, or knowledge sources
4. **Performance**: Fast responses, smooth streaming
5. **Security**: Zero data leaks, comprehensive audit trail

---

**Next Steps**: Begin Phase 1 implementation with database models and configuration factories.

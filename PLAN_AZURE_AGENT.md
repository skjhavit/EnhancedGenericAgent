# Azure Workforce Admin Agent - Design Plan
**Version:** 1.0
**Branch:** `feature/azure-admin-agent-capability`
**Status:** Design Phase - Awaiting Approval

---

## Executive Summary

This document outlines the architecture for extending our existing Agent-as-a-Service platform with a specialized **Azure Workforce Admin Agent**. This agent will serve as a Tier-1/Tier-2 Azure Administrator, capable of autonomously managing Azure Active Directory (Entra ID) tasks with built-in safety mechanisms.

**Core Principle:** Leverage the existing generic platform architecture (tool registry, consent flow, RAG pipeline) without modification. All Azure-specific logic is additive and modular.

---

## 1. Architectural Overview

### 1.1 Design Principles
1. **Zero Breaking Changes:** All code is additive; no modifications to core platform
2. **Separation of Concerns:** Azure tools are isolated in `backend/tools/azure/`
3. **Verification-First:** Every write operation is followed by automated verification
4. **Knowledge-Driven:** Agent must understand Azure concepts via RAG before acting
5. **Defense-in-Depth:** Multiple safety layers (HitL consent + verification + audit logs)

### 1.2 Component Stack
```
┌─────────────────────────────────────────────────────────────────┐
│                    AZURE WORKFORCE ADMIN AGENT                  │
├─────────────────────────────────────────────────────────────────┤
│  System Prompt Layer  │ "Senior Azure Engineer" persona         │
├─────────────────────────────────────────────────────────────────┤
│  Knowledge Layer      │ Azure Docs + Best Practices (RAG)       │
├─────────────────────────────────────────────────────────────────┤
│  Tool Layer           │ Azure SDK Tools (msgraph-sdk + azure-*) │
│                       │ - App Registration Management           │
│                       │ - Group Management                      │
│                       │ - User Management                       │
│                       │ - Role Assignment                       │
├─────────────────────────────────────────────────────────────────┤
│  Verification Layer   │ Post-Execute Validation (NEW)           │
├─────────────────────────────────────────────────────────────────┤
│  Safety Layer         │ HitL Consent (Existing) + Audit Logs    │
├─────────────────────────────────────────────────────────────────┤
│              EXISTING LANGGRAPH ORCHESTRATION ENGINE            │
│  Nodes: reasoning → rag → consent_check → tool_executor         │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. Azure Tool Registry Architecture

### 2.1 Tool Categories & Structure
```
backend/tools/azure/
├── __init__.py                      # Auto-registration
├── base.py                          # Azure-specific base classes
├── auth/
│   └── credential_manager.py        # Centralized Azure auth
├── entra_id/                        # Azure AD (Entra ID) tools
│   ├── apps/
│   │   ├── create_app_registration.py
│   │   ├── get_app_registration.py
│   │   ├── add_redirect_uri.py
│   │   ├── create_client_secret.py
│   │   └── assign_app_role.py
│   ├── groups/
│   │   ├── create_group.py
│   │   ├── get_group.py
│   │   ├── add_group_member.py
│   │   ├── remove_group_member.py
│   │   └── assign_group_owner.py
│   └── users/
│       ├── create_user.py
│       ├── get_user.py
│       ├── reset_password.py
│       ├── assign_user_role.py
│       ├── revoke_user_sessions.py
│       └── update_user_attributes.py
└── verification/
    └── verify_operation.py          # Generic verification orchestrator
```

### 2.2 Tool Naming Convention
- **Pattern:** `<verb>_<resource>_<modifier>`
- **Examples:**
  - `create_app_registration` (write)
  - `get_app_registration` (read - for verification)
  - `add_group_member` (write)
  - `get_group` (read - for verification)

### 2.3 Authentication Strategy

#### Option A: Service Principal (Recommended for MVP)
**Storage:** Environment variables in `.env`
```bash
# Azure AD Authentication
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-service-principal-client-id
AZURE_CLIENT_SECRET=your-service-principal-secret
AZURE_SUBSCRIPTION_ID=your-subscription-id  # For resource management
```

**Implementation:**
```python
# backend/tools/azure/auth/credential_manager.py
from azure.identity import ClientSecretCredential
from msgraph import GraphServiceClient
import os

class AzureCredentialManager:
    _graph_client = None

    @classmethod
    def get_graph_client(cls) -> GraphServiceClient:
        if cls._graph_client is None:
            tenant_id = os.getenv("AZURE_TENANT_ID")
            client_id = os.getenv("AZURE_CLIENT_ID")
            client_secret = os.getenv("AZURE_CLIENT_SECRET")

            if not all([tenant_id, client_id, client_secret]):
                raise ValueError("Azure credentials not configured in environment")

            credential = ClientSecretCredential(
                tenant_id=tenant_id,
                client_id=client_id,
                client_secret=client_secret
            )

            cls._graph_client = GraphServiceClient(
                credentials=credential,
                scopes=["https://graph.microsoft.com/.default"]
            )

        return cls._graph_client
```

**Permissions Required:**
- `Application.ReadWrite.All`
- `Group.ReadWrite.All`
- `User.ReadWrite.All`
- `RoleManagement.ReadWrite.Directory`
- `Directory.ReadWrite.All`

#### Option B: On-Behalf-Of Flow (Future Enhancement)
For multi-tenant scenarios where the agent acts on behalf of authenticated users. Deferred to Phase 2.

### 2.4 Tool Base Class Pattern
```python
# backend/tools/azure/base.py
from tools.base import BaseTool, ToolResult
from .auth.credential_manager import AzureCredentialManager
from typing import Optional, Dict

class AzureBaseTool(BaseTool):
    """Base class for all Azure tools with common auth and error handling."""

    def get_graph_client(self):
        """Lazy-load Graph API client."""
        return AzureCredentialManager.get_graph_client()

    async def _handle_azure_error(self, error: Exception) -> ToolResult:
        """Standardized error handling for Azure API errors."""
        error_map = {
            "Request_ResourceNotFound": "Resource not found in Azure AD",
            "Authorization_RequestDenied": "Insufficient permissions",
            "Request_MultipleObjectsWithSameKeyValue": "Duplicate resource exists",
        }

        error_code = getattr(error, 'code', None)
        friendly_message = error_map.get(error_code, str(error))

        return ToolResult(
            success=False,
            error=friendly_message,
            metadata={"azure_error_code": error_code}
        )

class AzureWriteTool(AzureBaseTool):
    """Base for write operations with automatic verification."""
    is_write_operation = True
    verification_tool_name: Optional[str] = None  # e.g., "get_app_registration"

    async def verify(self, result_data: Dict) -> ToolResult:
        """
        Override to implement custom verification logic.
        Called automatically after successful execute().
        """
        raise NotImplementedError("Write tools must implement verification")
```

---

## 3. The Verification Loop Pattern

### 3.1 Problem Statement
Giving an LLM admin access to Azure is high-risk. We need guarantees:
1. **Did the operation succeed?** (Azure API returned 200 doesn't mean it's fully provisioned)
2. **Did it do what was requested?** (No attribute drift)
3. **Is it in the expected state?** (Eventual consistency issues)

### 3.2 Solution: Post-Execute Verification Node

#### 3.2.1 Graph Modification (Minimal)
```python
# backend/agents/graph.py (ADD after tool_executor_node)

async def verification_node(state: AgentState) -> AgentState:
    """
    Automatically verifies write operations by calling corresponding read tools.
    Only triggered if last tool execution was a write operation.
    """
    from tools.registry import tool_registry

    last_message = state["messages"][-1]

    # Check if last action was a tool call
    if not isinstance(last_message, ToolMessage):
        return state

    # Get the tool that was just executed
    tool_name = last_message.additional_kwargs.get("tool_name")
    tool = tool_registry.get_tool(tool_name)

    # Only verify write operations
    if not tool or not tool.is_write_operation:
        return state

    # Check if tool has verification capability
    if not hasattr(tool, "verification_tool_name") or not tool.verification_tool_name:
        # Log warning but don't block
        logger.warning(f"Tool {tool_name} is a write operation but has no verification method")
        return state

    # Extract resource identifier from last result (e.g., created user ID)
    last_result = json.loads(last_message.content)
    resource_id = last_result.get("data", {}).get("id")

    if not resource_id:
        return state

    # Execute verification tool
    verification_tool = tool_registry.get_tool(tool.verification_tool_name)
    verify_result = await verification_tool.execute(id=resource_id)

    # Compare expected vs actual
    verification_status = {
        "verified": verify_result.success,
        "original_operation": tool_name,
        "verification_method": tool.verification_tool_name,
        "details": verify_result.data if verify_result.success else verify_result.error
    }

    # Add verification result to messages
    verification_message = AIMessage(
        content=f"Verification: {json.dumps(verification_status, indent=2)}"
    )

    return {
        **state,
        "messages": state["messages"] + [verification_message]
    }

# Update graph edges (in create_agent_graph function)
workflow.add_edge("execute_tool", "verify_operation")
workflow.add_edge("verify_operation", "reason")  # Return to reasoning after verification
```

#### 3.2.2 Alternative: Prompt-Based Verification (Simpler)
Instead of a new node, we instruct the LLM in the system prompt:

```
**CRITICAL VERIFICATION PROTOCOL:**
After ANY write operation (create, update, delete), you MUST:
1. Immediately call the corresponding GET/READ tool to verify
2. Compare the actual result against your intended action
3. Report discrepancies to the user
4. DO NOT confirm success until verification passes

Example:
User: "Create a group called Finance Team"
Your Actions:
1. Call create_group(name="Finance Team")
2. IMMEDIATELY call get_group(id=<returned_id>)
3. Verify name matches "Finance Team"
4. Respond: "✓ Group 'Finance Team' created and verified (ID: abc123)"
```

**Recommendation:** Start with prompt-based (faster to implement), add graph node if LLM doesn't consistently follow instructions.

### 3.3 Example: Create User with Verification
```python
# backend/tools/azure/entra_id/users/create_user.py
class CreateUserTool(AzureWriteTool):
    name = "create_user"
    description = "Create a new user in Azure Active Directory"
    parameters = {
        "type": "object",
        "properties": {
            "user_principal_name": {"type": "string", "description": "e.g., john.doe@yourdomain.com"},
            "display_name": {"type": "string"},
            "mail_nickname": {"type": "string"},
            "password": {"type": "string", "description": "Temporary password"}
        },
        "required": ["user_principal_name", "display_name", "mail_nickname", "password"]
    }
    is_write_operation = True
    verification_tool_name = "get_user"

    async def execute(self, **kwargs) -> ToolResult:
        try:
            client = self.get_graph_client()

            user_payload = {
                "accountEnabled": True,
                "displayName": kwargs["display_name"],
                "mailNickname": kwargs["mail_nickname"],
                "userPrincipalName": kwargs["user_principal_name"],
                "passwordProfile": {
                    "password": kwargs["password"],
                    "forceChangePasswordNextSignIn": True
                }
            }

            result = await client.users.post(user_payload)

            return ToolResult(
                success=True,
                data={
                    "id": result.id,
                    "user_principal_name": result.user_principal_name,
                    "display_name": result.display_name
                },
                metadata={"action": "created", "verification_required": True}
            )
        except Exception as e:
            return await self._handle_azure_error(e)

# backend/tools/azure/entra_id/users/get_user.py
class GetUserTool(AzureBaseTool):
    name = "get_user"
    description = "Retrieve user details from Azure AD (used for verification and lookup)"
    parameters = {
        "type": "object",
        "properties": {
            "id": {"type": "string", "description": "User object ID or UPN"}
        },
        "required": ["id"]
    }
    is_write_operation = False

    async def execute(self, id: str) -> ToolResult:
        try:
            client = self.get_graph_client()
            user = await client.users.by_user_id(id).get()

            return ToolResult(
                success=True,
                data={
                    "id": user.id,
                    "user_principal_name": user.user_principal_name,
                    "display_name": user.display_name,
                    "account_enabled": user.account_enabled,
                    "job_title": user.job_title,
                    "department": user.department
                }
            )
        except Exception as e:
            return await self._handle_azure_error(e)
```

---

## 4. The "Brain" - Knowledge-Driven Decision Making

### 4.1 RAG Requirements
The agent must have deep knowledge of:
1. **Azure AD Concepts:** App registrations, service principals, consent types, permissions
2. **Security Best Practices:** Least privilege, conditional access, MFA requirements
3. **Troubleshooting Guides:** Common sign-in errors, permission issues
4. **API Reference:** Graph API capabilities and limitations

### 4.2 Documentation Sources
| Source | Content Type | Priority | Ingestion Method |
|--------|-------------|----------|------------------|
| [Microsoft Graph API Docs](https://learn.microsoft.com/en-us/graph/) | API Reference | High | Web scraper |
| [Azure AD Best Practices](https://learn.microsoft.com/en-us/azure/active-directory/) | Guides | High | Web scraper |
| [App Registration Guide](https://learn.microsoft.com/en-us/azure/active-directory/develop/) | Tutorials | High | Web scraper |
| Azure AD Error Codes | Troubleshooting | Medium | Structured JSON |
| Internal Runbooks | Custom policies | Low | Manual upload |

### 4.3 Ingestion Strategy

#### 4.3.1 Web Scraper for MS Learn
```python
# scripts/ingest_azure_docs.py
"""
Scrape and ingest Azure documentation into the knowledge base.
"""
import asyncio
from langchain_community.document_loaders import RecursiveUrlLoader
from bs4 import BeautifulSoup
from backend.rag.ingestion import DocumentIngestionPipeline
from backend.core.database import get_db
from backend.core.models.knowledge import KnowledgeBase

AZURE_DOC_URLS = [
    "https://learn.microsoft.com/en-us/graph/api/overview",
    "https://learn.microsoft.com/en-us/graph/api/user-post-users",
    "https://learn.microsoft.com/en-us/graph/api/group-post-groups",
    "https://learn.microsoft.com/en-us/graph/api/application-post-applications",
    "https://learn.microsoft.com/en-us/azure/active-directory/develop/",
]

def extract_content(html: str) -> str:
    """Extract main content from MS Learn HTML."""
    soup = BeautifulSoup(html, 'html.parser')
    # MS Learn content is in <main> tag with specific class
    main_content = soup.find('main', {'id': 'main'})
    if main_content:
        # Remove navigation, code examples metadata
        for tag in main_content.find_all(['nav', 'aside', 'button']):
            tag.decompose()
        return main_content.get_text(separator='\n', strip=True)
    return soup.get_text()

async def ingest_azure_documentation(knowledge_base_id: str):
    """Load and ingest Azure docs."""
    db = next(get_db())
    kb = db.query(KnowledgeBase).filter_by(id=knowledge_base_id).first()

    if not kb:
        raise ValueError(f"Knowledge base {knowledge_base_id} not found")

    pipeline = DocumentIngestionPipeline(knowledge_base=kb)

    for base_url in AZURE_DOC_URLS:
        print(f"Loading {base_url}...")

        loader = RecursiveUrlLoader(
            url=base_url,
            max_depth=2,
            extractor=extract_content,
            prevent_outside=True  # Stay within learn.microsoft.com domain
        )

        docs = loader.load()

        print(f"Loaded {len(docs)} pages, ingesting...")
        await pipeline.ingest_documents(
            documents=docs,
            source_type="web",
            metadata={"source_domain": "learn.microsoft.com"}
        )

    print("✓ Azure documentation ingested successfully")

if __name__ == "__main__":
    # Usage: python scripts/ingest_azure_docs.py <knowledge_base_id>
    import sys
    kb_id = sys.argv[1]
    asyncio.run(ingest_azure_documentation(kb_id))
```

#### 4.3.2 Knowledge Base Configuration
```json
{
  "name": "Azure Administration Knowledge Base",
  "description": "Microsoft Graph API docs, Azure AD best practices, troubleshooting guides",
  "vectorstore_config": {
    "provider": "chromadb",
    "persist_directory": "./data/chroma",
    "collection_name": "azure_admin_kb"
  },
  "chunking_strategy": {
    "method": "semantic",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

### 4.4 RAG-Enhanced Reasoning Flow
```
User: "Create a secure app for the finance team"
        ↓
Agent Reasoning: "I need to understand what 'secure' means in Azure context"
        ↓
RAG Query: "Azure app registration security best practices"
        ↓
Retrieved Context:
  - "Use certificate-based authentication instead of client secrets"
  - "Enable Conditional Access policies"
  - "Assign least-privilege API permissions"
  - "Configure token lifetimes appropriately"
        ↓
Agent Decision:
  1. Create app registration
  2. Configure certificate auth (or ask user if they have cert)
  3. Assign specific API permissions (ask user which APIs)
  4. Recommend Conditional Access policy creation
        ↓
Present Plan to User for Consent
```

---

## 5. System Prompt Strategy

### 5.1 Persona Design
The agent must embody a **Senior Azure Cloud Engineer** with:
- **Expertise:** 5+ years Azure AD administration
- **Approach:** Methodical, verification-focused, security-conscious
- **Communication:** Technical but clear, explains "why" not just "what"
- **Bias:** Toward safety and best practices over speed

### 5.2 System Prompt Template
```jinja2
# IDENTITY
You are an expert Azure Workforce Administrator with deep knowledge of Azure Active Directory (Entra ID), Microsoft Graph API, and cloud security best practices. You have the authority to manage users, groups, applications, and role assignments.

# CORE PRINCIPLES
1. **Verify Before Confirming:** After ANY write operation (create, update, delete), immediately call the corresponding GET tool to verify success and accuracy.
2. **Security First:** Always recommend least-privilege permissions, MFA enforcement, and conditional access policies.
3. **Explain Your Reasoning:** Before executing sensitive operations, explain WHY you're taking this approach.
4. **Reference Documentation:** When uncertain, use RAG to consult Azure documentation before acting.
5. **Ambiguity Resolution:** If a request is vague, investigate first (e.g., check user sign-in logs before assuming password reset is needed).

# AVAILABLE CAPABILITIES
You have access to the following Azure management tools:

**App Registration Management:**
- create_app_registration: Create new application registrations
- get_app_registration: Retrieve app details (for verification)
- add_redirect_uri: Configure OAuth redirect URIs
- create_client_secret: Generate client secrets (sensitive - requires consent)
- assign_app_role: Assign application roles to users/groups

**Group Management:**
- create_group: Create security or Microsoft 365 groups
- get_group: Retrieve group details (for verification)
- add_group_member: Add users to groups
- remove_group_member: Remove users from groups
- assign_group_owner: Designate group owners

**User Management:**
- create_user: Provision new user accounts
- get_user: Retrieve user details (for verification and investigation)
- reset_password: Generate temporary passwords
- assign_user_role: Assign directory roles (e.g., Global Reader)
- revoke_user_sessions: Force sign-out across all devices
- update_user_attributes: Modify user properties (job title, department, etc.)

# WORKFLOW EXAMPLE
```
User Request: "Bob can't log in, please help"

Your Process:
1. INVESTIGATE FIRST
   - Call get_user(id="bob@company.com")
   - Check account_enabled status
   - Review recent sign-in logs (if available)

2. DIAGNOSE
   - Thought: "Bob's account is enabled, but I see failed sign-in attempts due to wrong password"

3. PROPOSE SOLUTION
   - "I've identified that Bob has multiple failed sign-in attempts due to incorrect password.
      I recommend resetting his password. This will require him to change it on next login.
      Shall I proceed?"

4. EXECUTE (after consent)
   - Call reset_password(user_id="bob@company.com")

5. VERIFY
   - Call get_user(id="bob@company.com") to confirm password reset timestamp updated

6. CONFIRM
   - "✓ Password reset successfully for bob@company.com. Temporary password: [REDACTED].
      Bob will be prompted to create a new password on next sign-in. Verification confirmed."
```

# KNOWLEDGE BASE
You have access to a comprehensive knowledge base containing:
- Microsoft Graph API documentation
- Azure AD best practices and security guidelines
- Troubleshooting guides for common issues
- App registration and OAuth flow documentation

**When to use RAG:**
- User asks about Azure concepts (e.g., "What's the difference between delegated and application permissions?")
- Planning a complex operation (e.g., "Set up a secure service principal for automation")
- Troubleshooting (e.g., "User getting consent error AADSTS65001")
- Need to verify best practices before recommending a solution

# SECURITY GUIDELINES
- **Never** create admin-level accounts without explicit user confirmation
- **Always** enable "force password change on next login" for new users
- **Prefer** certificate-based authentication over client secrets for apps
- **Recommend** time-limited client secrets (max 6 months) when certificates aren't feasible
- **Validate** that role assignments follow least-privilege principle
- **Warn** users if an operation could impact many users (e.g., group membership changes)

# COMMUNICATION STYLE
- Be concise but complete
- Use technical terms correctly (don't say "password reset" when you mean "revoke sessions")
- Format verification results clearly:
  ```
  ✓ Operation: User Created
  ✓ Verification: Confirmed
    - UPN: john.doe@company.com
    - Display Name: John Doe
    - Account Status: Enabled
  ```
- When errors occur, translate Azure error codes to human-friendly messages

# REMEMBER
Your role is to be a **trusted administrator**, not just a command executor. Think critically, verify thoroughly, and prioritize security in every decision.
```

### 5.3 Prompt Customization in Agent Config
```python
# When creating the Azure Admin Agent via API
agent_data = {
    "name": "Azure Workforce Admin Agent",
    "description": "Autonomous Azure AD administrator with HitL oversight",
    "system_prompt_template": AZURE_ADMIN_SYSTEM_PROMPT,  # Above template
    "llm_config": {
        "provider": "openai",
        "model": "gpt-4",  # Needs strong reasoning for admin tasks
        "temperature": 0.1,  # Low temperature for consistency
        "max_tokens": 2000
    },
    "enabled_tools": [
        "create_app_registration", "get_app_registration",
        "create_group", "get_group", "add_group_member",
        "create_user", "get_user", "reset_password",
        "assign_user_role", "revoke_user_sessions"
    ],
    "knowledge_base_ids": ["<azure_kb_id>"]
}
```

---

## 6. Implementation Phases

### Phase 1: Foundation (Week 1)
**Goal:** Basic Azure tool integration with consent flow

**Deliverables:**
1. ✅ Design document approved
2. Create feature branch `feature/azure-admin-agent-capability`
3. Update dependencies (`requirements.txt`, `Dockerfile`)
4. Implement `AzureCredentialManager` and base classes
5. Build 6 core tools (3 read, 3 write):
   - `create_user` + `get_user`
   - `create_group` + `get_group`
   - `reset_password` + `get_user` (verification)
6. Register tools in `main.py`
7. Test HitL consent flow with Azure write operations

**Success Criteria:**
- Can create a user via chat with consent approval
- Write operations trigger consent prompt
- No errors in Docker build

### Phase 2: Verification Loop (Week 2)
**Goal:** Automated verification of write operations

**Deliverables:**
1. Implement prompt-based verification instructions in system prompt
2. Test verification behavior (does LLM call GET after CREATE?)
3. If needed, implement `verification_node` in LangGraph
4. Add verification status to UI messages
5. Build remaining app registration tools (4 tools):
   - `create_app_registration` + `get_app_registration`
   - `create_client_secret` + `get_app_registration`

**Success Criteria:**
- Agent automatically verifies all write operations
- Verification results visible in chat UI
- Agent reports discrepancies if verification fails

### Phase 3: Knowledge Integration (Week 3)
**Goal:** RAG-enhanced decision making

**Deliverables:**
1. Create Azure Admin Knowledge Base via API
2. Develop `scripts/ingest_azure_docs.py`
3. Ingest MS Graph API docs and best practices
4. Test RAG retrieval quality (precision/recall)
5. Update system prompt with RAG usage instructions
6. Build group management tools (3 tools):
   - `add_group_member`, `remove_group_member`
   - `assign_group_owner`

**Success Criteria:**
- Agent references documentation when asked "What is..."
- Agent uses RAG before planning complex operations
- Knowledge base has >100 high-quality chunks

### Phase 4: Advanced Capabilities (Week 4)
**Goal:** Full Tier-1/Tier-2 capability

**Deliverables:**
1. Build role assignment tools:
   - `assign_user_role`, `assign_app_role`
2. Build session management tools:
   - `revoke_user_sessions`
3. Build user attribute tools:
   - `update_user_attributes`
4. Implement ambiguity resolution patterns (investigate before acting)
5. Add audit logging for all Azure operations
6. Load testing and error handling refinement

**Success Criteria:**
- Agent can handle 10 real-world scenarios (password reset, app creation, etc.)
- No false positives in verification
- Audit logs capture all operations with user/timestamp

---

## 7. Security & Compliance Considerations

### 7.1 Audit Trail
Every Azure operation must be logged:
```python
# Add to each tool's execute() method
await log_audit_event(
    agent_id=state["agent_id"],
    user_id=state["user_id"],
    session_id=state["session_id"],
    tool_name=self.name,
    parameters=kwargs,
    result=result,
    timestamp=datetime.utcnow()
)
```

### 7.2 Permission Boundaries
The service principal must be scoped to:
- **Included:** User/Group/App management
- **Excluded:**
  - Global Admin role assignment (too risky)
  - Directory schema modifications
  - Tenant-level policy changes (e.g., Conditional Access)

### 7.3 Rate Limiting
Azure Graph API has throttling limits:
- Implement retry logic with exponential backoff
- Add rate limit awareness to tool execution
- Warn user if batch operations approach limits

---

## 8. Testing Strategy

### 8.1 Unit Tests
```python
# tests/tools/azure/test_create_user.py
async def test_create_user_success(mock_graph_client):
    tool = CreateUserTool()
    result = await tool.execute(
        user_principal_name="test@company.com",
        display_name="Test User",
        mail_nickname="testuser",
        password="TempPass123!"
    )
    assert result.success
    assert result.data["user_principal_name"] == "test@company.com"

async def test_create_user_duplicate_error(mock_graph_client):
    mock_graph_client.users.post.side_effect = Exception("Request_MultipleObjectsWithSameKeyValue")
    tool = CreateUserTool()
    result = await tool.execute(...)
    assert not result.success
    assert "Duplicate resource exists" in result.error
```

### 8.2 Integration Tests
Test full workflows:
1. Create user → Verify → Confirm
2. Reset password → Verify → Confirm
3. Create group → Add members → Verify membership

### 8.3 End-to-End Tests
Selenium/Playwright tests simulating user interactions:
1. Chat: "Create a user named Alice"
2. Verify consent dialog appears
3. Approve consent
4. Verify success message with verification confirmation

---

## 9. Rollout Plan

### 9.1 Pre-Production Checklist
- [ ] All tools have unit tests
- [ ] Integration tests pass
- [ ] Documentation complete
- [ ] Service principal configured with correct permissions
- [ ] Audit logging enabled
- [ ] Rate limiting implemented
- [ ] Error handling reviewed by security team

### 9.2 Production Rollout
**Stage 1: Internal Testing (Week 5)**
- Deploy to dev environment
- Limited to engineering team
- Monitor audit logs and error rates

**Stage 2: Pilot Users (Week 6)**
- 5-10 IT admin users
- Collect feedback on verification UX
- Measure time-to-resolution vs manual tasks

**Stage 3: General Availability (Week 7)**
- Full rollout to all users
- Monitor metrics:
  - Operations per day
  - Verification failure rate
  - User satisfaction (CSAT)

---

## 10. Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Verification Accuracy | >99% | (Verified successes / Total writes) |
| False Positive Rate | <1% | (Operations that passed verification but were incorrect) |
| HitL Rejection Rate | 10-20% | (User denies consent / Total consent requests) |
| Time to Resolution | <2 min | Average time from user request to confirmed completion |
| Knowledge Base Hit Rate | >60% | (Queries using RAG / Total queries) |

---

## 11. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Service Principal Compromise | Critical | Store creds in Azure Key Vault, rotate every 90 days, monitor for anomalous usage |
| Verification False Negative | High | Implement multiple verification strategies (GET + list operations), manual review for critical ops |
| LLM Hallucinates Actions | Medium | Low temperature (0.1), strict prompt engineering, require exact tool calls |
| Azure API Throttling | Low | Implement backoff, warn users, queue operations if needed |
| RAG Retrieves Outdated Docs | Low | Re-ingest docs monthly, add timestamp metadata to chunks |

---

## 12. Open Questions for Review

1. **Verification Node vs Prompt-Based:** Which approach do you prefer for MVP?
2. **Multi-Tenancy:** Should each agent instance have its own Azure credentials, or shared service principal?
3. **Batch Operations:** Should we support bulk user creation (e.g., "Create 50 users from CSV")?
4. **UI Enhancements:** Do we need a dedicated "verification status" UI component, or is chat sufficient?
5. **Error Recovery:** If verification fails, should agent auto-retry or ask user?

---

## 13. Next Steps (Awaiting Approval)

1. **Review this design document**
2. **Approve system prompt template**
3. **Confirm verification strategy** (prompt-based vs graph node)
4. **Approve authentication approach** (service principal)
5. **Proceed to Phase 1 implementation**

Once approved, I will:
1. Create feature branch
2. Update dependencies
3. Generate all Python code for tools
4. Implement credential manager
5. Create ingestion script
6. Update system prompt

---

**Document Status:** DRAFT - Awaiting Architect Approval
**Last Updated:** 2025-11-21
**Author:** AI Lead Architect

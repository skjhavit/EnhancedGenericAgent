# Azure Admin Agent Knowledge Base

## Overview

This directory contains curated knowledge base documents optimized for RAG (Retrieval-Augmented Generation) to enhance the Azure Workforce Admin Agent's understanding of Azure AD concepts and operations.

## What's Included

### 01_user_management.md
**Topics covered**:
- Azure AD user creation, retrieval, updates
- Password policies and reset procedures
- User account types (cloud-only vs synced)
- Verification best practices
- Common user management scenarios
- Troubleshooting user-related issues

**Use cases**:
- Agent needs to understand how to create users correctly
- User asks "What's a User Principal Name?"
- Agent troubleshooting "User can't log in" scenarios

---

### 02_group_management.md
**Topics covered**:
- Security groups vs Microsoft 365 groups
- Group creation and configuration
- Group membership management (add/remove members)
- Owners vs members
- Access control patterns
- Dynamic groups

**Use cases**:
- Agent deciding whether to create security or M365 group
- User asks "What's the difference between group types?"
- Agent explaining why to use groups for permissions

---

### 03_app_registration_authentication.md
**Topics covered**:
- App registrations (what they are, why they exist)
- Application ID vs Object ID
- Sign-in audience types (single tenant, multi-tenant, public)
- Client secrets vs certificates
- Redirect URIs (web vs SPA)
- OAuth 2.0 flows
- Application vs delegated permissions

**Use cases**:
- Agent creating secure app registration for user
- User asks "What's a client secret?"
- Agent explaining OAuth redirect URIs
- Agent deciding single-tenant vs multi-tenant

---

### 04_common_errors_troubleshooting.md
**Topics covered**:
- Authentication errors (AADSTS codes)
- Permission errors (Authorization_RequestDenied)
- Rate limiting and throttling
- User/group specific errors
- Debugging strategies
- Error resolution workflows

**Use cases**:
- User reports error "AADSTS50020"
- Agent encounters "Insufficient privileges" error
- Agent needs to explain why operation failed
- Agent troubleshooting permission issues

---

## Document Structure

Each document is optimized for RAG with:

✅ **Clear section headers**: Easy semantic chunking
✅ **Keyword-rich content**: Includes terms users might search for
✅ **Practical examples**: Real-world scenarios and code snippets
✅ **Q&A style**: Natural language questions and answers
✅ **Cross-references**: Links between related concepts
✅ **Consistent formatting**: Predictable structure for LLM parsing

## Using These Documents

### Method 1: Automated Ingestion Script

Use the provided ingestion script to load all documents at once:

```bash
# Create knowledge base via API first, get the ID
KNOWLEDGE_BASE_ID="your-kb-id-here"

# Run ingestion script (ingests all .md files from this directory)
python scripts/ingest_azure_knowledge_base.py $KNOWLEDGE_BASE_ID
```

### Method 2: Manual Upload via API

```bash
# Upload individual documents
curl -X POST http://localhost:8000/api/knowledge-bases/{kb_id}/documents \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@knowledge_base/azure/01_user_management.md"
```

### Method 3: Web Scraping (Alternative)

The original `scripts/ingest_azure_docs.py` scrapes live Microsoft documentation. Use these local documents for:
- Faster ingestion (no web scraping)
- Offline development
- Customized content specific to your tools

---

## Chunking Strategy

These documents are designed to work with semantic chunking:

**Recommended settings**:
```json
{
  "chunking_strategy": {
    "method": "semantic",
    "chunk_size": 1000,
    "chunk_overlap": 200
  }
}
```

**Why this works**:
- Each section is self-contained
- Headers provide context for chunking
- Examples include full context
- Cross-references maintain coherence

---

## RAG Query Examples

**User**: "Create a user for John Doe"

**Agent RAG query**: "Azure AD user creation requirements password policy"

**Retrieved chunks**:
- Required attributes for user creation
- Password profile best practices
- Force password change on first login

---

**User**: "What's the difference between security groups and M365 groups?"

**Agent RAG query**: "security group vs Microsoft 365 group differences"

**Retrieved chunks**:
- Group types comparison table
- When to use each type
- Mail enabled vs security enabled

---

**User**: "I'm getting error AADSTS50020"

**Agent RAG query**: "AADSTS50020 error solution"

**Retrieved chunks**:
- Error explanation
- Cause (external user accessing single-tenant app)
- Solutions (invite as guest, change to multi-tenant)

---

## Extending the Knowledge Base

### Adding New Documents

When adding new documents, follow this structure:

```markdown
# Topic Title

## Overview
High-level introduction (2-3 paragraphs)

## Key Concepts
Define important terms

## Detailed Sections
Break down into specific topics with clear headers

## Use Cases / Scenarios
Practical examples

## Common Errors
Related troubleshooting

## References
Links to official documentation

---

**Keywords**: comma, separated, search, terms
```

### Topics to Consider Adding

- **Role-based access control (RBAC)**
- **Conditional Access policies**
- **Azure AD B2B (guest users)**
- **Azure AD B2C (customer identity)**
- **Privileged Identity Management (PIM)**
- **Multi-factor authentication (MFA)**
- **Single sign-on (SSO) configuration**
- **Azure AD Connect (hybrid identity)**

---

## Maintenance

### Updating Documents

As Azure AD/Microsoft Entra ID evolves:

1. **Review quarterly**: Check for API changes
2. **Update examples**: Ensure code snippets still work
3. **Add new features**: Document new capabilities
4. **Deprecation notices**: Mark deprecated features
5. **Re-ingest**: After updates, re-ingest to knowledge base

### Version Tracking

Each document includes:
- Last updated date (at bottom)
- Version number (if major changes)
- Keywords for search optimization

---

## Knowledge Base Configuration

### Creating the Knowledge Base

```bash
# Via API
curl -X POST http://localhost:8000/api/knowledge-bases \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Azure Administration Knowledge Base",
    "description": "Curated Azure AD documentation for the Azure Workforce Admin Agent",
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
  }'
```

### Linking to Azure Admin Agent

When creating your Azure Admin Agent, include the knowledge base ID:

```json
{
  "name": "Azure Workforce Admin",
  "description": "Autonomous Azure AD administrator with expert knowledge",
  "enabled_tools": [
    "create_user", "get_user", "reset_password",
    "create_group", "get_group", "add_group_member",
    "create_app_registration", "get_app_registration",
    "add_redirect_uri", "create_client_secret"
  ],
  "knowledge_base_ids": ["your-azure-kb-id-here"],
  "system_prompt_template": "{{USE AZURE_ADMIN_SYSTEM_PROMPT.md}}"
}
```

---

## Testing RAG Quality

### Test Queries

After ingestion, test retrieval quality:

```python
# Test 1: Specific fact retrieval
query = "What password policy applies when creating Azure AD users?"
# Should retrieve password complexity requirements

# Test 2: Concept explanation
query = "Explain difference between delegated and application permissions"
# Should retrieve permissions section with examples

# Test 3: Troubleshooting
query = "Why am I getting insufficient privileges error?"
# Should retrieve authorization error troubleshooting

# Test 4: Procedural knowledge
query = "How do I verify a user was created successfully?"
# Should retrieve verification best practices
```

### Metrics to Track

- **Retrieval precision**: Are retrieved chunks relevant?
- **Recall**: Does the query find all relevant information?
- **Answer quality**: Can the agent answer questions correctly?
- **Missing knowledge**: Track questions the agent can't answer

---

## Best Practices

### For Optimal RAG Performance

1. **Specific queries**: Agent should create focused search queries
2. **Context inclusion**: Retrieved chunks should have enough context
3. **Redundancy**: Important concepts appear in multiple documents
4. **Examples**: Include practical examples in every topic
5. **Keywords**: Use terms users naturally search for

### System Prompt Instructions

Include in your agent's system prompt:

```
When uncertain about Azure AD concepts:
1. Query knowledge base with specific terms
2. Use retrieved context to inform your answer
3. Cite which document you referenced (if relevant)
4. If knowledge base doesn't have the answer, say so
```

---

## File Format Requirements

- **Format**: Markdown (.md)
- **Encoding**: UTF-8
- **Size**: <100KB per file (for optimal chunking)
- **Images**: Not supported (text only)
- **Links**: External links OK, will be preserved in chunks

---

## Support

If you have questions or want to contribute:

1. **Issues**: Report missing or incorrect information
2. **Additions**: Suggest new topics to cover
3. **Improvements**: Propose better explanations or examples

---

**Last Updated**: 2025-11-21
**Version**: 1.0
**Documents**: 4 core topics
**Total Content**: ~15,000 words optimized for RAG

"""LangGraph agent state definition."""

from typing import TypedDict, Annotated, List, Dict, Any
from langchain_core.messages import BaseMessage, add_messages


class AgentState(TypedDict):
    """
    State for the LangGraph agent workflow.

    This state is passed between nodes and contains all necessary context
    for the agent to reason, use tools, and interact with the user.
    """

    # Chat messages (managed by LangChain's add_messages reducer)
    messages: Annotated[List[BaseMessage], add_messages]

    # Session context
    user_id: str
    agent_id: str
    session_id: str

    # Agent configuration
    agent_config: Dict[str, Any]  # Contains LLM config, personality, etc.
    tool_manifest: List[Dict[str, Any]]  # Available tools
    knowledge_base_ids: List[str]  # Linked knowledge bases

    # RAG context
    rag_context: str  # Retrieved context from knowledge base

    # Human-in-the-Loop consent
    needs_consent: bool
    consent_data: Dict[str, Any]  # Tool name, args, description

    # Loop prevention
    iteration: int  # Track number of reasoning loops
    max_iterations: int  # Maximum allowed iterations

    # Agent decision
    next_action: str  # 'respond', 'use_tool', 'use_rag', 'ask_consent'

    # Error handling
    error: str | None  # Error message if something goes wrong

"""LangGraph workflow definition for the agent."""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver

from agents.state import AgentState
from agents.nodes import (
    load_state_node,
    reasoning_node,
    rag_node,
    consent_check_node,
    tool_executor_node,
    route_from_reasoning,
    route_from_consent,
)
from core.database import DATABASE_URL


def create_agent_graph(enable_checkpointing: bool = True) -> StateGraph:
    """
    Create the LangGraph agent workflow.

    This graph implements a ReAct (Reasoning + Acting) pattern with:
    - Dynamic reasoning
    - RAG integration
    - Tool execution
    - Human-in-the-Loop consent

    Args:
        enable_checkpointing: Whether to enable state persistence

    Returns:
        Compiled StateGraph
    """
    # Create workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("load_state", load_state_node)
    workflow.add_node("reason", reasoning_node)
    workflow.add_node("rag", rag_node)
    workflow.add_node("check_consent", consent_check_node)
    workflow.add_node("execute_tool", tool_executor_node)

    # Set entry point
    workflow.set_entry_point("load_state")

    # Define edges
    workflow.add_edge("load_state", "reason")

    # Conditional routing from reasoning
    workflow.add_conditional_edges(
        "reason",
        route_from_reasoning,
        {
            "reason": "reason",  # Loop back (with iteration check)
            "use_rag": "rag",
            "check_consent": "check_consent",
            "respond": END,
        }
    )

    # RAG flows back to reasoning
    workflow.add_edge("rag", "reason")

    # Conditional routing from consent check
    workflow.add_conditional_edges(
        "check_consent",
        route_from_consent,
        {
            "wait_consent": END,  # Interrupt and wait for user approval
            "execute_tool": "execute_tool",
        }
    )

    # Tool execution flows back to reasoning
    workflow.add_edge("execute_tool", "reason")

    # Compile with checkpointing if enabled
    if enable_checkpointing:
        # PostgreSQL checkpointer for state persistence
        checkpointer = PostgresSaver.from_conn_string(DATABASE_URL)
        return workflow.compile(
            checkpointer=checkpointer,
            interrupt_before=["check_consent"],  # Can interrupt here for consent
        )
    else:
        return workflow.compile()


# Global agent graph instance
agent_graph = create_agent_graph(enable_checkpointing=True)


async def run_agent(
    user_message: str,
    session_id: str,
    user_id: str,
    agent_config: dict,
    tool_manifest: list,
    knowledge_base_ids: list = None,
):
    """
    Run the agent for a single turn.

    Args:
        user_message: User's input message
        session_id: Session ID for checkpointing
        user_id: User ID
        agent_config: Agent configuration
        tool_manifest: List of available tools
        knowledge_base_ids: List of knowledge base IDs

    Yields:
        State updates as the agent progresses
    """
    from langchain_core.messages import HumanMessage

    # Initial state
    initial_state = AgentState(
        messages=[HumanMessage(content=user_message)],
        user_id=user_id,
        agent_id=agent_config.get("id"),
        session_id=session_id,
        agent_config=agent_config,
        tool_manifest=tool_manifest,
        knowledge_base_ids=knowledge_base_ids or [],
        rag_context="",
        needs_consent=False,
        consent_data={},
        iteration=0,
        max_iterations=10,
        next_action="reason",
        error=None,
    )

    # Configuration for graph execution
    config = {
        "configurable": {
            "thread_id": session_id,  # For checkpointing
        }
    }

    # Stream the graph execution
    async for event in agent_graph.astream(initial_state, config):
        yield event


async def resume_agent_after_consent(
    session_id: str,
    approved: bool,
):
    """
    Resume agent execution after user provides consent.

    Args:
        session_id: Session ID
        approved: Whether user approved the action

    Yields:
        State updates as the agent resumes
    """
    from langchain_core.messages import HumanMessage

    # Configuration for resuming
    config = {
        "configurable": {
            "thread_id": session_id,
        }
    }

    # Get the current state from checkpoint
    state = await agent_graph.aget_state(config)

    if approved:
        # User approved, proceed to tool execution
        state.values["next_action"] = "execute_tool"
        state.values["messages"].append(
            HumanMessage(content="Approved")
        )
    else:
        # User rejected, go back to reasoning
        state.values["next_action"] = "reason"
        state.values["needs_consent"] = False
        state.values["consent_data"] = {}
        state.values["messages"].append(
            HumanMessage(content="Rejected - please suggest an alternative")
        )

    # Resume execution
    async for event in agent_graph.astream(None, config):
        yield event

"""LangGraph workflow definition for the agent."""

from langgraph.graph import StateGraph, END

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
        try:
            # Try to use MemorySaver for checkpointing
            from langgraph.checkpoint.memory import MemorySaver
            checkpointer = MemorySaver()
            # Don't use interrupt_before - let the graph naturally interrupt
            # when route_from_consent returns "wait_consent" -> END
            return workflow.compile(checkpointer=checkpointer)
        except ImportError:
            # Fallback to no checkpointing if MemorySaver not available
            print("Warning: MemorySaver not available, running without checkpointing")
            return workflow.compile()
    else:
        return workflow.compile()


# Global agent graph instance (checkpointing enabled for consent flow)
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

    print(f"[DEBUG] Resuming agent after consent. session_id={session_id}, approved={approved}")

    # Get the current state from checkpoint
    current_state = await agent_graph.aget_state(config)
    print(f"[DEBUG] Current state next: {current_state.next}")
    print(f"[DEBUG] Current state values keys: {list(current_state.values.keys())}")

    # Prepare the update based on user's decision
    if approved:
        # User approved, update state to proceed to tool execution
        updates = {
            "next_action": "execute_tool",
            "needs_consent": False,
        }
        print(f"[DEBUG] User approved - updating state with: {updates}")
    else:
        # User rejected, go back to reasoning
        updates = {
            "next_action": "reason",
            "needs_consent": False,
            "consent_data": {},
        }
        print(f"[DEBUG] User rejected - updating state with: {updates}")

    # Update the checkpoint state with our changes
    await agent_graph.aupdate_state(config, updates)
    print(f"[DEBUG] State updated, now resuming execution...")

    # Resume execution from the updated checkpoint
    async for event in agent_graph.astream(None, config):
        print(f"[DEBUG] Resume event: {list(event.keys())}")
        yield event

"""LangGraph nodes for the agent workflow."""

from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.language_models.chat_models import BaseChatModel
import json

from agents.state import AgentState
from agents.prompts import build_system_prompt, build_consent_request
from core.config import get_llm_provider
from tools.registry import tool_registry


async def load_state_node(state: AgentState) -> AgentState:
    """
    Entry node: Load agent configuration and initialize state.

    This node is called once at the start of a conversation turn.
    """
    # Initialize iteration counter
    if "iteration" not in state or state["iteration"] is None:
        state["iteration"] = 0

    # Set max iterations
    if "max_iterations" not in state or state["max_iterations"] is None:
        state["max_iterations"] = 10

    # Initialize flags
    if "needs_consent" not in state:
        state["needs_consent"] = False

    if "consent_data" not in state:
        state["consent_data"] = {}

    if "rag_context" not in state:
        state["rag_context"] = ""

    if "error" not in state:
        state["error"] = None

    state["next_action"] = "reason"

    return state


async def reasoning_node(state: AgentState) -> AgentState:
    """
    Core reasoning node: LLM decides what to do next.

    This node:
    1. Builds the system prompt with context
    2. Calls the LLM
    3. Interprets the response
    4. Decides next action (respond, use_tool, use_rag)
    """
    # Increment iteration counter
    state["iteration"] += 1

    # Check for infinite loops
    if state["iteration"] > state["max_iterations"]:
        state["error"] = "Maximum reasoning iterations exceeded. Please simplify your request."
        state["next_action"] = "respond"
        state["messages"].append(
            AIMessage(content="I apologize, but I've been thinking for too long. Could you please rephrase your request or break it into smaller parts?")
        )
        return state

    # Get agent config
    agent_config = state["agent_config"]
    agent_name = agent_config.get("name", "Assistant")
    agent_role = agent_config.get("role", "helpful AI assistant")

    # Build system prompt
    system_prompt = build_system_prompt(
        agent_name=agent_name,
        agent_role=agent_role,
        tools=state["tool_manifest"],
        knowledge_bases=agent_config.get("knowledge_bases", []),
        rag_context=state.get("rag_context", ""),
    )

    # Get LLM
    llm_config = agent_config.get("llm_config", {})
    llm: BaseChatModel = get_llm_provider(llm_config)

    # Bind tools to LLM if available
    tools_bound = False
    if state["tool_manifest"]:
        try:
            # Convert tool manifest to LangChain tool format
            base_tools = [tool_registry.get_tool(t["name"]) for t in state["tool_manifest"]]
            langchain_tools = [tool.to_langchain_tool() for tool in base_tools if tool]
            llm = llm.bind_tools(langchain_tools)
            tools_bound = True
            print(f"✓ Tools bound to LLM: {[t.name for t in base_tools if t]}")
        except NotImplementedError:
            provider = llm_config.get('provider', 'unknown')
            print(f"⚠ LLM provider '{provider}' does not support tool binding.")
            if provider == 'ollama':
                print(f"  → Upgrade to use tool calling: pip install langchain-ollama")
                print(f"  → Supported models: llama3.1, llama3.2, mistral, phi-4")
            print(f"  → Tools will be described in system prompt instead")
        except Exception as e:
            print(f"⚠ Failed to bind tools: {e}")
            import traceback
            traceback.print_exc()

    # Prepare messages
    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # Call LLM
    try:
        response = await llm.ainvoke(messages)

        # Check if LLM wants to call a tool
        if hasattr(response, "tool_calls") and response.tool_calls:
            # LLM wants to use a tool
            state["messages"].append(response)
            state["next_action"] = "check_consent"
        else:
            # LLM is responding directly
            state["messages"].append(response)
            state["next_action"] = "respond"

    except Exception as e:
        state["error"] = f"LLM error: {str(e)}"
        state["messages"].append(
            AIMessage(content=f"I apologize, but I encountered an error: {str(e)}")
        )
        state["next_action"] = "respond"

    return state


async def rag_node(state: AgentState) -> AgentState:
    """
    RAG node: Retrieve relevant context from knowledge base.

    This node:
    1. Takes the user's query
    2. Retrieves relevant documents
    3. Re-ranks them
    4. Adds context to state
    """
    # TODO: Implement RAG retrieval
    # For now, just mark that RAG was attempted

    # Get the last user message
    user_messages = [m for m in state["messages"] if isinstance(m, HumanMessage)]
    if not user_messages:
        state["rag_context"] = ""
        state["next_action"] = "reason"
        return state

    last_user_message = user_messages[-1].content

    # TODO: Actual RAG implementation
    # This is a placeholder
    state["rag_context"] = f"[RAG context for: {last_user_message}]"

    # Go back to reasoning with the new context
    state["next_action"] = "reason"

    return state


async def consent_check_node(state: AgentState) -> AgentState:
    """
    Consent check node: Determine if tool requires user approval.

    This node:
    1. Inspects the tool call from the LLM
    2. Checks if it's a write operation
    3. If yes: Set needs_consent=True and interrupt
    4. If no: Proceed to tool execution
    """
    # Get the last message (should be an AI message with tool calls)
    last_message = state["messages"][-1]

    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        state["next_action"] = "respond"
        return state

    tool_call = last_message.tool_calls[0]  # Handle first tool call
    tool_name = tool_call["name"]

    # Check if tool requires consent
    write_ops = state["agent_config"].get("write_operation_tools", [])

    if tool_name in write_ops:
        # Requires consent!
        tool_manifest_entry = next(
            (t for t in state["tool_manifest"] if t["name"] == tool_name),
            None
        )

        state["needs_consent"] = True
        state["consent_data"] = {
            "tool_name": tool_name,
            "tool_description": tool_manifest_entry.get("description", ""),
            "parameters": tool_call.get("args", {}),
            "action_impact": "modify data",  # TODO: Make this more specific
        }

        # Build consent request message
        consent_msg = build_consent_request(
            tool_name=state["consent_data"]["tool_name"],
            tool_description=state["consent_data"]["tool_description"],
            parameters=state["consent_data"]["parameters"],
            action_impact=state["consent_data"]["action_impact"],
        )

        state["messages"].append(AIMessage(content=consent_msg))
        state["next_action"] = "wait_consent"  # This will interrupt the graph
    else:
        # Read-only operation, execute directly
        state["needs_consent"] = False
        state["next_action"] = "execute_tool"

    return state


async def tool_executor_node(state: AgentState) -> AgentState:
    """
    Tool execution node: Execute the approved tool.

    This node:
    1. Gets the tool from the registry
    2. Executes it with the provided arguments
    3. Adds the result to messages
    4. Returns to reasoning
    """
    # Get the last AI message with tool calls
    ai_messages_with_tools = [
        m for m in state["messages"]
        if hasattr(m, "tool_calls") and m.tool_calls
    ]

    if not ai_messages_with_tools:
        state["next_action"] = "respond"
        return state

    last_ai_message = ai_messages_with_tools[-1]
    tool_call = last_ai_message.tool_calls[0]

    tool_name = tool_call["name"]
    tool_args = tool_call.get("args", {})

    # Get tool from registry
    tool = tool_registry.get_tool(tool_name)

    if not tool:
        error_msg = f"Tool '{tool_name}' not found in registry"
        state["messages"].append(
            ToolMessage(
                content=json.dumps({"error": error_msg}),
                tool_call_id=tool_call.get("id", ""),
            )
        )
        state["next_action"] = "reason"
        return state

    # Execute tool
    try:
        result = await tool.execute(**tool_args)
        state["messages"].append(
            ToolMessage(
                content=json.dumps(result.dict()),
                tool_call_id=tool_call.get("id", ""),
            )
        )
    except Exception as e:
        state["messages"].append(
            ToolMessage(
                content=json.dumps({"error": str(e)}),
                tool_call_id=tool_call.get("id", ""),
            )
        )

    # Reset consent state
    state["needs_consent"] = False
    state["consent_data"] = {}

    # Go back to reasoning with tool result
    state["next_action"] = "reason"

    return state


# Routing functions
def route_from_reasoning(state: AgentState) -> str:
    """Route from reasoning node based on next_action."""
    return state.get("next_action", "respond")


def route_from_consent(state: AgentState) -> str:
    """Route from consent check based on needs_consent."""
    if state.get("needs_consent", False):
        return "wait_consent"
    return "execute_tool"

"""WebSocket handler for real-time chat communication."""

import socketio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
from uuid import UUID
import json

from core.database import AsyncSessionLocal
from core.models import User, Agent, ChatSession, ChatMessage, MessageType
from core.security import decode_token
from agents.graph import run_agent, resume_agent_after_consent
from tools.registry import tool_registry


async def register_handlers(sio: socketio.AsyncServer):
    """Register Socket.IO event handlers."""

    @sio.event
    async def connect(sid, environ, auth):
        """Handle client connection."""
        try:
            # Authenticate user
            if not auth or "token" not in auth:
                await sio.disconnect(sid)
                return False

            token = auth["token"]
            payload = decode_token(token)
            user_id = payload.get("sub")

            if not user_id:
                await sio.disconnect(sid)
                return False

            # Store user info in session
            async with sio.session(sid) as session:
                session["user_id"] = user_id
                session["authenticated"] = True

            print(f"Client {sid} connected (user: {user_id})")
            return True

        except Exception as e:
            print(f"Connection error: {e}")
            await sio.disconnect(sid)
            return False

    @sio.event
    async def disconnect(sid):
        """Handle client disconnection."""
        print(f"Client {sid} disconnected")

    @sio.event
    async def join_session(sid, data: Dict[str, Any]):
        """Join a specific chat session room."""
        try:
            session_id = data.get("session_id")
            if not session_id:
                await sio.emit("error", {"message": "session_id required"}, room=sid)
                return

            # Verify session ownership
            async with sio.session(sid) as session:
                user_id = session.get("user_id")

            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(ChatSession)
                    .where(ChatSession.id == UUID(session_id))
                    .where(ChatSession.user_id == UUID(user_id))
                )
                chat_session = result.scalar_one_or_none()

                if not chat_session:
                    await sio.emit("error", {"message": "Session not found"}, room=sid)
                    return

            # Join room
            sio.enter_room(sid, session_id)

            # Store session ID
            async with sio.session(sid) as session:
                session["session_id"] = session_id

            await sio.emit("joined_session", {"session_id": session_id}, room=sid)
            print(f"Client {sid} joined session {session_id}")

        except Exception as e:
            await sio.emit("error", {"message": str(e)}, room=sid)

    @sio.event
    async def chat_message(sid, data: Dict[str, Any]):
        """Handle incoming chat message from user."""
        print(f"[DEBUG] chat_message handler called with sid={sid}, data={data}")
        try:
            # Get session info
            print(f"[DEBUG] Getting session info from sio.session...")
            async with sio.session(sid) as session:
                user_id = session.get("user_id")
                session_id = session.get("session_id")

            print(f"[DEBUG] user_id={user_id}, session_id={session_id}")

            if not session_id:
                print("[DEBUG] No session_id, sending error")
                await sio.emit("error", {"message": "Not in a session"}, room=sid)
                return

            message = data.get("message")
            print(f"[DEBUG] message={message}")
            if not message:
                print("[DEBUG] No message, sending error")
                await sio.emit("error", {"message": "Message required"}, room=sid)
                return

            # Get session and agent info from database
            print(f"[DEBUG] Opening database session...")
            async with AsyncSessionLocal() as db:
                print(f"[DEBUG] Querying ChatSession for id={session_id}")
                result = await db.execute(
                    select(ChatSession)
                    .where(ChatSession.id == UUID(session_id))
                )
                chat_session = result.scalar_one_or_none()
                print(f"[DEBUG] chat_session={chat_session}")

                if not chat_session:
                    print("[DEBUG] Chat session not found, sending error")
                    await sio.emit("error", {"message": "Session not found"}, room=sid)
                    return

                # Get agent
                print(f"[DEBUG] Querying Agent for id={chat_session.agent_id}")
                result = await db.execute(
                    select(Agent).where(Agent.id == chat_session.agent_id)
                )
                agent = result.scalar_one_or_none()
                print(f"[DEBUG] agent={agent}")

                if not agent:
                    print("[DEBUG] Agent not found, sending error")
                    await sio.emit("error", {"message": "Agent not found"}, room=sid)
                    return

                # Save user message to database
                print(f"[DEBUG] Saving user message to database...")
                user_msg = ChatMessage(
                    session_id=UUID(session_id),
                    message_type=MessageType.HUMAN,
                    content=message,
                    metadata={},
                )
                db.add(user_msg)
                await db.commit()
                print(f"[DEBUG] User message saved")

                # Prepare agent config
                print(f"[DEBUG] Preparing agent config...")
                agent_config = {
                    "id": str(agent.id),
                    "name": agent.name,
                    "role": agent.description or "helpful assistant",
                    "llm_config": agent.llm_config,
                    "embedding_config": agent.embedding_config,
                    "knowledge_bases": [],  # TODO: Load linked knowledge bases
                }

                # Get tool manifest for enabled tools
                print(f"[DEBUG] Getting tool manifest for tools: {agent.enabled_tools}")
                tool_manifest = tool_registry.get_manifest(agent.enabled_tools)
                print(f"[DEBUG] tool_manifest={tool_manifest}")

            # Emit typing indicator
            await sio.emit("agent_typing", {"typing": True}, room=session_id)

            # Stream agent response
            final_response = ""
            try:
                print(f"Starting agent execution for session {session_id}")
                print(f"Agent config: {agent_config}")
                print(f"Tool manifest: {tool_manifest}")

                async for event in run_agent(
                    user_message=message,
                    session_id=session_id,
                    user_id=user_id,
                    agent_config=agent_config,
                    tool_manifest=tool_manifest,
                ):
                    print(f"Agent event: {list(event.keys())}")

                    # Process each event from the agent graph
                    for node_name, node_state in event.items():
                        if node_name == "reason":
                            # Reasoning node - stream tokens
                            if "messages" in node_state:
                                last_msg = node_state["messages"][-1]
                                if hasattr(last_msg, "content"):
                                    # Stream the message content
                                    await sio.emit(
                                        "token",
                                        {"data": last_msg.content},
                                        room=session_id
                                    )
                                    final_response = last_msg.content

                        elif node_name == "check_consent":
                            # Consent required
                            if node_state.get("needs_consent"):
                                consent_data = node_state.get("consent_data", {})
                                await sio.emit(
                                    "consent_required",
                                    {"data": consent_data},
                                    room=session_id
                                )

                        elif node_name == "execute_tool":
                            # Tool executed
                            await sio.emit(
                                "agent_thought",
                                {"data": "Executing tool..."},
                                room=session_id
                            )

            except Exception as agent_error:
                error_msg = f"Agent execution error: {str(agent_error)}"
                print(error_msg)
                import traceback
                traceback.print_exc()
                await sio.emit("error", {"message": error_msg}, room=session_id)
                return

            # Save AI response to database
            if final_response:
                async with AsyncSessionLocal() as db:
                    ai_msg = ChatMessage(
                        session_id=UUID(session_id),
                        message_type=MessageType.AI,
                        content=final_response,
                        metadata={},
                    )
                    db.add(ai_msg)

                    # Update session timestamp
                    from datetime import datetime
                    result = await db.execute(
                        select(ChatSession).where(ChatSession.id == UUID(session_id))
                    )
                    chat_session = result.scalar_one_or_none()
                    if chat_session:
                        chat_session.last_message_at = datetime.utcnow()

                    await db.commit()

            # Emit end of stream
            await sio.emit("end_of_stream", {}, room=session_id)
            await sio.emit("agent_typing", {"typing": False}, room=session_id)

        except Exception as e:
            await sio.emit("error", {"message": str(e)}, room=sid)
            print(f"Chat message error: {e}")
            import traceback
            traceback.print_exc()

    @sio.event
    async def consent_response(sid, data: Dict[str, Any]):
        """Handle user's consent response (approve/reject)."""
        try:
            async with sio.session(sid) as session:
                session_id = session.get("session_id")

            if not session_id:
                await sio.emit("error", {"message": "Not in a session"}, room=sid)
                return

            approved = data.get("approved", False)

            # Resume agent execution
            await sio.emit("agent_typing", {"typing": True}, room=session_id)

            final_response = ""
            async for event in resume_agent_after_consent(
                session_id=session_id,
                approved=approved,
            ):
                # Process events similar to chat_message
                for node_name, node_state in event.items():
                    if node_name == "reason":
                        if "messages" in node_state:
                            last_msg = node_state["messages"][-1]
                            if hasattr(last_msg, "content"):
                                await sio.emit(
                                    "token",
                                    {"data": last_msg.content},
                                    room=session_id
                                )
                                final_response = last_msg.content

            # Save response
            if final_response:
                async with AsyncSessionLocal() as db:
                    ai_msg = ChatMessage(
                        session_id=UUID(session_id),
                        message_type=MessageType.AI,
                        content=final_response,
                        metadata={},
                    )
                    db.add(ai_msg)
                    await db.commit()

            await sio.emit("end_of_stream", {}, room=session_id)
            await sio.emit("agent_typing", {"typing": False}, room=session_id)

        except Exception as e:
            await sio.emit("error", {"message": str(e)}, room=sid)
            print(f"Consent response error: {e}")

    return sio

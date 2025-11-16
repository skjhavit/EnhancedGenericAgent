"""Chat session management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from core.database import get_db
from core.models import User, ChatSession, ChatMessage, MessageType, Agent
from core.security import get_current_user

router = APIRouter()


# Request/Response models
class CreateSessionRequest(BaseModel):
    agent_id: str
    title: str | None = None


class SessionResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    message_count: int

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    id: str
    message_type: str
    content: str
    metadata: dict
    created_at: datetime

    class Config:
        from_attributes = True


class SessionDetailResponse(BaseModel):
    id: str
    agent_id: str
    agent_name: str
    title: str | None
    created_at: datetime
    updated_at: datetime
    last_message_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class UpdateSessionRequest(BaseModel):
    title: str


@router.post("", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new chat session."""
    # Verify agent exists
    result = await db.execute(select(Agent).where(Agent.id == UUID(request.agent_id)))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Create session
    session = ChatSession(
        user_id=current_user.id,
        agent_id=UUID(request.agent_id),
        title=request.title,
    )

    db.add(session)
    await db.commit()
    await db.refresh(session)

    return SessionResponse(
        id=str(session.id),
        agent_id=str(session.agent_id),
        agent_name=agent.name,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        message_count=0,
    )


@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List all chat sessions for the current user."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .options(joinedload(ChatSession.agent))
        .order_by(desc(ChatSession.last_message_at))
        .limit(limit)
        .offset(offset)
    )
    sessions = result.scalars().unique().all()

    # Get message counts
    session_responses = []
    for session in sessions:
        message_count_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id)
        )
        message_count = len(message_count_result.scalars().all())

        session_responses.append(SessionResponse(
            id=str(session.id),
            agent_id=str(session.agent_id),
            agent_name=session.agent.name,
            title=session.title,
            created_at=session.created_at,
            updated_at=session.updated_at,
            last_message_at=session.last_message_at,
            message_count=message_count,
        ))

    return session_responses


@router.get("/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat session with all messages."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == UUID(session_id))
        .where(ChatSession.user_id == current_user.id)
        .options(joinedload(ChatSession.agent))
        .options(joinedload(ChatSession.messages))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    messages = [
        MessageResponse(
            id=str(msg.id),
            message_type=msg.message_type.value,
            content=msg.content,
            metadata=msg.message_metadata,
            created_at=msg.created_at,
        )
        for msg in sorted(session.messages, key=lambda m: m.created_at)
    ]

    return SessionDetailResponse(
        id=str(session.id),
        agent_id=str(session.agent_id),
        agent_name=session.agent.name,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        messages=messages,
    )


@router.patch("/{session_id}", response_model=SessionResponse)
async def update_session(
    session_id: str,
    request: UpdateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update a chat session (e.g., change title)."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == UUID(session_id))
        .where(ChatSession.user_id == current_user.id)
        .options(joinedload(ChatSession.agent))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    session.title = request.title
    await db.commit()
    await db.refresh(session)

    # Get message count
    message_count_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session.id)
    )
    message_count = len(message_count_result.scalars().all())

    return SessionResponse(
        id=str(session.id),
        agent_id=str(session.agent_id),
        agent_name=session.agent.name,
        title=session.title,
        created_at=session.created_at,
        updated_at=session.updated_at,
        last_message_at=session.last_message_at,
        message_count=message_count,
    )


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session and all its messages."""
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == UUID(session_id))
        .where(ChatSession.user_id == current_user.id)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    await db.delete(session)
    await db.commit()

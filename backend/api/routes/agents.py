"""Agent management routes."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from core.database import get_db
from core.models import User, Agent, KnowledgeBase
from core.security import get_current_user

router = APIRouter()


# Request/Response models
class AgentResponse(BaseModel):
    id: str
    name: str
    description: str | None
    system_prompt_template: str
    llm_config: dict
    embedding_config: dict
    enabled_tools: list
    write_operation_tools: list
    knowledge_base_ids: list
    created_at: datetime

    class Config:
        from_attributes = True


class CreateAgentRequest(BaseModel):
    name: str
    description: str | None = None
    system_prompt_template: str
    llm_config: dict
    embedding_config: dict
    enabled_tools: list = []
    write_operation_tools: list = []
    knowledge_base_ids: list = []


class UpdateAgentRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    system_prompt_template: str | None = None
    llm_config: dict | None = None
    embedding_config: dict | None = None
    enabled_tools: list | None = None
    write_operation_tools: list | None = None
    knowledge_base_ids: list | None = None


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List all available agents."""
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.knowledge_bases))
        .limit(limit)
        .offset(offset)
    )
    agents = result.scalars().all()

    return [
        AgentResponse(
            id=str(agent.id),
            name=agent.name,
            description=agent.description,
            system_prompt_template=agent.system_prompt_template,
            llm_config=agent.llm_config,
            embedding_config=agent.embedding_config,
            enabled_tools=agent.enabled_tools,
            write_operation_tools=agent.write_operation_tools,
            knowledge_base_ids=[str(kb.id) for kb in agent.knowledge_bases],
            created_at=agent.created_at,
        )
        for agent in agents
    ]


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get a specific agent."""
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.knowledge_bases))
        .where(Agent.id == UUID(agent_id))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt_template=agent.system_prompt_template,
        llm_config=agent.llm_config,
        embedding_config=agent.embedding_config,
        enabled_tools=agent.enabled_tools,
        write_operation_tools=agent.write_operation_tools,
        knowledge_base_ids=[str(kb.id) for kb in agent.knowledge_bases],
        created_at=agent.created_at,
    )


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    request: CreateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new agent."""
    agent = Agent(
        name=request.name,
        description=request.description,
        system_prompt_template=request.system_prompt_template,
        llm_config=request.llm_config,
        embedding_config=request.embedding_config,
        enabled_tools=request.enabled_tools,
        write_operation_tools=request.write_operation_tools,
        created_by=current_user.id,
    )

    # Attach knowledge bases if provided
    if request.knowledge_base_ids:
        kb_result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id.in_([UUID(kb_id) for kb_id in request.knowledge_base_ids]))
        )
        knowledge_bases = kb_result.scalars().all()
        agent.knowledge_bases = list(knowledge_bases)

    db.add(agent)
    await db.commit()
    await db.refresh(agent, ["knowledge_bases"])

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt_template=agent.system_prompt_template,
        llm_config=agent.llm_config,
        embedding_config=agent.embedding_config,
        enabled_tools=agent.enabled_tools,
        write_operation_tools=agent.write_operation_tools,
        knowledge_base_ids=[str(kb.id) for kb in agent.knowledge_bases],
        created_at=agent.created_at,
    )


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: str,
    request: UpdateAgentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update an agent."""
    result = await db.execute(
        select(Agent)
        .options(selectinload(Agent.knowledge_bases))
        .where(Agent.id == UUID(agent_id))
    )
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    # Update fields if provided
    if request.name is not None:
        agent.name = request.name
    if request.description is not None:
        agent.description = request.description
    if request.system_prompt_template is not None:
        agent.system_prompt_template = request.system_prompt_template
    if request.llm_config is not None:
        agent.llm_config = request.llm_config
    if request.embedding_config is not None:
        agent.embedding_config = request.embedding_config
    if request.enabled_tools is not None:
        agent.enabled_tools = request.enabled_tools
    if request.write_operation_tools is not None:
        agent.write_operation_tools = request.write_operation_tools

    # Update knowledge bases if provided
    if request.knowledge_base_ids is not None:
        kb_result = await db.execute(
            select(KnowledgeBase).where(KnowledgeBase.id.in_([UUID(kb_id) for kb_id in request.knowledge_base_ids]))
        )
        knowledge_bases = kb_result.scalars().all()
        agent.knowledge_bases = list(knowledge_bases)

    await db.commit()
    await db.refresh(agent, ["knowledge_bases"])

    return AgentResponse(
        id=str(agent.id),
        name=agent.name,
        description=agent.description,
        system_prompt_template=agent.system_prompt_template,
        llm_config=agent.llm_config,
        embedding_config=agent.embedding_config,
        enabled_tools=agent.enabled_tools,
        write_operation_tools=agent.write_operation_tools,
        knowledge_base_ids=[str(kb.id) for kb in agent.knowledge_bases],
        created_at=agent.created_at,
    )


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete an agent."""
    result = await db.execute(select(Agent).where(Agent.id == UUID(agent_id)))
    agent = result.scalar_one_or_none()

    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found",
        )

    await db.delete(agent)
    await db.commit()

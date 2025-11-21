"""Admin routes for system management."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict, Any

from core.models import User
from core.security import get_current_admin_user

router = APIRouter()


class SystemStatsResponse(BaseModel):
    total_users: int
    total_agents: int
    total_knowledge_bases: int
    total_chat_sessions: int
    total_messages: int


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_admin: User = Depends(get_current_admin_user)
):
    """Get system statistics (admin only)."""
    # TODO: Implement actual statistics gathering
    return SystemStatsResponse(
        total_users=0,
        total_agents=0,
        total_knowledge_bases=0,
        total_chat_sessions=0,
        total_messages=0,
    )


@router.get("/tools")
async def list_available_tools(
    current_admin: User = Depends(get_current_admin_user)
) -> List[Dict[str, Any]]:
    """
    List all available tools in the registry.

    Returns tool manifests that can be used by the UI to populate
    the available tools list when creating/editing agents.
    """
    from tools.registry import tool_registry

    # Get all tools from the registry
    manifests = tool_registry.get_manifest()

    # Return manifests sorted by name for consistent UI ordering
    return sorted(manifests, key=lambda x: x['name'])

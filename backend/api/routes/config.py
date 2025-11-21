"""Configuration routes for runtime settings."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List

from core.security import get_current_user
from core.models import User
from core.llm_config import LLMProviderConfig

router = APIRouter()


class ProvidersResponse(BaseModel):
    llm_providers: List[str]
    embedding_providers: List[str]


@router.get("/providers", response_model=ProvidersResponse)
async def get_available_providers(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of available LLM and embedding providers based on configured API keys.

    Returns providers that have valid API keys in environment variables.
    """
    return ProvidersResponse(
        llm_providers=LLMProviderConfig.get_available_llm_providers(),
        embedding_providers=LLMProviderConfig.get_available_embedding_providers(),
    )

"""
LLM Provider Configuration

Loads API keys from environment variables and provides default model configurations.
Used for runtime LLM/embedding provider overrides in chat sessions.
"""

import os
from typing import Dict, Optional


class LLMProviderConfig:
    """Configuration for LLM providers with default models and API keys from environment."""

    # Default models for each provider
    DEFAULT_MODELS = {
        "openai": "gpt-4o",
        "anthropic": "claude-3-5-sonnet-20241022",
        "gemini": "gemini-1.5-pro",
        "ollama": "llama3.1",
    }

    # Default embedding models for each provider
    DEFAULT_EMBEDDING_MODELS = {
        "openai": "text-embedding-3-small",
        "gemini": "text-embedding-004",
        "ollama": "nomic-embed-text",
    }

    @classmethod
    def get_api_key(cls, provider: str) -> Optional[str]:
        """
        Get API key for a provider from environment variables.

        Args:
            provider: Provider name (openai, anthropic, gemini, ollama)

        Returns:
            API key or None if not found
        """
        env_var_map = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "gemini": "GOOGLE_API_KEY",
            "google": "GOOGLE_API_KEY",  # Alias
        }

        env_var = env_var_map.get(provider)
        if env_var:
            return os.getenv(env_var)
        return None

    @classmethod
    def get_ollama_base_url(cls) -> str:
        """Get Ollama base URL from environment."""
        return os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

    @classmethod
    def get_llm_config(cls, provider: str) -> Dict:
        """
        Get LLM configuration for a provider using environment API keys.

        Args:
            provider: Provider name

        Returns:
            Configuration dict with provider, model, and api_key
        """
        config = {
            "provider": provider,
            "model": cls.DEFAULT_MODELS.get(provider, "gpt-4o"),
            "temperature": 0.7,
        }

        if provider == "ollama":
            config["base_url"] = cls.get_ollama_base_url()
        else:
            api_key = cls.get_api_key(provider)
            if api_key:
                config["api_key"] = api_key

        return config

    @classmethod
    def get_embedding_config(cls, provider: str) -> Dict:
        """
        Get embedding configuration for a provider using environment API keys.

        Args:
            provider: Provider name

        Returns:
            Configuration dict with provider, model, and api_key
        """
        config = {
            "provider": provider,
            "model": cls.DEFAULT_EMBEDDING_MODELS.get(provider, "text-embedding-3-small"),
        }

        if provider == "ollama":
            config["base_url"] = cls.get_ollama_base_url()
        else:
            api_key = cls.get_api_key(provider)
            if api_key:
                config["api_key"] = api_key

        return config

    @classmethod
    def get_available_llm_providers(cls) -> list:
        """
        Get list of available LLM providers based on configured API keys.

        Returns:
            List of provider names that have API keys configured
        """
        providers = []

        # Always include Ollama (doesn't require API key)
        providers.append("ollama")

        # Check for API keys
        if cls.get_api_key("openai"):
            providers.append("openai")
        if cls.get_api_key("anthropic"):
            providers.append("anthropic")
        if cls.get_api_key("gemini"):
            providers.append("gemini")

        return providers

    @classmethod
    def get_available_embedding_providers(cls) -> list:
        """
        Get list of available embedding providers based on configured API keys.

        Returns:
            List of provider names that have API keys configured
        """
        providers = []

        # Always include Ollama (doesn't require API key)
        providers.append("ollama")

        # Check for API keys
        if cls.get_api_key("openai"):
            providers.append("openai")
        if cls.get_api_key("gemini"):
            providers.append("gemini")

        return providers

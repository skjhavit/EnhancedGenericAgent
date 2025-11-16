"""LLM provider factory for creating configurable language models."""

from typing import Dict, Any
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama


class LLMFactory:
    """Factory for creating LLM instances based on configuration."""

    @staticmethod
    def create(config: Dict[str, Any]) -> BaseChatModel:
        """
        Create an LLM instance based on the provided configuration.

        Args:
            config: Dictionary containing LLM configuration
                Required keys:
                - provider: str (openai, gemini, ollama, anthropic)
                - model: str
                Optional keys (provider-specific):
                - api_key: str
                - base_url: str
                - temperature: float
                - max_tokens: int
                - streaming: bool

        Returns:
            Configured LLM instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = config.get("provider", "").lower()
        model = config.get("model")
        temperature = config.get("temperature", 0.7)
        max_tokens = config.get("max_tokens", 2000)
        streaming = config.get("streaming", True)

        if provider == "openai":
            return ChatOpenAI(
                model=model,
                api_key=config.get("api_key"),
                temperature=temperature,
                max_tokens=max_tokens,
                streaming=streaming,
            )

        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                model=model,
                google_api_key=config.get("api_key"),
                temperature=temperature,
                max_output_tokens=max_tokens,
                streaming=streaming,
            )

        elif provider == "ollama":
            return ChatOllama(
                model=model,
                base_url=config.get("base_url", "http://localhost:11434"),
                temperature=temperature,
                num_predict=max_tokens,
            )

        elif provider == "anthropic":
            # Import here to avoid dependency if not using Anthropic
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(
                    model=model,
                    anthropic_api_key=config.get("api_key"),
                    temperature=temperature,
                    max_tokens=max_tokens,
                    streaming=streaming,
                )
            except ImportError:
                raise ValueError(
                    "Anthropic provider requires langchain-anthropic. "
                    "Install with: pip install langchain-anthropic"
                )

        else:
            raise ValueError(
                f"Unsupported LLM provider: {provider}. "
                f"Supported providers: openai, gemini, ollama, anthropic"
            )


def get_llm_provider(config: Dict[str, Any]) -> BaseChatModel:
    """
    Convenience function to get an LLM provider.

    Args:
        config: LLM configuration dictionary

    Returns:
        Configured LLM instance
    """
    return LLMFactory.create(config)

"""Embedding model factory for creating configurable embeddings."""

from typing import Dict, Any
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.embeddings import OllamaEmbeddings, HuggingFaceEmbeddings


class EmbeddingFactory:
    """Factory for creating embedding model instances based on configuration."""

    @staticmethod
    def create(config: Dict[str, Any]) -> Embeddings:
        """
        Create an embedding model instance based on the provided configuration.

        Args:
            config: Dictionary containing embedding configuration
                Required keys:
                - provider: str (openai, gemini, ollama, huggingface)
                - model: str
                Optional keys (provider-specific):
                - api_key: str
                - base_url: str

        Returns:
            Configured embedding model instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = config.get("provider", "").lower()
        model = config.get("model")

        if provider == "openai":
            return OpenAIEmbeddings(
                model=model or "text-embedding-3-small",
                openai_api_key=config.get("api_key"),
            )

        elif provider == "gemini":
            return GoogleGenerativeAIEmbeddings(
                model=model or "models/embedding-001",
                google_api_key=config.get("api_key"),
            )

        elif provider == "ollama":
            return OllamaEmbeddings(
                model=model or "nomic-embed-text",
                base_url=config.get("base_url", "http://localhost:11434"),
            )

        elif provider == "huggingface":
            return HuggingFaceEmbeddings(
                model_name=model or "sentence-transformers/all-MiniLM-L6-v2",
                model_kwargs={"device": "cpu"},  # Can be configured to use GPU
                encode_kwargs={"normalize_embeddings": True},
            )

        else:
            raise ValueError(
                f"Unsupported embedding provider: {provider}. "
                f"Supported providers: openai, gemini, ollama, huggingface"
            )


def get_embedding_model(config: Dict[str, Any]) -> Embeddings:
    """
    Convenience function to get an embedding model.

    Args:
        config: Embedding configuration dictionary

    Returns:
        Configured embedding model instance
    """
    return EmbeddingFactory.create(config)

"""Vector store factory for creating configurable vector databases."""

from typing import Dict, Any, Optional
from langchain_core.vectorstores import VectorStore
from langchain_core.embeddings import Embeddings
from langchain_community.vectorstores import Chroma
import os


class VectorStoreFactory:
    """Factory for creating vector store instances based on configuration."""

    @staticmethod
    def create(
        config: Dict[str, Any],
        embedding_model: Embeddings,
        collection_name: str
    ) -> VectorStore:
        """
        Create a vector store instance based on the provided configuration.

        Args:
            config: Dictionary containing vector store configuration
                Required keys:
                - provider: str (chromadb, weaviate, pinecone)
                Optional keys (provider-specific):
                - persist_directory: str (for ChromaDB)
                - host: str (for Weaviate)
                - api_key: str (for Pinecone)
                - environment: str (for Pinecone)
            embedding_model: Embedding model to use for vectorization
            collection_name: Name of the collection/index

        Returns:
            Configured vector store instance

        Raises:
            ValueError: If provider is not supported
        """
        provider = config.get("provider", "").lower()

        if provider == "chromadb" or provider == "chroma":
            persist_directory = config.get(
                "persist_directory",
                os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
            )

            return Chroma(
                collection_name=collection_name,
                embedding_function=embedding_model,
                persist_directory=persist_directory,
            )

        elif provider == "weaviate":
            try:
                from langchain_community.vectorstores import Weaviate
                import weaviate

                # Connect to Weaviate
                client = weaviate.Client(
                    url=config.get("host", "http://localhost:8080"),
                    auth_client_secret=weaviate.AuthApiKey(
                        api_key=config.get("api_key", "")
                    ) if config.get("api_key") else None,
                )

                return Weaviate(
                    client=client,
                    index_name=collection_name,
                    text_key="text",
                    embedding=embedding_model,
                )
            except ImportError:
                raise ValueError(
                    "Weaviate provider requires weaviate-client. "
                    "Install with: pip install weaviate-client"
                )

        elif provider == "pinecone":
            try:
                from langchain_community.vectorstores import Pinecone
                import pinecone

                # Initialize Pinecone
                pinecone.init(
                    api_key=config.get("api_key"),
                    environment=config.get("environment", "us-west1-gcp"),
                )

                return Pinecone.from_existing_index(
                    index_name=collection_name,
                    embedding=embedding_model,
                )
            except ImportError:
                raise ValueError(
                    "Pinecone provider requires pinecone-client. "
                    "Install with: pip install pinecone-client"
                )

        else:
            raise ValueError(
                f"Unsupported vector store provider: {provider}. "
                f"Supported providers: chromadb, weaviate, pinecone"
            )


def get_vectorstore(
    config: Dict[str, Any],
    embedding_model: Embeddings,
    collection_name: str
) -> VectorStore:
    """
    Convenience function to get a vector store.

    Args:
        config: Vector store configuration dictionary
        embedding_model: Embedding model to use
        collection_name: Name of the collection/index

    Returns:
        Configured vector store instance
    """
    return VectorStoreFactory.create(config, embedding_model, collection_name)

"""Document ingestion pipeline for RAG."""

from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import (
    PyPDFLoader,
    UnstructuredFileLoader,
    TextLoader,
)
from pathlib import Path
import os


class DocumentIngestionPipeline:
    """
    Pipeline for ingesting documents into the RAG system.

    Handles:
    - Loading documents from various formats
    - Semantic chunking
    - Metadata extraction
    """

    def __init__(
        self,
        chunk_size: int = 1500,
        chunk_overlap: int = 300,
    ):
        """
        Initialize the ingestion pipeline.

        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Text splitter for semantic chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def load_document(self, file_path: str) -> List[Document]:
        """
        Load a document from file.

        Args:
            file_path: Path to the document

        Returns:
            List of loaded documents

        Raises:
            ValueError: If file type is not supported
        """
        path = Path(file_path)
        file_extension = path.suffix.lower()

        if file_extension == ".pdf":
            loader = PyPDFLoader(file_path)
        elif file_extension in [".txt", ".md"]:
            loader = TextLoader(file_path)
        elif file_extension in [".docx", ".doc"]:
            loader = UnstructuredFileLoader(file_path)
        elif file_extension == ".html":
            from langchain_community.document_loaders import BSHTMLLoader
            loader = BSHTMLLoader(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        return loader.load()

    def chunk_documents(
        self,
        documents: List[Document],
        add_metadata: bool = True,
    ) -> List[Document]:
        """
        Chunk documents into smaller pieces.

        Args:
            documents: List of documents to chunk
            add_metadata: Whether to add chunk metadata

        Returns:
            List of chunked documents
        """
        chunks = self.text_splitter.split_documents(documents)

        if add_metadata:
            for i, chunk in enumerate(chunks):
                chunk.metadata["chunk_id"] = i
                chunk.metadata["chunk_size"] = len(chunk.page_content)

        return chunks

    async def ingest_file(
        self,
        file_path: str,
        knowledge_base_id: str,
        additional_metadata: dict = None,
    ) -> List[Document]:
        """
        Complete ingestion pipeline for a single file.

        Args:
            file_path: Path to the file
            knowledge_base_id: ID of the knowledge base
            additional_metadata: Additional metadata to add to chunks

        Returns:
            List of chunked documents ready for embedding
        """
        # Load document
        documents = self.load_document(file_path)

        # Add metadata
        for doc in documents:
            doc.metadata["knowledge_base_id"] = knowledge_base_id
            doc.metadata["source_file"] = os.path.basename(file_path)
            if additional_metadata:
                doc.metadata.update(additional_metadata)

        # Chunk documents
        chunks = self.chunk_documents(documents)

        return chunks


async def ingest_and_store_document(
    file_path: str,
    knowledge_base_id: str,
    embedding_model,
    vectorstore,
    chunk_size: int = 1500,
    chunk_overlap: int = 300,
) -> dict:
    """
    Complete pipeline: ingest, embed, and store document.

    Args:
        file_path: Path to the document
        knowledge_base_id: ID of the knowledge base
        embedding_model: Embedding model instance
        vectorstore: Vector store instance
        chunk_size: Size of chunks
        chunk_overlap: Overlap between chunks

    Returns:
        Dictionary with ingestion results
    """
    pipeline = DocumentIngestionPipeline(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )

    # Ingest and chunk
    chunks = await pipeline.ingest_file(
        file_path=file_path,
        knowledge_base_id=knowledge_base_id,
    )

    # Add to vector store
    vectorstore.add_documents(chunks)

    return {
        "chunks_created": len(chunks),
        "total_characters": sum(len(c.page_content) for c in chunks),
        "file_path": file_path,
    }

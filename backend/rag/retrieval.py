"""Advanced retrieval with re-ranking for RAG."""

from typing import List, Optional
from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore


class AdvancedRetriever:
    """
    Advanced retriever with re-ranking support.

    Implements a two-stage retrieval:
    1. Initial broad retrieval (k=10)
    2. Re-ranking to get top-n most relevant
    """

    def __init__(
        self,
        vectorstore: VectorStore,
        use_reranking: bool = True,
        initial_k: int = 10,
        final_top_n: int = 5,
    ):
        """
        Initialize the retriever.

        Args:
            vectorstore: Vector store to retrieve from
            use_reranking: Whether to use re-ranking
            initial_k: Number of documents to initially retrieve
            final_top_n: Number of documents to return after re-ranking
        """
        self.vectorstore = vectorstore
        self.use_reranking = use_reranking
        self.initial_k = initial_k
        self.final_top_n = final_top_n

        # Initialize re-ranker if enabled
        if use_reranking:
            try:
                from flashrank import Ranker, RerankRequest
                self.reranker = Ranker(model_name="ms-marco-MiniLM-L-12-v2")
                self.RerankRequest = RerankRequest
            except ImportError:
                print("FlashRank not available, disabling re-ranking")
                self.use_reranking = False
                self.reranker = None

    async def retrieve(
        self,
        query: str,
        filter_metadata: Optional[dict] = None,
    ) -> List[Document]:
        """
        Retrieve relevant documents for a query.

        Args:
            query: Search query
            filter_metadata: Optional metadata filters

        Returns:
            List of relevant documents (re-ranked if enabled)
        """
        # Initial retrieval
        docs = await self.vectorstore.asimilarity_search(
            query,
            k=self.initial_k,
            filter=filter_metadata,
        )

        if not docs:
            return []

        # Re-rank if enabled
        if self.use_reranking and self.reranker:
            docs = await self._rerank_documents(query, docs)

        return docs[:self.final_top_n]

    async def _rerank_documents(
        self,
        query: str,
        documents: List[Document],
    ) -> List[Document]:
        """
        Re-rank documents using FlashRank.

        Args:
            query: Search query
            documents: List of documents to re-rank

        Returns:
            Re-ranked list of documents
        """
        if not documents:
            return []

        # Prepare passages for re-ranking
        passages = [
            {
                "id": i,
                "text": doc.page_content,
                "meta": doc.metadata,
            }
            for i, doc in enumerate(documents)
        ]

        # Create rerank request
        rerank_request = self.RerankRequest(
            query=query,
            passages=passages,
        )

        # Perform re-ranking
        results = self.reranker.rerank(rerank_request)

        # Sort documents by re-ranking score
        ranked_docs = []
        for result in results:
            doc_id = result["id"]
            ranked_docs.append(documents[doc_id])

        return ranked_docs

    def retrieve_with_scores(
        self,
        query: str,
        filter_metadata: Optional[dict] = None,
    ) -> List[tuple[Document, float]]:
        """
        Retrieve documents with similarity scores.

        Args:
            query: Search query
            filter_metadata: Optional metadata filters

        Returns:
            List of (document, score) tuples
        """
        return self.vectorstore.similarity_search_with_score(
            query,
            k=self.initial_k,
            filter=filter_metadata,
        )


async def synthesize_context(
    query: str,
    documents: List[Document],
    max_context_length: int = 4000,
) -> str:
    """
    Synthesize retrieved documents into coherent context.

    Args:
        query: Original query
        documents: Retrieved documents
        max_context_length: Maximum length of context

    Returns:
        Synthesized context string
    """
    if not documents:
        return ""

    # Build context from documents
    context_parts = []
    current_length = 0

    for i, doc in enumerate(documents, 1):
        # Format document
        doc_text = f"[Source {i}]\n{doc.page_content}\n"

        # Check if adding this document would exceed limit
        if current_length + len(doc_text) > max_context_length:
            break

        context_parts.append(doc_text)
        current_length += len(doc_text)

    # Join all parts
    context = "\n---\n".join(context_parts)

    return context


class RAGPipeline:
    """Complete RAG pipeline for retrieval and synthesis."""

    def __init__(
        self,
        vectorstore: VectorStore,
        use_reranking: bool = True,
    ):
        """
        Initialize the RAG pipeline.

        Args:
            vectorstore: Vector store instance
            use_reranking: Whether to use re-ranking
        """
        self.retriever = AdvancedRetriever(
            vectorstore=vectorstore,
            use_reranking=use_reranking,
        )

    async def get_context(
        self,
        query: str,
        knowledge_base_id: Optional[str] = None,
        max_context_length: int = 4000,
    ) -> str:
        """
        Get synthesized context for a query.

        Args:
            query: Search query
            knowledge_base_id: Optional KB ID to filter by
            max_context_length: Maximum context length

        Returns:
            Synthesized context string
        """
        # Filter by knowledge base if provided
        filter_metadata = None
        if knowledge_base_id:
            filter_metadata = {"knowledge_base_id": knowledge_base_id}

        # Retrieve documents
        documents = await self.retriever.retrieve(
            query=query,
            filter_metadata=filter_metadata,
        )

        # Synthesize context
        context = await synthesize_context(
            query=query,
            documents=documents,
            max_context_length=max_context_length,
        )

        return context

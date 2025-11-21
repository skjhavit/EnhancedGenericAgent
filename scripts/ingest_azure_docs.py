#!/usr/bin/env python3
"""
Azure Documentation Ingestion Script

This script scrapes and ingests Azure Active Directory and Microsoft Graph API
documentation into the knowledge base for the Azure Workforce Admin Agent.

Usage:
    python scripts/ingest_azure_docs.py <knowledge_base_id>

Example:
    python scripts/ingest_azure_docs.py 123e4567-e89b-12d3-a456-426614174000

Requirements:
    - Knowledge base must be created first via API
    - Database must be running
    - Internet connection for fetching documentation
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from bs4 import BeautifulSoup
from langchain_community.document_loaders import AsyncHtmlLoader
from langchain_core.documents import Document
from typing import List
import httpx


# Microsoft Learn documentation URLs
AZURE_DOC_URLS = [
    # Microsoft Graph API - Users
    "https://learn.microsoft.com/en-us/graph/api/user-post-users",
    "https://learn.microsoft.com/en-us/graph/api/user-get",
    "https://learn.microsoft.com/en-us/graph/api/user-update",
    "https://learn.microsoft.com/en-us/graph/api/user-delete",
    "https://learn.microsoft.com/en-us/graph/api/resources/user",

    # Microsoft Graph API - Groups
    "https://learn.microsoft.com/en-us/graph/api/group-post-groups",
    "https://learn.microsoft.com/en-us/graph/api/group-get",
    "https://learn.microsoft.com/en-us/graph/api/group-update",
    "https://learn.microsoft.com/en-us/graph/api/group-delete",
    "https://learn.microsoft.com/en-us/graph/api/group-post-members",
    "https://learn.microsoft.com/en-us/graph/api/resources/group",

    # Microsoft Graph API - Applications
    "https://learn.microsoft.com/en-us/graph/api/application-post-applications",
    "https://learn.microsoft.com/en-us/graph/api/application-get",
    "https://learn.microsoft.com/en-us/graph/api/resources/application",

    # Azure AD Best Practices
    "https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-users-assign-role-azure-portal",
    "https://learn.microsoft.com/en-us/azure/active-directory/fundamentals/active-directory-groups-create-azure-portal",

    # Microsoft Graph Overview
    "https://learn.microsoft.com/en-us/graph/overview",
    "https://learn.microsoft.com/en-us/graph/auth/",
    "https://learn.microsoft.com/en-us/graph/permissions-reference",
]


def extract_main_content(html: str, url: str) -> str:
    """
    Extract main content from Microsoft Learn HTML.

    Args:
        html: Raw HTML content
        url: Source URL (for metadata)

    Returns:
        Cleaned text content
    """
    soup = BeautifulSoup(html, 'html.parser')

    # MS Learn uses <main> tag with specific ID
    main_content = soup.find('main', {'id': 'main'})

    if not main_content:
        # Fallback to article tag
        main_content = soup.find('article')

    if not main_content:
        # Last resort - get body
        main_content = soup.find('body')

    if main_content:
        # Remove navigation, code toolbar buttons, and other UI elements
        for tag in main_content.find_all(['nav', 'aside', 'button', 'footer']):
            tag.decompose()

        # Remove elements with specific classes (MS Learn UI elements)
        for class_name in ['feedback-section', 'margin-note', 'op-single-selector']:
            for element in main_content.find_all(class_=class_name):
                element.decompose()

        # Extract text with proper formatting
        text = main_content.get_text(separator='\n', strip=True)

        # Clean up excessive whitespace
        lines = [line.strip() for line in text.split('\n')]
        lines = [line for line in lines if line]  # Remove empty lines
        text = '\n\n'.join(lines)

        return text

    return soup.get_text()


async def fetch_documents(urls: List[str]) -> List[Document]:
    """
    Fetch and parse documents from URLs.

    Args:
        urls: List of URLs to fetch

    Returns:
        List of Document objects
    """
    documents = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        for url in urls:
            try:
                print(f"Fetching: {url}")
                response = await client.get(url)
                response.raise_for_status()

                # Extract content
                content = extract_main_content(response.text, url)

                if content:
                    doc = Document(
                        page_content=content,
                        metadata={
                            "source": url,
                            "source_type": "web",
                            "domain": "learn.microsoft.com",
                            "category": "azure_documentation"
                        }
                    )
                    documents.append(doc)
                    print(f"✓ Fetched: {url} ({len(content)} chars)")
                else:
                    print(f"⚠ No content extracted from: {url}")

            except Exception as e:
                print(f"✗ Failed to fetch {url}: {e}")

    return documents


async def ingest_azure_documentation(knowledge_base_id: str):
    """
    Main ingestion workflow.

    Args:
        knowledge_base_id: UUID of the knowledge base to ingest into
    """
    from dotenv import load_dotenv
    load_dotenv()

    # Import after env is loaded
    from core.database import get_db
    from core.models.knowledge import KnowledgeBase
    from rag.ingestion import DocumentIngestionPipeline

    print(f"🚀 Starting Azure documentation ingestion")
    print(f"📦 Target Knowledge Base ID: {knowledge_base_id}")
    print(f"📄 Fetching {len(AZURE_DOC_URLS)} documentation pages...")

    # Fetch documents
    documents = await fetch_documents(AZURE_DOC_URLS)

    if not documents:
        print("✗ No documents fetched. Aborting.")
        return

    print(f"\n✓ Fetched {len(documents)} documents")
    print(f"📝 Total content size: {sum(len(doc.page_content) for doc in documents):,} characters")

    # Get knowledge base from database
    db = next(get_db())
    kb = db.query(KnowledgeBase).filter_by(id=knowledge_base_id).first()

    if not kb:
        print(f"✗ Knowledge base not found: {knowledge_base_id}")
        print("   Create a knowledge base first via the API")
        return

    print(f"\n📚 Knowledge Base: {kb.name}")
    print(f"🔧 Chunking strategy: {kb.chunking_strategy.get('method', 'default')}")

    # Ingest documents
    try:
        pipeline = DocumentIngestionPipeline(knowledge_base=kb)

        print(f"\n⚙️  Ingesting documents...")
        await pipeline.ingest_documents(
            documents=documents,
            source_type="web",
            metadata={"source_domain": "learn.microsoft.com"}
        )

        print(f"\n✅ Azure documentation ingested successfully!")
        print(f"📊 Total documents: {len(documents)}")
        print(f"🎯 Knowledge base ready for Azure Admin Agent")

    except Exception as e:
        print(f"\n✗ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/ingest_azure_docs.py <knowledge_base_id>")
        print("\nExample:")
        print("  python scripts/ingest_azure_docs.py 123e4567-e89b-12d3-a456-426614174000")
        print("\nNote: Create a knowledge base first via the API:")
        print("  POST /api/knowledge-bases")
        sys.exit(1)

    knowledge_base_id = sys.argv[1]

    # Validate UUID format (basic check)
    if len(knowledge_base_id) != 36 or knowledge_base_id.count('-') != 4:
        print(f"✗ Invalid knowledge base ID format: {knowledge_base_id}")
        print("   Expected UUID format: 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

    # Run ingestion
    asyncio.run(ingest_azure_documentation(knowledge_base_id))


if __name__ == "__main__":
    main()

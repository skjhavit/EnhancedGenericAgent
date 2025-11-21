#!/usr/bin/env python3
"""
Azure Knowledge Base Ingestion Script

Ingests curated Azure documentation from knowledge_base/azure/ directory
into the platform's vector store for RAG-enhanced agent responses.

Usage:
    python scripts/ingest_azure_knowledge_base.py <knowledge_base_id>

Example:
    python scripts/ingest_azure_knowledge_base.py 123e4567-e89b-12d3-a456-426614174000
"""

import asyncio
import sys
import os
from pathlib import Path

# Add backend to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from langchain_core.documents import Document
from typing import List


def load_markdown_files(directory: Path) -> List[Document]:
    """
    Load all markdown files from a directory into Document objects.

    Args:
        directory: Path to directory containing .md files

    Returns:
        List of Document objects with content and metadata
    """
    documents = []

    # Get all .md files in directory
    md_files = sorted(directory.glob("*.md"))

    if not md_files:
        print(f"⚠️  No markdown files found in {directory}")
        return documents

    print(f"📚 Found {len(md_files)} markdown files")

    for md_file in md_files:
        try:
            # Read file content
            content = md_file.read_text(encoding='utf-8')

            # Extract title from first line (assumes # Title format)
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else md_file.stem

            # Create document
            doc = Document(
                page_content=content,
                metadata={
                    "source": str(md_file),
                    "source_type": "local_markdown",
                    "filename": md_file.name,
                    "title": title,
                    "category": "azure_documentation"
                }
            )

            documents.append(doc)
            print(f"  ✓ Loaded: {md_file.name} ({len(content):,} chars)")

        except Exception as e:
            print(f"  ✗ Error loading {md_file.name}: {e}")

    return documents


async def ingest_knowledge_base(knowledge_base_id: str):
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

    print(f"🚀 Starting Azure Knowledge Base Ingestion")
    print(f"📦 Target Knowledge Base ID: {knowledge_base_id}")

    # Get knowledge base directory
    kb_dir = Path(__file__).parent.parent / "knowledge_base" / "azure"

    if not kb_dir.exists():
        print(f"✗ Knowledge base directory not found: {kb_dir}")
        print("   Make sure you're running from the project root")
        return

    print(f"📁 Loading from: {kb_dir}")

    # Load all markdown documents
    documents = load_markdown_files(kb_dir)

    if not documents:
        print("✗ No documents to ingest. Aborting.")
        return

    print(f"\n✓ Loaded {len(documents)} documents")
    print(f"📝 Total content size: {sum(len(doc.page_content) for doc in documents):,} characters")

    # Get knowledge base from database
    db = next(get_db())
    kb = db.query(KnowledgeBase).filter_by(id=knowledge_base_id).first()

    if not kb:
        print(f"\n✗ Knowledge base not found: {knowledge_base_id}")
        print("   Create a knowledge base first via the API:")
        print("   POST /api/knowledge-bases")
        return

    print(f"\n📚 Knowledge Base: {kb.name}")
    print(f"🔧 Chunking strategy: {kb.chunking_strategy.get('method', 'default')}")

    # Ingest documents
    try:
        pipeline = DocumentIngestionPipeline(knowledge_base=kb)

        print(f"\n⚙️  Ingesting documents into vector store...")

        await pipeline.ingest_documents(
            documents=documents,
            source_type="local_markdown",
            metadata={
                "source_directory": "knowledge_base/azure",
                "ingestion_type": "curated_documentation"
            }
        )

        print(f"\n✅ Azure Knowledge Base ingested successfully!")
        print(f"📊 Summary:")
        print(f"   - Documents ingested: {len(documents)}")
        print(f"   - Total characters: {sum(len(doc.page_content) for doc in documents):,}")
        print(f"   - Vector store: {kb.vectorstore_config.get('provider', 'unknown')}")
        print(f"   - Collection: {kb.vectorstore_config.get('collection_name', kb.id)}")

        print(f"\n🎯 Next Steps:")
        print(f"   1. Create an Azure Admin Agent via API")
        print(f"   2. Link this knowledge base (ID: {knowledge_base_id})")
        print(f"   3. Enable Azure tools in agent configuration")
        print(f"   4. Test with questions like:")
        print(f"      - 'What is a User Principal Name?'")
        print(f"      - 'Explain security groups vs M365 groups'")
        print(f"      - 'How do I create a secure app registration?'")

    except Exception as e:
        print(f"\n✗ Ingestion failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("❌ Error: Knowledge base ID required")
        print("\nUsage:")
        print("  python scripts/ingest_azure_knowledge_base.py <knowledge_base_id>")
        print("\nExample:")
        print("  python scripts/ingest_azure_knowledge_base.py 123e4567-e89b-12d3-a456-426614174000")
        print("\nDocuments to be ingested:")

        # List available documents
        kb_dir = Path(__file__).parent.parent / "knowledge_base" / "azure"
        if kb_dir.exists():
            md_files = sorted(kb_dir.glob("*.md"))
            if md_files:
                print(f"  Found {len(md_files)} documents in knowledge_base/azure/:")
                for md_file in md_files:
                    size_kb = md_file.stat().st_size / 1024
                    print(f"    - {md_file.name} ({size_kb:.1f} KB)")
            else:
                print("  ⚠️  No .md files found in knowledge_base/azure/")
        else:
            print("  ⚠️  Directory knowledge_base/azure/ not found")

        print("\nNote: Create a knowledge base first via:")
        print("  POST /api/knowledge-bases")

        sys.exit(1)

    knowledge_base_id = sys.argv[1]

    # Validate UUID format (basic check)
    if len(knowledge_base_id) != 36 or knowledge_base_id.count('-') != 4:
        print(f"❌ Invalid knowledge base ID format: {knowledge_base_id}")
        print("   Expected UUID format: 123e4567-e89b-12d3-a456-426614174000")
        sys.exit(1)

    # Run ingestion
    asyncio.run(ingest_knowledge_base(knowledge_base_id))


if __name__ == "__main__":
    main()

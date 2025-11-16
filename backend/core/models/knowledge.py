"""Knowledge base and document models."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


# Association table for many-to-many relationship between agents and knowledge bases
agent_knowledge_links = Table(
    "agent_knowledge_links",
    Base.metadata,
    Column("agent_id", UUID(as_uuid=True), ForeignKey("agents.id"), primary_key=True),
    Column("knowledge_base_id", UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), primary_key=True),
    Column("created_at", DateTime, default=datetime.utcnow, nullable=False),
)


class KnowledgeBase(Base):
    """Knowledge base containing documents for RAG."""

    __tablename__ = "knowledge_bases"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Vector store configuration
    vectorstore_config = Column(JSON, nullable=False)  # {provider, collection_name, etc.}

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agents = relationship(
        "Agent",
        secondary="agent_knowledge_links",
        back_populates="knowledge_bases"
    )
    documents = relationship("Document", back_populates="knowledge_base", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<KnowledgeBase(id={self.id}, name={self.name})>"


class Document(Base):
    """Document stored in a knowledge base."""

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    knowledge_base_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_bases.id"), nullable=False)

    # File information
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)  # Path to stored file
    file_type = Column(String, nullable=False)  # pdf, docx, txt, etc.
    file_size = Column(String, nullable=True)  # File size in bytes

    # Processing metadata
    file_metadata = Column(JSON, default=dict, nullable=False)  # {chunks_count, embedding_model, etc.}
    processing_status = Column(String, default="pending", nullable=False)  # pending, processing, completed, failed

    # Timestamps
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    processed_at = Column(DateTime, nullable=True)

    # Relationships
    knowledge_base = relationship("KnowledgeBase", back_populates="documents")

    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, status={self.processing_status})>"

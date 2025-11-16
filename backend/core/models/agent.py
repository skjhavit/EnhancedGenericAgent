"""Agent model."""

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from core.database import Base


class Agent(Base):
    """Agent model representing a configured AI agent."""

    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # System prompt template (Jinja2 template)
    system_prompt_template = Column(Text, nullable=False)

    # Configuration stored as JSON
    llm_config = Column(JSON, nullable=False)  # {provider, model, temperature, etc.}
    embedding_config = Column(JSON, nullable=False)  # {provider, model, etc.}

    # Tool configuration
    enabled_tools = Column(JSON, default=list, nullable=False)  # List of tool names
    write_operation_tools = Column(JSON, default=list, nullable=False)  # Tools requiring consent

    # Metadata
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    creator = relationship("User", back_populates="created_agents", foreign_keys=[created_by])
    knowledge_bases = relationship(
        "KnowledgeBase",
        secondary="agent_knowledge_links",
        back_populates="agents"
    )
    chat_sessions = relationship("ChatSession", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Agent(id={self.id}, name={self.name})>"

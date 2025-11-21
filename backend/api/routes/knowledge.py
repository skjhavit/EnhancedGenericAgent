"""Knowledge base management routes."""

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from uuid import UUID
from datetime import datetime

from core.database import get_db
from core.models import User, KnowledgeBase, Document
from core.security import get_current_user

router = APIRouter()


# Request/Response models
class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str | None
    vectorstore_config: dict
    created_at: datetime
    document_count: int

    class Config:
        from_attributes = True


class CreateKnowledgeBaseRequest(BaseModel):
    name: str
    description: str | None = None
    vectorstore_config: dict = {"provider": "chromadb"}


class DocumentResponse(BaseModel):
    id: str
    filename: str
    file_type: str
    file_size: str | None
    processing_status: str
    uploaded_at: datetime
    processed_at: datetime | None

    class Config:
        from_attributes = True


@router.get("", response_model=List[KnowledgeBaseResponse])
async def list_knowledge_bases(
    db: AsyncSession = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    """List all knowledge bases."""
    result = await db.execute(
        select(KnowledgeBase)
        .limit(limit)
        .offset(offset)
    )
    knowledge_bases = result.scalars().all()

    responses = []
    for kb in knowledge_bases:
        doc_count_result = await db.execute(
            select(Document).where(Document.knowledge_base_id == kb.id)
        )
        doc_count = len(doc_count_result.scalars().all())

        responses.append(KnowledgeBaseResponse(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            vectorstore_config=kb.vectorstore_config,
            created_at=kb.created_at,
            document_count=doc_count,
        ))

    return responses


@router.post("", response_model=KnowledgeBaseResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_base(
    request: CreateKnowledgeBaseRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new knowledge base."""
    kb = KnowledgeBase(
        name=request.name,
        description=request.description,
        vectorstore_config=request.vectorstore_config,
    )

    db.add(kb)
    await db.commit()
    await db.refresh(kb)

    return KnowledgeBaseResponse(
        id=str(kb.id),
        name=kb.name,
        description=kb.description,
        vectorstore_config=kb.vectorstore_config,
        created_at=kb.created_at,
        document_count=0,
    )


@router.get("/{kb_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    kb_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List all documents in a knowledge base."""
    result = await db.execute(
        select(Document).where(Document.knowledge_base_id == UUID(kb_id))
    )
    documents = result.scalars().all()

    return [
        DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            file_type=doc.file_type,
            file_size=doc.file_size,
            processing_status=doc.processing_status,
            uploaded_at=doc.uploaded_at,
            processed_at=doc.processed_at,
        )
        for doc in documents
    ]


@router.post("/{kb_id}/upload", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Upload a document to a knowledge base."""
    # Verify knowledge base exists
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == UUID(kb_id)))
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    # TODO: Save file to disk/S3
    # TODO: Queue document processing task (Celery)

    # Create document record
    import os
    file_type = os.path.splitext(file.filename)[1].lstrip('.')

    document = Document(
        knowledge_base_id=UUID(kb_id),
        filename=file.filename,
        file_path=f"./uploads/{kb_id}/{file.filename}",  # Placeholder
        file_type=file_type,
        file_size=str(file.size) if hasattr(file, 'size') else None,
        processing_status="pending",
    )

    db.add(document)
    await db.commit()
    await db.refresh(document)

    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        processing_status=document.processing_status,
        uploaded_at=document.uploaded_at,
        processed_at=document.processed_at,
    )


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_knowledge_base(
    kb_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a knowledge base and all its documents."""
    result = await db.execute(select(KnowledgeBase).where(KnowledgeBase.id == UUID(kb_id)))
    kb = result.scalar_one_or_none()

    if not kb:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Knowledge base not found",
        )

    await db.delete(kb)
    await db.commit()

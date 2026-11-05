"""
Document upload & management API router.
"""
from __future__ import annotations

import os
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.core.logging_config import logger
from app.models.schemas import DocumentMetadata
from app.services.document_processor import document_processor
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/documents", tags=["Documents"])

# Import shared document store
from app.api.translate import get_document_store


@router.post("/upload", response_model=DocumentMetadata, summary="Upload a document for translation")
async def upload_document(
    file: UploadFile = File(..., description="PDF, DOCX, PPTX, TXT, or MD file"),
    subject_domain: Optional[str] = Form(None, description="Academic domain (e.g. mathematics, biology)"),
):
    """
    Upload an academic document. The server extracts text, chunks it, and
    indexes it in the vector store for RAG-enhanced translation.
    """
    settings = get_settings()

    # Validate file type
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in settings.allowed_extensions_set:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {settings.allowed_extensions}",
        )

    file_bytes = await file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > settings.max_upload_size_mb:
        raise HTTPException(
            status_code=413,
            detail=f"File too large ({size_mb:.1f} MB). Maximum: {settings.max_upload_size_mb} MB",
        )

    # Process document
    try:
        doc_data = document_processor.process(file_bytes, filename, len(file_bytes))
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    if subject_domain:
        doc_data["subject_domain"] = subject_domain

    # Index in vector store
    chunks = document_processor.chunk_text(
        doc_data["text"],
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
    )
    try:
        vector_store.index_document(
            document_id=doc_data["document_id"],
            chunks=chunks,
            metadata={
                "filename": filename,
                "file_type": ext,
                "domain": subject_domain or "general",
            },
        )
        doc_data["indexed"] = True
    except Exception as exc:
        logger.warning("Vector indexing skipped for %s: %s", filename, exc)

    # Register in shared document store
    get_document_store()[doc_data["document_id"]] = doc_data

    logger.info(
        "Document uploaded: %s | id=%s | pages=%d | chunks=%d",
        filename, doc_data["document_id"], doc_data["page_count"], len(chunks),
    )

    return DocumentMetadata(
        document_id=doc_data["document_id"],
        filename=filename,
        file_type=ext,
        size_bytes=doc_data["size_bytes"],
        page_count=doc_data["page_count"],
        subject_domain=subject_domain,
        upload_timestamp=doc_data["upload_timestamp"],
        indexed=doc_data["indexed"],
    )


@router.get("/", summary="List uploaded documents")
async def list_documents():
    """Return all documents currently loaded in this session."""
    store = get_document_store()
    return [
        {
            "document_id": d["document_id"],
            "filename": d["filename"],
            "file_type": d["file_type"],
            "size_bytes": d["size_bytes"],
            "page_count": d["page_count"],
            "subject_domain": d.get("subject_domain"),
            "upload_timestamp": d["upload_timestamp"],
            "indexed": d.get("indexed", False),
        }
        for d in store.values()
    ]


@router.delete("/{document_id}", summary="Delete a document")
async def delete_document(document_id: str):
    """Remove a document from the session and vector store."""
    store = get_document_store()
    if document_id not in store:
        raise HTTPException(status_code=404, detail="Document not found.")
    del store[document_id]
    try:
        vector_store.delete_document(document_id)
    except Exception as exc:
        logger.warning("Could not delete from vector store: %s", exc)
    return {"message": f"Document {document_id} deleted."}

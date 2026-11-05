"""
Translation API router — text and document translation endpoints.
"""
from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query

from app.core.config import get_settings
from app.core.logging_config import logger
from app.models.schemas import (
    DocumentTranslationRequest,
    DocumentTranslationStatus,
    LanguageCode,
    TranslationRequest,
    TranslationResult,
)
from app.services.translation_agent import translation_agent

router = APIRouter(prefix="/api/translate", tags=["Translation"])
_executor = ThreadPoolExecutor(max_workers=4)

# In-memory job store (production: use Redis or a database)
_jobs: dict[str, DocumentTranslationStatus] = {}
# In-memory document store (keyed by document_id)
_documents: dict[str, dict] = {}


def _register_document(doc_data: dict) -> None:
    """Register a processed document so translation endpoints can access it."""
    _documents[doc_data["document_id"]] = doc_data


def get_document_store() -> dict[str, dict]:
    return _documents


# ── Text translation ───────────────────────────────────────────────────────────

@router.post("/text", response_model=TranslationResult, summary="Translate a text snippet")
async def translate_text(request: TranslationRequest):
    """
    Translate a piece of academic text to a target regional language.
    Uses IBM Granite (watsonx.ai) + RAG glossary enrichment.
    """
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(
            _executor,
            lambda: translation_agent.translate_text(
                text=request.text,
                target_language=request.target_language.value,
                source_language=request.source_language,
                subject_domain=request.subject_domain,
            ),
        )
        return result
    except Exception as exc:
        logger.error("Text translation error: %s", exc)
        msg = str(exc)
        # Surface a clear message for the most common failure modes
        if (
            "your_ibm_watsonx_api_key_here" in msg
            or "API key" in msg.lower()
            or "401" in msg
            or "Unauthorized" in msg
            or "BXNIM0415E" in msg
            or "Provided API key could not be found" in msg
            or "authenticating connection" in msg.lower()
        ):
            msg = ("IBM watsonx.ai credentials not configured. "
                   "Open the .env file and set WATSONX_API_KEY and WATSONX_PROJECT_ID "
                   "with your real IBM Cloud values, then restart the server.")
        elif "403" in msg or "Forbidden" in msg:
            msg = ("IBM watsonx.ai returned 403 Forbidden. "
                   "Check that your WATSONX_PROJECT_ID is correct and the Granite model "
                   "is enabled for your account at cloud.ibm.com.")
        elif "ConnectionError" in msg or "Failed to establish" in msg or "Name or service" in msg:
            msg = "Cannot reach IBM watsonx.ai. Check your internet connection and WATSONX_URL in .env."
        raise HTTPException(status_code=500, detail=msg)


@router.post("/document", response_model=DocumentTranslationStatus, summary="Translate an uploaded document")
async def translate_document(
    request: DocumentTranslationRequest,
    background_tasks: BackgroundTasks,
):
    """
    Translate a previously-uploaded document to one or more target languages.
    The job runs in the background; poll /api/translate/status/{job_id} for results.
    """
    doc = _documents.get(request.document_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Document '{request.document_id}' not found. Upload it first.",
        )

    import uuid
    job_id = str(uuid.uuid4())
    status = DocumentTranslationStatus(
        job_id=job_id,
        document_id=request.document_id,
        document_name=doc["filename"],
        target_languages=[lang.value for lang in request.target_languages],
        status="pending",
        progress=0.0,
    )
    _jobs[job_id] = status

    background_tasks.add_task(
        _run_document_translation,
        job_id=job_id,
        doc=doc,
        target_languages=[lang.value for lang in request.target_languages],
        subject_domain=request.subject_domain,
    )
    return status


def _run_document_translation(
    job_id: str, doc: dict, target_languages: List[str], subject_domain: Optional[str]
):
    status = _jobs[job_id]
    status.status = "processing"
    try:
        finished = translation_agent.translate_document(
            document_data=doc,
            target_languages=target_languages,
            subject_domain=subject_domain,
        )
        status.status = "completed"
        status.progress = 100.0
        status.results = finished.results
    except Exception as exc:
        logger.error("Document translation job %s failed: %s", job_id, exc)
        status.status = "failed"
        status.error = str(exc)


@router.get("/status/{job_id}", response_model=DocumentTranslationStatus, summary="Check translation job status")
async def get_job_status(job_id: str):
    """Poll the status of a background document translation job."""
    status = _jobs.get(job_id)
    if not status:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")
    return status


@router.get("/languages", summary="List supported languages")
async def get_supported_languages():
    """Return all supported translation target languages."""
    settings = get_settings()
    names = settings.language_names_dict
    return [
        {"code": code, "name": names.get(code, code)}
        for code in settings.supported_language_list
    ]

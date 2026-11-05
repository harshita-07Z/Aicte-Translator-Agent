"""
Pydantic request/response models for the API.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ── Language codes ─────────────────────────────────────────────────────────────
class LanguageCode(str, Enum):
    hi = "hi"   # Hindi
    mr = "mr"   # Marathi
    ta = "ta"   # Tamil
    bn = "bn"   # Bengali
    te = "te"   # Telugu
    kn = "kn"   # Kannada
    gu = "gu"   # Gujarati
    pa = "pa"   # Punjabi
    ml = "ml"   # Malayalam
    or_ = "or"  # Odia
    ur = "ur"   # Urdu
    en = "en"   # English


# ── Translation request / response ────────────────────────────────────────────
class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=50_000, description="Text to translate")
    target_language: LanguageCode = Field(..., description="Target language code")
    source_language: Optional[str] = Field(
        None, description="Source language code (auto-detect if omitted)"
    )
    subject_domain: Optional[str] = Field(
        None, description="Academic domain e.g. 'mathematics', 'biology'"
    )
    preserve_formatting: bool = Field(True, description="Preserve markdown/formatting")


class TranslationResult(BaseModel):
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    target_language_name: str
    subject_domain: Optional[str]
    glossary_terms_used: List[str] = []
    model_used: str
    confidence: Optional[float] = None


# ── Document translation ───────────────────────────────────────────────────────
class DocumentTranslationRequest(BaseModel):
    document_id: str = Field(..., description="ID of an already-uploaded document")
    target_languages: List[LanguageCode] = Field(
        ..., min_length=1, description="One or more target languages"
    )
    subject_domain: Optional[str] = None
    preserve_formatting: bool = True


class DocumentTranslationStatus(BaseModel):
    job_id: str
    document_id: str
    document_name: str
    target_languages: List[str]
    status: str  # pending | processing | completed | failed
    progress: float = 0.0
    results: Dict[str, Any] = {}
    error: Optional[str] = None


# ── Document metadata ──────────────────────────────────────────────────────────
class DocumentMetadata(BaseModel):
    document_id: str
    filename: str
    file_type: str
    size_bytes: int
    page_count: int
    language: Optional[str] = None
    subject_domain: Optional[str] = None
    upload_timestamp: str
    indexed: bool = False


# ── Glossary ───────────────────────────────────────────────────────────────────
class GlossaryEntry(BaseModel):
    term: str
    domain: str
    translations: Dict[str, str]  # lang_code -> translated term
    definition: Optional[str] = None
    context: Optional[str] = None


# ── Health check ──────────────────────────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    version: str
    watsonx_connected: bool
    vector_store_ready: bool
    glossary_loaded: bool
    supported_languages: List[str]

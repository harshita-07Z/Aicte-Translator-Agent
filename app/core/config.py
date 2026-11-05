"""
Application configuration — loads from .env via pydantic-settings.
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── IBM watsonx.ai ────────────────────────────────────────────────────────
    watsonx_api_key: str = Field(..., description="IBM watsonx.ai API key")
    watsonx_project_id: str = Field(..., description="IBM watsonx.ai project ID")
    watsonx_url: str = Field(
        "https://us-south.ml.cloud.ibm.com",
        description="IBM watsonx.ai service URL",
    )
    granite_model_id: str = Field(
        "ibm/granite-4-h-small",
        description="Primary IBM Granite model ID",
    )
    granite_3_model_id: str = Field(
        "ibm/granite-4-h-small",
        description="Granite 4.x model ID",
    )

    # ── Watson Language Translator (optional) ─────────────────────────────────
    watson_language_translator_apikey: str = Field(
        "", description="Watson Language Translator API key"
    )
    watson_language_translator_url: str = Field(
        "", description="Watson Language Translator URL"
    )

    # ── App ───────────────────────────────────────────────────────────────────
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_debug: bool = True
    app_secret_key: str = "change_me_in_production"

    # ── RAG / Vector Store ────────────────────────────────────────────────────
    chroma_persist_dir: str = "./data/chroma_db"
    embedding_model: str = (
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    )
    chunk_size: int = 512
    chunk_overlap: int = 64
    rag_top_k: int = 5

    # ── Uploads ───────────────────────────────────────────────────────────────
    upload_dir: str = "./data/uploads"
    max_upload_size_mb: int = 50
    allowed_extensions: str = "pdf,docx,pptx,txt,md"

    # ── Languages ─────────────────────────────────────────────────────────────
    supported_languages: str = "hi,mr,ta,bn,te,kn,gu,pa,ml,or,ur,en"
    language_names: str = (
        '{"hi":"Hindi","mr":"Marathi","ta":"Tamil","bn":"Bengali",'
        '"te":"Telugu","kn":"Kannada","gu":"Gujarati","pa":"Punjabi",'
        '"ml":"Malayalam","or":"Odia","ur":"Urdu","en":"English"}'
    )

    # ── Logging ───────────────────────────────────────────────────────────────
    log_level: str = "INFO"
    log_file: str = "./logs/app.log"

    # ── Derived properties ────────────────────────────────────────────────────
    @property
    def supported_language_list(self) -> List[str]:
        return [lang.strip() for lang in self.supported_languages.split(",")]

    @property
    def language_names_dict(self) -> Dict[str, str]:
        return json.loads(self.language_names)

    @property
    def allowed_extensions_set(self) -> set:
        return {ext.strip().lower() for ext in self.allowed_extensions.split(",")}

    @property
    def upload_path(self) -> Path:
        p = Path(self.upload_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def chroma_path(self) -> Path:
        p = Path(self.chroma_persist_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

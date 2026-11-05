"""
Translation Agent — orchestrates RAG retrieval + Granite LLM
for context-aware, pedagogically sound multi-language translation.
"""
from __future__ import annotations

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.logging_config import logger
from app.models.schemas import TranslationResult, DocumentTranslationStatus
from app.services.glossary_service import glossary_service
from app.services.granite_llm import granite_llm
from app.services.vector_store import vector_store

# Thread pool for blocking LLM calls
_executor = ThreadPoolExecutor(max_workers=4)


class TranslationAgent:
    """
    Retrieval-Augmented Generation (RAG) Translation Agent.

    Workflow:
        1. Detect source language if not provided.
        2. Retrieve relevant context chunks from vector store (RAG).
        3. Look up glossary terms in the text.
        4. Build an enriched prompt with RAG context + glossary.
        5. Call IBM Granite for the final translation.
        6. Return structured result.
    """

    def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        subject_domain: Optional[str] = None,
        document_id: Optional[str] = None,
        preserve_formatting: bool = True,
    ) -> TranslationResult:
        """
        Translate a text snippet with RAG-augmented context.
        """
        settings = get_settings()

        # 1. Auto-detect source language
        if not source_language:
            source_language = granite_llm.detect_language(text)

        # 2. RAG retrieval — find similar academic content already indexed
        rag_context = ""
        try:
            search_results = vector_store.search(
                query=text[:500],  # use first 500 chars as query
                n_results=settings.rag_top_k,
                filter_document_id=document_id,
                filter_domain=subject_domain,
            )
            if search_results:
                context_chunks = [r["text"] for r in search_results[:3]]
                rag_context = "\n---\n".join(context_chunks)
        except Exception as exc:
            logger.warning("RAG retrieval skipped: %s", exc)

        # 3. Glossary context
        glossary_context = glossary_service.build_glossary_context(
            text, target_language, domain=subject_domain
        )
        glossary_terms = glossary_service.get_term_names_used(
            text, target_language, domain=subject_domain
        )

        # 4 + 5. Call IBM Granite
        translated_text = granite_llm.translate(
            text=text,
            target_lang=target_language,
            source_lang=source_language,
            domain=subject_domain,
            glossary_context=glossary_context,
            rag_context=rag_context,
        )

        lang_names = settings.language_names_dict
        return TranslationResult(
            original_text=text,
            translated_text=translated_text,
            source_language=source_language,
            target_language=target_language,
            target_language_name=lang_names.get(target_language, target_language),
            subject_domain=subject_domain,
            glossary_terms_used=glossary_terms,
            model_used=granite_llm.model_id,
        )

    def translate_document(
        self,
        document_data: Dict,
        target_languages: List[str],
        subject_domain: Optional[str] = None,
    ) -> DocumentTranslationStatus:
        """
        Translate a processed document into multiple languages.
        Splits the document text into sections and translates each.
        """
        settings = get_settings()
        doc_id = document_data["document_id"]
        filename = document_data["filename"]
        text = document_data["text"]
        job_id = str(uuid.uuid4())

        status = DocumentTranslationStatus(
            job_id=job_id,
            document_id=doc_id,
            document_name=filename,
            target_languages=target_languages,
            status="processing",
            progress=0.0,
        )

        # Split text into manageable sections (~2000 chars each)
        sections = self._split_into_sections(text, max_chars=2000)
        total_tasks = len(sections) * len(target_languages)
        completed = 0
        results: Dict[str, str] = {}

        for lang in target_languages:
            lang_parts: List[str] = []
            for section in sections:
                try:
                    result = self.translate_text(
                        text=section,
                        target_language=lang,
                        subject_domain=subject_domain,
                        document_id=doc_id,
                    )
                    lang_parts.append(result.translated_text)
                except Exception as exc:
                    logger.error(
                        "Failed to translate section for lang=%s doc=%s: %s",
                        lang, doc_id, exc,
                    )
                    lang_parts.append(f"[Translation error: {exc}]")
                completed += 1
                status.progress = round(completed / total_tasks * 100, 1)

            results[lang] = "\n\n".join(lang_parts)

        status.status = "completed"
        status.progress = 100.0
        status.results = results
        return status

    # ── Helpers ────────────────────────────────────────────────────────────────

    def _split_into_sections(self, text: str, max_chars: int = 2000) -> List[str]:
        """
        Split text into sections of at most *max_chars*, breaking on paragraph
        boundaries where possible.
        """
        paragraphs = text.split("\n\n")
        sections: List[str] = []
        current = ""

        for para in paragraphs:
            if len(current) + len(para) + 2 > max_chars and current:
                sections.append(current.strip())
                current = para
            else:
                current = current + "\n\n" + para if current else para

        if current.strip():
            sections.append(current.strip())

        return sections or [text]


# Singleton
translation_agent = TranslationAgent()

"""
IBM Granite / watsonx.ai LLM service.

Handles authentication, prompt construction, and inference calls
to IBM Granite models via ibm-watsonx-ai SDK.
"""
from __future__ import annotations

from typing import Optional

from app.core.config import get_settings
from app.core.logging_config import logger


# Language names for prompts
LANGUAGE_NAMES: dict[str, str] = {
    "hi": "Hindi",
    "mr": "Marathi",
    "ta": "Tamil",
    "bn": "Bengali",
    "te": "Telugu",
    "kn": "Kannada",
    "gu": "Gujarati",
    "pa": "Punjabi",
    "ml": "Malayalam",
    "or": "Odia",
    "ur": "Urdu",
    "en": "English",
}

# Default generation parameters for IBM Granite chat API (conservative for translation)
DEFAULT_PARAMS = {
    "max_tokens": 2048,
    "temperature": 0.2,
    "top_p": 0.9,
    "repetition_penalty": 1.05,
}


class GraniteLLMService:
    """
    Wraps IBM watsonx.ai Model inference for multilingual academic translation.
    """

    def __init__(self) -> None:
        self._model = None
        self._model_3 = None
        self._connected = False

    def _get_credentials(self):
        settings = get_settings()
        return {
            "url": settings.watsonx_url,
            "apikey": settings.watsonx_api_key,
        }

    def _load_model(self, model_id: str):
        """Lazy-load a watsonx.ai Model instance."""
        from ibm_watsonx_ai import APIClient, Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams

        settings = get_settings()
        credentials = Credentials(
            url=settings.watsonx_url,
            api_key=settings.watsonx_api_key,
        )
        client = APIClient(credentials)
        model = ModelInference(
            model_id=model_id,
            api_client=client,
            project_id=settings.watsonx_project_id,
            params=DEFAULT_PARAMS,
        )
        return model

    def _ensure_connected(self) -> None:
        if self._model is None:
            settings = get_settings()
            try:
                logger.info("Connecting to IBM watsonx.ai — model: %s", settings.granite_model_id)
                self._model = self._load_model(settings.granite_model_id)
                self._connected = True
                logger.info("IBM Granite model loaded successfully")
            except Exception as exc:
                logger.error("Failed to load IBM Granite model: %s", exc)
                raise

    def _build_chat_messages(
        self,
        text: str,
        target_lang: str,
        source_lang: str,
        domain: Optional[str],
        glossary_context: str,
    ) -> list:
        """
        Build chat messages list for IBM Granite chat API (/v1/text/chat).
        Uses the standard OpenAI-compatible messages format.
        """
        target_lang_name = LANGUAGE_NAMES.get(target_lang, target_lang)
        source_lang_name = LANGUAGE_NAMES.get(source_lang, source_lang) if source_lang else "the source language"
        domain_hint = f" The content is from the academic domain of **{domain}**." if domain else ""

        system_content = (
            "You are an expert academic translator specializing in Indian regional languages. "
            "Your translations are accurate, contextually appropriate, and preserve educational integrity. "
            "You maintain technical terminology exactly as specified in any glossary provided. "
            "You preserve the structure, formatting, and meaning of the original text."
        )

        user_parts = [
            f"Translate the following academic content from {source_lang_name} to {target_lang_name}.{domain_hint}",
            "Requirements:",
            "- Preserve all technical terms, formulas, and numeric values exactly.",
            "- Maintain the original structure (headings, bullet points, numbered lists).",
            "- Use natural, pedagogically appropriate language suitable for students.",
            "- Do NOT add explanations or commentary—translate only.",
        ]

        if glossary_context:
            user_parts.append("")
            user_parts.append(glossary_context)

        user_parts.extend([
            "",
            "Content to translate:",
            "---",
            text,
            "---",
            "",
            f"Provide only the translation in {target_lang_name}, nothing else.",
        ])

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": "\n".join(user_parts)},
        ]

    def translate(
        self,
        text: str,
        target_lang: str,
        source_lang: str = "en",
        domain: Optional[str] = None,
        glossary_context: str = "",
        rag_context: str = "",
    ) -> str:
        """
        Translate *text* to *target_lang* using IBM Granite.

        Returns the translated text string.
        """
        self._ensure_connected()

        # If RAG context is available, prepend it to glossary context
        full_context = ""
        if rag_context:
            full_context += f"Relevant Context from Source Document:\n{rag_context}\n\n"
        if glossary_context:
            full_context += glossary_context

        messages = self._build_chat_messages(
            text=text,
            target_lang=target_lang,
            source_lang=source_lang,
            domain=domain,
            glossary_context=full_context,
        )

        logger.debug(
            "Sending translation request — target: %s, domain: %s, text_len: %d",
            target_lang, domain, len(text),
        )

        try:
            response = self._model.chat(messages=messages)
            # Extract text from chat response structure
            translated = (
                response["choices"][0]["message"]["content"].strip()
                if isinstance(response, dict)
                else str(response).strip()
            )
            logger.info(
                "Translation complete — target: %s, output_len: %d",
                target_lang, len(translated),
            )
            return translated
        except Exception as exc:
            logger.error("Translation failed: %s", exc)
            raise

    def detect_language(self, text: str) -> str:
        """
        Detect the source language of *text*.
        Uses langdetect as primary; falls back to 'en'.
        """
        try:
            from langdetect import detect
            lang = detect(text)
            logger.debug("Detected language: %s", lang)
            return lang
        except Exception:
            return "en"

    def health_check(self) -> bool:
        """Return True if watsonx.ai is reachable."""
        try:
            self._ensure_connected()
            return True
        except Exception:
            return False

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def model_id(self) -> str:
        return get_settings().granite_model_id


# Singleton
granite_llm = GraniteLLMService()

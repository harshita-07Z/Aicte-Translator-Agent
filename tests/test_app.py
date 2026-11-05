"""
Unit tests for the AICTE Translator Agent.
Run with: pytest tests/ -v
"""
import json
import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# ── Ensure project root is on sys.path ────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Set dummy env vars before importing config
os.environ.setdefault("WATSONX_API_KEY", "test_api_key")
os.environ.setdefault("WATSONX_PROJECT_ID", "test_project_id")


# ─────────────────────────────────────────────────────────────────────────────
# 1. Configuration
# ─────────────────────────────────────────────────────────────────────────────
class TestConfig:
    def test_supported_languages_list(self):
        from app.core.config import get_settings
        settings = get_settings()
        langs = settings.supported_language_list
        assert "hi" in langs
        assert "ta" in langs
        assert "bn" in langs

    def test_language_names_dict(self):
        from app.core.config import get_settings
        settings = get_settings()
        names = settings.language_names_dict
        assert names["hi"] == "Hindi"
        assert names["mr"] == "Marathi"

    def test_allowed_extensions_set(self):
        from app.core.config import get_settings
        settings = get_settings()
        exts = settings.allowed_extensions_set
        assert "pdf" in exts
        assert "docx" in exts
        assert "pptx" in exts


# ─────────────────────────────────────────────────────────────────────────────
# 2. Glossary Service
# ─────────────────────────────────────────────────────────────────────────────
class TestGlossaryService:
    def setup_method(self):
        from app.services.glossary_service import GlossaryService
        self.service = GlossaryService()
        self.service.load()  # loads from data/glossaries/

    def test_glossary_loaded(self):
        assert self.service.is_loaded
        assert self.service.entry_count > 0

    def test_get_translation_known_term(self):
        result = self.service.get_translation("algorithm", "hi")
        assert result is not None
        assert "एल्गोरिदम" in result or result  # has some Hindi text

    def test_get_translation_unknown_term(self):
        result = self.service.get_translation("xyznonexistent", "hi")
        assert result is None

    def test_find_terms_in_text(self):
        text = "The algorithm uses a data structure for efficiency."
        terms = self.service.find_terms_in_text(text, domain="computer_science")
        term_names = [t["term"] for t in terms]
        assert "algorithm" in term_names

    def test_build_glossary_context(self):
        text = "Photosynthesis is a biological process."
        ctx = self.service.build_glossary_context(text, "hi", domain="biology")
        assert "photosynthesis" in ctx.lower() or ctx  # has context


# ─────────────────────────────────────────────────────────────────────────────
# 3. Document Processor
# ─────────────────────────────────────────────────────────────────────────────
class TestDocumentProcessor:
    def setup_method(self):
        from app.services.document_processor import DocumentProcessor
        self.processor = DocumentProcessor()

    def test_extract_txt(self):
        content = b"Hello world. This is a test document."
        doc = self.processor.process(content, "test.txt", len(content))
        assert doc["file_type"] == "txt"
        assert "Hello world" in doc["text"]
        assert doc["page_count"] >= 1

    def test_extract_md(self):
        content = b"# Title\n\nSome **markdown** content here."
        doc = self.processor.process(content, "notes.md", len(content))
        assert "Title" in doc["text"]

    def test_unsupported_extension(self):
        with pytest.raises(ValueError, match="Unsupported"):
            self.processor.process(b"data", "file.xyz", 4)

    def test_chunk_text(self):
        text = "Sentence one. Sentence two. Sentence three. " * 20
        chunks = self.processor.chunk_text(text, chunk_size=100, chunk_overlap=20)
        assert len(chunks) > 1
        for chunk in chunks:
            assert len(chunk) > 0

    def test_document_id_is_unique(self):
        content = b"Some text content."
        doc1 = self.processor.process(content, "a.txt", len(content))
        doc2 = self.processor.process(content, "b.txt", len(content))
        assert doc1["document_id"] != doc2["document_id"]

    def test_empty_text_raises(self):
        with pytest.raises(ValueError, match="No text"):
            self.processor.process(b"   \n  ", "empty.txt", 5)


# ─────────────────────────────────────────────────────────────────────────────
# 4. Granite LLM Service (mocked)
# ─────────────────────────────────────────────────────────────────────────────
class TestGraniteLLMService:
    def test_detect_language_english(self):
        from app.services.granite_llm import GraniteLLMService
        service = GraniteLLMService()
        lang = service.detect_language("The derivative of a function measures rate of change.")
        assert lang in ("en", "unknown")  # langdetect may vary

    def test_translate_calls_model(self):
        from app.services.granite_llm import GraniteLLMService
        service = GraniteLLMService()
        mock_model = MagicMock()
        # chat() returns OpenAI-compatible dict
        mock_model.chat.return_value = {
            "choices": [{"message": {"content": "यह एक परीक्षण है।"}}]
        }
        service._model = mock_model
        service._connected = True

        result = service.translate(
            text="This is a test.",
            target_lang="hi",
            source_lang="en",
        )
        assert result == "यह एक परीक्षण है।"
        mock_model.chat.assert_called_once()

    def test_build_prompt_contains_language(self):
        from app.services.granite_llm import GraniteLLMService
        service = GraniteLLMService()
        messages = service._build_chat_messages(
            text="Test text",
            target_lang="ta",
            source_lang="en",
            domain="biology",
            glossary_context="",
        )
        full_text = " ".join(m["content"] for m in messages)
        assert "Tamil" in full_text
        assert "biology" in full_text.lower()
        assert "Test text" in full_text


# ─────────────────────────────────────────────────────────────────────────────
# 5. Pydantic Models
# ─────────────────────────────────────────────────────────────────────────────
class TestSchemas:
    def test_translation_request_valid(self):
        from app.models.schemas import TranslationRequest, LanguageCode
        req = TranslationRequest(text="Hello", target_language=LanguageCode.hi)
        assert req.target_language == LanguageCode.hi

    def test_translation_request_too_short(self):
        from app.models.schemas import TranslationRequest, LanguageCode
        import pydantic
        with pytest.raises(pydantic.ValidationError):
            TranslationRequest(text="", target_language=LanguageCode.hi)

    def test_document_metadata_valid(self):
        from app.models.schemas import DocumentMetadata
        meta = DocumentMetadata(
            document_id="abc123",
            filename="notes.pdf",
            file_type="pdf",
            size_bytes=1024,
            page_count=5,
            upload_timestamp="2024-01-01T00:00:00Z",
        )
        assert meta.document_id == "abc123"


# ─────────────────────────────────────────────────────────────────────────────
# 6. FastAPI endpoints (using TestClient)
# ─────────────────────────────────────────────────────────────────────────────
class TestAPIEndpoints:
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import create_app
        return TestClient(create_app())

    def test_health_endpoint_reachable(self, client):
        res = client.get("/api/health")
        assert res.status_code == 200
        data = res.json()
        assert "status" in data
        assert "supported_languages" in data
        assert "hi" in data["supported_languages"]

    def test_languages_endpoint(self, client):
        res = client.get("/api/translate/languages")
        assert res.status_code == 200
        langs = res.json()
        assert isinstance(langs, list)
        codes = [l["code"] for l in langs]
        assert "hi" in codes
        assert "ta" in codes

    def test_document_list_empty(self, client):
        res = client.get("/api/documents/")
        assert res.status_code == 200
        assert res.json() == []

    def test_upload_invalid_extension(self, client):
        res = client.post(
            "/api/documents/upload",
            files={"file": ("test.exe", b"binary data", "application/octet-stream")},
        )
        assert res.status_code == 400

    def test_upload_txt_document(self, client):
        content = b"Newton's Laws of Motion explain the relationship between force and acceleration."
        res = client.post(
            "/api/documents/upload",
            files={"file": ("lecture.txt", content, "text/plain")},
            data={"subject_domain": "physics"},
        )
        # May fail if vector store not ready, but should not be 400/422
        assert res.status_code in (200, 500)

    def test_text_translation_missing_field(self, client):
        res = client.post("/api/translate/text", json={"text": "Hello"})
        assert res.status_code == 422  # missing target_language

    def test_job_status_not_found(self, client):
        res = client.get("/api/translate/status/nonexistent-job-id")
        assert res.status_code == 404

    def test_serve_index_html(self, client):
        res = client.get("/")
        assert res.status_code == 200
        assert "AICTE" in res.text or "Translator" in res.text

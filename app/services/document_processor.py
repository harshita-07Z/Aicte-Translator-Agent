"""
Document processor — extracts plain text from PDF, DOCX, PPTX, TXT, and MD files.
"""
from __future__ import annotations

import io
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from app.core.logging_config import logger


def extract_text_from_pdf(file_bytes: bytes) -> Tuple[str, int]:
    """Return (full_text, page_count) from a PDF byte stream."""
    try:
        import pymupdf as fitz  # PyMuPDF >= 1.24 uses 'pymupdf' package name
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        pages = [page.get_text() for page in doc]
        return "\n\n".join(pages), len(pages)
    except ImportError:
        # Fallback: pypdf
        from pypdf import PdfReader
        reader = PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages), len(pages)


def extract_text_from_docx(file_bytes: bytes) -> Tuple[str, int]:
    """Return (full_text, estimated_pages) from a DOCX byte stream."""
    from docx import Document
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    text = "\n\n".join(paragraphs)
    # Estimate pages: ~3000 chars per page
    page_count = max(1, len(text) // 3000)
    return text, page_count


def extract_text_from_pptx(file_bytes: bytes) -> Tuple[str, int]:
    """Return (full_text, slide_count) from a PPTX byte stream."""
    from pptx import Presentation
    prs = Presentation(io.BytesIO(file_bytes))
    slide_texts = []
    for slide in prs.slides:
        parts = []
        for shape in slide.shapes:
            if hasattr(shape, "text") and shape.text.strip():
                parts.append(shape.text.strip())
        if parts:
            slide_texts.append("\n".join(parts))
    return "\n\n--- Slide Break ---\n\n".join(slide_texts), len(prs.slides)


def extract_text_from_txt(file_bytes: bytes) -> Tuple[str, int]:
    """Return (full_text, 1) from a plain-text / Markdown byte stream."""
    text = file_bytes.decode("utf-8", errors="replace")
    page_count = max(1, len(text) // 3000)
    return text, page_count


EXTRACTORS = {
    "pdf": extract_text_from_pdf,
    "docx": extract_text_from_docx,
    "pptx": extract_text_from_pptx,
    "txt": extract_text_from_txt,
    "md": extract_text_from_txt,
}


class DocumentProcessor:
    """Handles document ingestion, text extraction, and metadata creation."""

    def process(
        self, file_bytes: bytes, filename: str, size_bytes: int
    ) -> Dict:
        """
        Extract text from an uploaded document.

        Returns a dict with:
            document_id, filename, file_type, size_bytes, page_count,
            text, upload_timestamp, indexed
        """
        ext = Path(filename).suffix.lstrip(".").lower()
        extractor = EXTRACTORS.get(ext)
        if extractor is None:
            raise ValueError(f"Unsupported file type: .{ext}")

        logger.info("Processing document: %s (%d bytes)", filename, size_bytes)
        text, page_count = extractor(file_bytes)

        if not text.strip():
            raise ValueError("No text could be extracted from the document.")

        doc_id = str(uuid.uuid4())
        return {
            "document_id": doc_id,
            "filename": filename,
            "file_type": ext,
            "size_bytes": size_bytes,
            "page_count": page_count,
            "text": text,
            "upload_timestamp": datetime.now(timezone.utc).isoformat(),
            "indexed": False,
        }

    def chunk_text(
        self, text: str, chunk_size: int = 512, chunk_overlap: int = 64
    ) -> List[str]:
        """
        Split *text* into overlapping chunks suitable for vector embedding.
        Uses sentence-aware splitting where possible.
        """
        import re
        # Split on sentence boundaries
        sentences = re.split(r"(?<=[.!?])\s+", text)
        chunks: List[str] = []
        current: List[str] = []
        current_len = 0

        for sentence in sentences:
            s_len = len(sentence)
            if current_len + s_len > chunk_size and current:
                chunks.append(" ".join(current))
                # Keep overlap
                overlap_text = " ".join(current)[-chunk_overlap:]
                current = [overlap_text, sentence]
                current_len = len(overlap_text) + s_len
            else:
                current.append(sentence)
                current_len += s_len

        if current:
            chunks.append(" ".join(current))

        return [c.strip() for c in chunks if c.strip()]


document_processor = DocumentProcessor()

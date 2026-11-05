"""
Glossary service — loads academic term glossaries and provides
context-aware lookup to augment translation prompts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict, List, Optional

from app.core.logging_config import logger


GLOSSARY_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "glossaries"


class GlossaryService:
    """Manages multilingual academic glossaries for RAG-enhanced translation."""

    def __init__(self) -> None:
        self._entries: List[Dict] = []
        self._by_term: Dict[str, Dict] = {}
        self._by_domain: Dict[str, List[Dict]] = {}
        self._loaded = False

    def load(self) -> None:
        """Load all JSON glossary files from the glossaries directory."""
        if self._loaded:
            return
        GLOSSARY_DIR.mkdir(parents=True, exist_ok=True)
        count = 0
        for json_file in GLOSSARY_DIR.glob("*.json"):
            try:
                with open(json_file, encoding="utf-8") as f:
                    data = json.load(f)
                if isinstance(data, list):
                    for entry in data:
                        self._index_entry(entry)
                        count += 1
            except Exception as exc:
                logger.warning("Failed to load glossary %s: %s", json_file.name, exc)
        self._loaded = True
        logger.info("Loaded %d glossary entries from %s", count, GLOSSARY_DIR)

    def _index_entry(self, entry: Dict) -> None:
        self._entries.append(entry)
        term_lower = entry.get("term", "").lower()
        self._by_term[term_lower] = entry
        domain = entry.get("domain", "general")
        self._by_domain.setdefault(domain, []).append(entry)

    # ── Public API ─────────────────────────────────────────────────────────────

    def get_translation(self, term: str, target_lang: str) -> Optional[str]:
        """Return the glossary translation for a term in the target language."""
        entry = self._by_term.get(term.lower())
        if entry:
            return entry.get("translations", {}).get(target_lang)
        return None

    def find_terms_in_text(
        self, text: str, domain: Optional[str] = None
    ) -> List[Dict]:
        """
        Find glossary terms present in *text*.
        If *domain* is provided, prioritise entries from that domain.
        """
        self.load()
        found: List[Dict] = []
        text_lower = text.lower()
        candidates = self._by_domain.get(domain, []) + self._entries if domain else self._entries
        seen: set = set()
        for entry in candidates:
            term = entry.get("term", "")
            if term.lower() in seen:
                continue
            pattern = r"\b" + re.escape(term.lower()) + r"\b"
            if re.search(pattern, text_lower):
                found.append(entry)
                seen.add(term.lower())
        return found

    def build_glossary_context(
        self, text: str, target_lang: str, domain: Optional[str] = None
    ) -> str:
        """
        Build a glossary context string to prepend to translation prompts,
        informing the model about correct term translations.
        """
        self.load()
        terms = self.find_terms_in_text(text, domain)
        if not terms:
            return ""
        lines = ["Academic Glossary (use these exact translations):"]
        for entry in terms:
            translated = entry.get("translations", {}).get(target_lang)
            if translated:
                lines.append(f"  • {entry['term']} → {translated}")
        if len(lines) == 1:
            return ""
        return "\n".join(lines)

    def get_term_names_used(
        self, text: str, target_lang: str, domain: Optional[str] = None
    ) -> List[str]:
        """Return list of glossary term names found in text that have a translation."""
        self.load()
        terms = self.find_terms_in_text(text, domain)
        return [
            t["term"]
            for t in terms
            if t.get("translations", {}).get(target_lang)
        ]

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @property
    def entry_count(self) -> int:
        return len(self._entries)


# Singleton
glossary_service = GlossaryService()

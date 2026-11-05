"""
RAG Vector Store service — ChromaDB-backed document index with
multilingual sentence-transformer embeddings.
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

from app.core.config import get_settings
from app.core.logging_config import logger


class VectorStoreService:
    """
    Manages a ChromaDB persistent vector store for academic document retrieval.
    Uses a multilingual sentence-transformer model for embeddings.
    """

    COLLECTION_NAME = "academic_documents"

    def __init__(self) -> None:
        self._client = None
        self._collection = None
        self._embedding_fn = None
        self._ready = False

    def _get_client(self):
        if self._client is None:
            import chromadb
            settings = get_settings()
            self._client = chromadb.PersistentClient(
                path=str(settings.chroma_path)
            )
        return self._client

    def _get_embedding_function(self):
        if self._embedding_fn is None:
            from chromadb.utils import embedding_functions
            settings = get_settings()
            self._embedding_fn = (
                embedding_functions.SentenceTransformerEmbeddingFunction(
                    model_name=settings.embedding_model
                )
            )
        return self._embedding_fn

    def _get_collection(self):
        if self._collection is None:
            client = self._get_client()
            emb_fn = self._get_embedding_function()
            self._collection = client.get_or_create_collection(
                name=self.COLLECTION_NAME,
                embedding_function=emb_fn,
                metadata={"hnsw:space": "cosine"},
            )
            self._ready = True
            logger.info(
                "Vector store ready — collection '%s' has %d documents",
                self.COLLECTION_NAME,
                self._collection.count(),
            )
        return self._collection

    # ── Indexing ───────────────────────────────────────────────────────────────

    def index_document(
        self,
        document_id: str,
        chunks: List[str],
        metadata: Optional[Dict] = None,
    ) -> int:
        """
        Add document chunks to the vector store.
        Returns the number of chunks indexed.
        """
        collection = self._get_collection()
        base_meta = metadata or {}
        ids, texts, metas = [], [], []

        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}_chunk_{i}"
            ids.append(chunk_id)
            texts.append(chunk)
            metas.append({**base_meta, "document_id": document_id, "chunk_index": i})

        if not ids:
            return 0

        # Add in batches of 100 to avoid memory spikes
        batch_size = 100
        for start in range(0, len(ids), batch_size):
            collection.upsert(
                ids=ids[start : start + batch_size],
                documents=texts[start : start + batch_size],
                metadatas=metas[start : start + batch_size],
            )

        logger.info("Indexed %d chunks for document %s", len(ids), document_id)
        return len(ids)

    def search(
        self,
        query: str,
        n_results: int = 5,
        filter_document_id: Optional[str] = None,
        filter_domain: Optional[str] = None,
    ) -> List[Dict]:
        """
        Semantic search over indexed documents.
        Returns a list of dicts with 'text', 'metadata', and 'distance'.
        """
        collection = self._get_collection()
        where: Optional[Dict] = None
        if filter_document_id:
            where = {"document_id": filter_document_id}
        elif filter_domain:
            where = {"domain": filter_domain}

        kwargs: Dict = {
            "query_texts": [query],
            "n_results": min(n_results, max(1, collection.count())),
        }
        if where:
            kwargs["where"] = where

        try:
            results = collection.query(**kwargs)
        except Exception as exc:
            logger.warning("Vector search failed: %s", exc)
            return []

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]
        for doc, meta, dist in zip(docs, metas, dists):
            output.append({"text": doc, "metadata": meta, "distance": dist})
        return output

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks for a given document from the vector store."""
        collection = self._get_collection()
        collection.delete(where={"document_id": document_id})
        logger.info("Deleted chunks for document %s", document_id)

    @property
    def is_ready(self) -> bool:
        try:
            self._get_collection()
            return True
        except Exception:
            return False

    @property
    def document_count(self) -> int:
        try:
            return self._get_collection().count()
        except Exception:
            return 0


# Singleton
vector_store = VectorStoreService()

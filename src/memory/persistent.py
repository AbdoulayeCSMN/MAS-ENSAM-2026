"""Persistent memory: Qdrant vector store for vulnerability patterns and patches."""

from __future__ import annotations

import logging
import os
import uuid

logger = logging.getLogger(__name__)

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http.models import Distance, PointStruct, VectorParams
    from sentence_transformers import SentenceTransformer
    _QDRANT_AVAILABLE = True
except ImportError:
    _QDRANT_AVAILABLE = False
    logger.warning("qdrant_client or sentence_transformers not installed — persistent memory disabled")

COLLECTION_PATTERNS = "vuln_patterns"
COLLECTION_PATCHES = "patches"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2


class PersistentMemory:
    def __init__(self) -> None:
        if not _QDRANT_AVAILABLE:
            self._enabled = False
            return

        host = os.environ.get("QDRANT_HOST", "localhost")
        port = int(os.environ.get("QDRANT_PORT", "6333"))

        try:
            self._client = QdrantClient(host=host, port=port)
            self._encoder = SentenceTransformer("all-MiniLM-L6-v2")
            self._ensure_collections()
            self._enabled = True
        except Exception as exc:  # noqa: BLE001
            logger.warning("[memory] Qdrant unavailable: %s — running without persistent memory", exc)
            self._enabled = False

    def _ensure_collections(self) -> None:
        existing = {c.name for c in self._client.get_collections().collections}
        for name in (COLLECTION_PATTERNS, COLLECTION_PATCHES):
            if name not in existing:
                self._client.create_collection(
                    name,
                    vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
                )

    def retrieve_similar_patterns(self, code_snippets: list[str], top_k: int = 5) -> list[str]:
        if not self._enabled or not code_snippets:
            return []
        combined = " ".join(code_snippets[:3])[:2000]
        vector = self._encoder.encode(combined).tolist()
        hits = self._client.search(COLLECTION_PATTERNS, query_vector=vector, limit=top_k)
        return [h.payload.get("pattern", "") for h in hits]

    def retrieve_patches(self, cwe_id: str, top_k: int = 3) -> list[str]:
        if not self._enabled:
            return []
        vector = self._encoder.encode(cwe_id).tolist()
        hits = self._client.search(COLLECTION_PATCHES, query_vector=vector, limit=top_k)
        return [h.payload.get("diff", "") for h in hits]

    def store_patch(self, cwe_id: str, diff: str) -> None:
        if not self._enabled:
            return
        vector = self._encoder.encode(f"{cwe_id} {diff[:200]}").tolist()
        self._client.upsert(
            COLLECTION_PATCHES,
            points=[PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"cwe_id": cwe_id, "diff": diff})],
        )

    def store_pattern(self, description: str, code_snippet: str) -> None:
        if not self._enabled:
            return
        text = f"{description}\n{code_snippet[:500]}"
        vector = self._encoder.encode(text).tolist()
        self._client.upsert(
            COLLECTION_PATTERNS,
            points=[PointStruct(id=str(uuid.uuid4()), vector=vector, payload={"pattern": description, "snippet": code_snippet})],
        )

from __future__ import annotations

import os
from typing import List, Dict, Any

from app.core.config import get_settings

settings = get_settings()

# Lazy singletons — loaded only when first used
_embedder = None
_reranker = None
_qdrant = None


def _get_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer(settings.EMBEDDING_MODEL)
    return _embedder


def _get_reranker():
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
    return _reranker


def _get_qdrant():
    global _qdrant
    if _qdrant is None:
        from qdrant_client import QdrantClient
        from qdrant_client.http.models import Distance, VectorParams

        _qdrant = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)

        existing = [c.name for c in _qdrant.get_collections().collections]
        if settings.QDRANT_COLLECTION not in existing:
            _qdrant.create_collection(
                collection_name=settings.QDRANT_COLLECTION,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
    return _qdrant


# ── Text extraction ───────────────────────────────────────────────────────────
def extract_text(file_path: str) -> str:
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        return _extract_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return _extract_docx(file_path)
    else:
        with open(file_path, "r", errors="ignore") as f:
            return f.read()


def _extract_pdf(path: str) -> str:
    import PyPDF2
    pages = []
    with open(path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            pages.append(page.extract_text() or "")
    return "\n".join(pages)


def _extract_docx(path: str) -> str:
    import docx
    doc = docx.Document(path)
    return "\n".join(p.text for p in doc.paragraphs)


# ── Chunking ──────────────────────────────────────────────────────────────────
def chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


# ── Index document ────────────────────────────────────────────────────────────
def index_document(document_id: int, file_path: str, metadata: Dict[str, Any]) -> int:
    from qdrant_client.http.models import PointStruct

    text = extract_text(file_path)
    chunks = chunk_text(text)
    if not chunks:
        return 0

    embedder = _get_embedder()
    client = _get_qdrant()

    points = []
    for idx, chunk in enumerate(chunks):
        vector = embedder.encode(chunk).tolist()
        # PointStruct id must be an unsigned integer or UUID object, not a str
        point_id = abs(hash(f"{document_id}_{idx}")) % (2**63)
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "document_id": document_id,
                    "chunk_index": idx,
                    "chunk_text": chunk,
                    **metadata,
                },
            )
        )

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return len(points)


# ── Remove document embeddings ────────────────────────────────────────────────
def remove_document(document_id: int):
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    client = _get_qdrant()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
    )


# ── Semantic search + rerank ──────────────────────────────────────────────────
def semantic_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    embedder = _get_embedder()
    reranker = _get_reranker()
    client = _get_qdrant()

    query_vector = embedder.encode(query).tolist()

    # Step 1 — vector search top-20
    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        limit=20,
        with_payload=True,
    )

    if not results:
        return []

    # Step 2 — cross-encoder rerank
    pairs = [[query, r.payload["chunk_text"]] for r in results]
    scores = reranker.predict(pairs)

    ranked = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)[:top_k]

    return [
        {
            "document_id": hit.payload["document_id"],
            "title": hit.payload.get("title", ""),
            "company_name": hit.payload.get("company_name", ""),
            "chunk_text": hit.payload["chunk_text"],
            "score": float(score),
        }
        for hit, score in ranked
    ]


# ── Get all chunks for a document ─────────────────────────────────────────────
def get_document_context(document_id: int) -> List[Dict[str, Any]]:
    from qdrant_client.http.models import Filter, FieldCondition, MatchValue

    client = _get_qdrant()
    # scroll() returns a tuple: (list[Record], Optional[next_page_offset])
    scroll_result = client.scroll(
        collection_name=settings.QDRANT_COLLECTION,
        scroll_filter=Filter(
            must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]
        ),
        with_payload=True,
        limit=500,
    )
    records = scroll_result[0]  # first element is the list of records
    return [
        {
            "chunk_index": r.payload.get("chunk_index"),
            "chunk_text": r.payload.get("chunk_text"),
        }
        for r in sorted(records, key=lambda x: x.payload.get("chunk_index", 0))
    ]

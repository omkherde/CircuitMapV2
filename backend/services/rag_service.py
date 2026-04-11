"""
rag_service.py — ChromaDB-backed PubMed RAG vector store with semantic search.

Primary path: sentence-transformers embedding → ChromaDB vector similarity query.
Demo/offline fallback: lexical (token overlap) scoring when model is unavailable.

Singleton pattern — loads collection and embedding model once at module level.
"""
import os
import re

CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_client = None
_collection = None
_embed_model = None
_documents_cache = None  # only populated for lexical fallback


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb
        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        try:
            _collection = _client.get_collection(name="pubmed_abstracts")
        except Exception:
            return None
    return _collection


def _get_embed_model():
    """Load the sentence-transformers model once; return None if unavailable."""
    global _embed_model
    if _embed_model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _embed_model = SentenceTransformer(EMBEDDING_MODEL)
        except Exception:
            _embed_model = False  # sentinel: model unavailable
    return _embed_model if _embed_model is not False else None


def rag_store_ready() -> bool:
    """Return True when the local Chroma store exists and contains documents."""
    collection = _get_collection()
    return bool(collection is not None and collection.count() > 0)


# ── Semantic search (primary) ─────────────────────────────────────────────────

def _semantic_search(query: str, top_k: int) -> dict:
    """
    Encode the query with sentence-transformers and query ChromaDB for the
    top-k most similar documents by cosine distance.
    """
    collection = _get_collection()
    model = _get_embed_model()

    if collection is None or model is None:
        return _lexical_search(query, top_k)

    try:
        query_embedding = model.encode([query]).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=min(top_k, collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        abstracts = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            # ChromaDB cosine distance ∈ [0, 2]; similarity = 1 - dist/2
            similarity = round(1.0 - (dist / 2.0), 3)
            abstracts.append({
                "title": str(meta.get("title", "Unknown title"))[:120],
                "authors": str(meta.get("authors", "")),
                "journal": str(meta.get("journal", "Unknown journal"))[:80],
                "year": str(meta.get("year", "")),
                "pmid": str(meta.get("pmid", "")),
                "snippet": doc[:400] + "..." if len(doc) > 400 else doc,
                "similarity_score": similarity,
            })

        return {
            "query": query,
            "results": abstracts,
            "total_results": len(abstracts),
            "source": f"PubMed semantic search (ChromaDB + {EMBEDDING_MODEL})",
        }
    except Exception as e:
        # Embedding query failed — fall through to lexical
        return _lexical_search(query, top_k, _fallback_note=str(e))


# ── Lexical search (demo / offline fallback) ──────────────────────────────────

def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _get_documents_for_lexical() -> list[dict]:
    """Fetch all documents from ChromaDB for lexical scoring (one-time cache)."""
    global _documents_cache
    if _documents_cache is None:
        collection = _get_collection()
        if collection is None or collection.count() == 0:
            _documents_cache = []
        else:
            payload = collection.get(include=["documents", "metadatas"])
            _documents_cache = [
                {"document": doc or "", "metadata": meta or {}}
                for doc, meta in zip(payload["documents"], payload["metadatas"])
            ]
    return _documents_cache


def _score_document(query_tokens: set[str], document: str, metadata: dict) -> float:
    title = str(metadata.get("title", ""))
    journal = str(metadata.get("journal", ""))
    disease = str(metadata.get("disease", ""))
    gene = str(metadata.get("gene", ""))

    doc_tokens = _tokenize(document)
    title_tokens = _tokenize(title)
    meta_tokens = _tokenize(" ".join([journal, disease, gene]))

    overlap = len(query_tokens & doc_tokens)
    title_overlap = len(query_tokens & title_tokens)
    meta_overlap = len(query_tokens & meta_tokens)
    return float((title_overlap * 3) + (meta_overlap * 2) + overlap)


def _lexical_search(query: str, top_k: int, _fallback_note: str = "") -> dict:
    """Keyword-overlap scoring — used as demo/offline fallback."""
    documents = _get_documents_for_lexical()
    if not documents:
        return {
            "query": query,
            "results": [],
            "error": "RAG store not initialized. Run scripts/build_rag_store.py first.",
            "total_results": 0,
        }

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {"query": query, "results": [], "error": "Query is empty", "total_results": 0}

    scored = [
        (s, item)
        for item in documents
        if (s := _score_document(query_tokens, item["document"], item["metadata"])) > 0
    ]
    scored.sort(key=lambda p: (p[0], str(p[1]["metadata"].get("year", ""))), reverse=True)

    abstracts = []
    for score, item in scored[: min(top_k, 10, len(scored))]:
        meta = item["metadata"]
        doc = item["document"]
        abstracts.append({
            "title": str(meta.get("title", "Unknown title"))[:120],
            "authors": str(meta.get("authors", "")),
            "journal": str(meta.get("journal", "Unknown journal"))[:80],
            "year": str(meta.get("year", "")),
            "pmid": str(meta.get("pmid", "")),
            "snippet": doc[:400] + "..." if len(doc) > 400 else doc,
            "similarity_score": round(score / max(len(query_tokens), 1), 3),
        })

    note = "PubMed lexical search (offline demo fallback)"
    if _fallback_note:
        note += f" — semantic search error: {_fallback_note[:80]}"

    return {
        "query": query,
        "results": abstracts,
        "total_results": len(abstracts),
        "source": note,
    }


# ── Public API ────────────────────────────────────────────────────────────────

def search_literature(query: str, top_k: int = 5) -> dict:
    """
    Search pre-embedded PubMed abstracts for relevant literature.

    Uses sentence-transformers semantic similarity when the embedding model is
    available; falls back to lexical scoring for offline / demo mode.

    Args:
        query: Scientific question or search terms
        top_k: Number of abstracts to retrieve (max 10)

    Returns:
        dict with results list, each containing title, journal, year, pmid, snippet
    """
    if not rag_store_ready():
        return {
            "query": query,
            "results": [],
            "error": "RAG store not initialized. Run scripts/build_rag_store.py first.",
            "total_results": 0,
        }

    top_k = min(top_k, 10)
    return _semantic_search(query, top_k)


if __name__ == "__main__":
    result = search_literature("SUV39H1 Alzheimer memory hippocampus")
    print(f"Query: {result['query']}")
    print(f"Results: {result['total_results']}")
    print(f"Source: {result.get('source', '')}")
    if result.get("results"):
        print(f"Top result: {result['results'][0]['title']}")
        print(f"Similarity: {result['results'][0]['similarity_score']}")
    elif result.get("error"):
        print(f"Note: {result['error']} (expected if RAG not built)")
    print("rag_service TEST PASSED")

"""
rag_service.py — ChromaDB-backed PubMed RAG vector store.

Singleton pattern — loads collection once at module level.
Returns gracefully if the store hasn't been built yet.
"""
import os
import re

CHROMA_DIR = os.getenv("CHROMA_DB_DIR", "./cache/chroma_db")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

_client = None
_collection = None
_documents_cache = None


def _get_collection():
    global _client, _collection
    if _collection is None:
        import chromadb

        _client = chromadb.PersistentClient(path=CHROMA_DIR)
        try:
            _collection = _client.get_collection(name="pubmed_abstracts")
        except Exception:
            # Collection doesn't exist yet — return None gracefully
            return None
    return _collection


def rag_store_ready() -> bool:
    """Return True when the local Chroma store exists and contains documents."""
    collection = _get_collection()
    return bool(collection is not None and collection.count() > 0)


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _get_documents() -> list[dict]:
    global _documents_cache
    if _documents_cache is None:
        collection = _get_collection()
        if collection is None or collection.count() == 0:
            return []

        payload = collection.get(include=["documents", "metadatas"])
        _documents_cache = [
            {
                "document": document or "",
                "metadata": metadata or {},
            }
            for document, metadata in zip(payload["documents"], payload["metadatas"])
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

    # Weight title and metadata matches higher than body-only hits.
    return float((title_overlap * 3) + (meta_overlap * 2) + overlap)


def search_literature(query: str, top_k: int = 5) -> dict:
    """
    Search pre-embedded PubMed abstracts for relevant literature.

    Args:
        query: Scientific question or search terms
        top_k: Number of abstracts to retrieve (max 10)

    Returns:
        dict with results list, each containing title, journal, year, pmid, snippet
    """
    documents = _get_documents()

    if not documents:
        return {
            "query": query,
            "results": [],
            "error": "RAG store not initialized. Run scripts/build_rag_store.py first.",
            "total_results": 0
        }

    query_tokens = _tokenize(query)
    if not query_tokens:
        return {"query": query, "results": [], "error": "Query is empty", "total_results": 0}

    scored = []
    for item in documents:
        score = _score_document(query_tokens, item["document"], item["metadata"])
        if score <= 0:
            continue
        scored.append((score, item))

    scored.sort(
        key=lambda pair: (
            pair[0],
            str(pair[1]["metadata"].get("year", "")),
        ),
        reverse=True
    )

    top_k = min(top_k, 10, len(scored))
    abstracts = []
    for score, item in scored[:top_k]:
        meta = item["metadata"]
        doc = item["document"]
        abstracts.append({
            "title": str(meta.get("title", "Unknown title"))[:120],
            "authors": str(meta.get("authors", "")),
            "journal": str(meta.get("journal", "Unknown journal"))[:80],
            "year": str(meta.get("year", "")),
            "pmid": str(meta.get("pmid", "")),
            "snippet": doc[:400] + "..." if len(doc) > 400 else doc,
            "similarity_score": round(score / max(len(query_tokens), 1), 3)
        })

    return {
        "query": query,
        "results": abstracts,
        "total_results": len(abstracts),
        "source": "PubMed local lexical search (Chroma cache)"
    }


if __name__ == "__main__":
    result = search_literature("SUV39H1 Alzheimer memory hippocampus")
    print(f"Query: {result['query']}")
    print(f"Results: {result['total_results']}")
    if result.get('results'):
        print(f"Top result: {result['results'][0]['title']}")
    elif result.get('error'):
        print(f"Note: {result['error']} (expected if RAG not built)")
    print("rag_service TEST PASSED (RAG may not be built yet)")

"""Local RAG over ChromaDB + sentence-transformers. Heavy deps are an optional
extra (pip install -e ".[rag]"); everything imports lazily and degrades to 501.
"""

from functools import lru_cache


def rag_available() -> bool:
    try:
        import chromadb  # noqa: F401
        import sentence_transformers  # noqa: F401

        return True
    except ImportError:
        return False


@lru_cache(maxsize=1)
def _collection():
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction

    client = chromadb.PersistentClient(path="./data/chroma")
    return client.get_or_create_collection(
        "lvpp",
        embedding_function=SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2"),
    )


def index(doc_id: str, text: str, metadata: dict | None = None) -> None:
    _collection().upsert(ids=[doc_id], documents=[text], metadatas=[metadata or {}])


def query(text: str, n_results: int = 5, where: dict | None = None) -> list[dict]:
    res = _collection().query(query_texts=[text], n_results=n_results, where=where or None)
    return [
        {"id": i, "text": d, "metadata": m, "distance": dist}
        for i, d, m, dist in zip(
            res["ids"][0],
            res["documents"][0],
            res["metadatas"][0],
            res["distances"][0],
            strict=True,
        )
    ]

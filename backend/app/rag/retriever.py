# retriever.py: finds the policy chunks most related to a treatment
import math

from app.rag.store import get_collection, get_embedder

TOP_K = 4
# Cosine distance above this = not really related, so we drop it (0 = same meaning, 2 = opposite)
MAX_DISTANCE = 0.6


def cosine_distance(a: list[float], b: list[float]) -> float:
    # Computed here (not by the database) so local and cloud give the same scores
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return 1.0 if norm == 0 else 1 - dot / norm


def search_policy(query: str, k: int = TOP_K) -> list[dict]:
    collection = get_collection()
    count = collection.count()
    if count == 0:
        raise RuntimeError("Policy is not loaded. Run: python -m app.rag.ingest")

    # 1. Turn the question into a vector (same model as the chunks)
    vector = get_embedder().embed_query(query, task_type="RETRIEVAL_QUERY")

    # 2. Ask ChromaDB for the k closest chunks
    result = collection.query(
        query_embeddings=[vector],
        n_results=min(k, count),
        include=["documents", "metadatas", "embeddings"],
    )

    # 3. Keep only chunks that are close enough (by cosine distance)
    chunks = []
    for text, meta, emb in zip(result["documents"][0], result["metadatas"][0], result["embeddings"][0]):
        distance = cosine_distance(vector, list(emb))
        if distance <= MAX_DISTANCE:
            chunks.append({"text": text, "page": (meta or {}).get("page"), "distance": round(distance, 3)})
    return sorted(chunks, key=lambda c: c["distance"])

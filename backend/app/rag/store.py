# store.py: one shared place for the ChromaDB collection and the embedding model
# CHROMA_MODE=local -> a folder on this machine (like SQLite, no account)
# CHROMA_MODE=cloud -> Chroma Cloud (online, shared by all servers, needs an API key)
from functools import lru_cache
from pathlib import Path

import chromadb
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from app.config import settings

# Local mode saves its files here (ignored by Git)
CHROMA_DIR = Path(__file__).resolve().parents[2] / "chroma_db"
COLLECTION_NAME = "health_policy"
EMBEDDING_MODEL = "gemini-embedding-001"


@lru_cache
def get_embedder() -> GoogleGenerativeAIEmbeddings:
    # Turns text into a list of numbers (a vector) that captures its meaning
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is needed for policy embeddings")
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        google_api_key=settings.google_api_key,
    )


def is_cloud() -> bool:
    return settings.chroma_mode.lower() == "cloud"


@lru_cache
def _client() -> chromadb.ClientAPI:
    if is_cloud():
        if not settings.chroma_api_key:
            raise RuntimeError("CHROMA_MODE=cloud needs CHROMA_API_KEY (and CHROMA_TENANT, CHROMA_DATABASE)")
        return chromadb.CloudClient(
            api_key=settings.chroma_api_key,
            tenant=settings.chroma_tenant or None,
            database=settings.chroma_database or None,
        )
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection():
    if is_cloud():
        # Chroma Cloud picks its own index; we compute cosine ourselves in retriever.py
        return _client().get_or_create_collection(name=COLLECTION_NAME)
    return _client().get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def reset_collection() -> None:
    # Delete old chunks before re-ingesting (so we never keep stale rules)
    try:
        _client().delete_collection(COLLECTION_NAME)
    except Exception:
        pass

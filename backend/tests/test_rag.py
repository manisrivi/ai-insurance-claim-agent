# RAG store/retriever tests: local Chroma in a temp folder, fake embeddings (no Gemini)
import chromadb
import pytest

from app.rag import retriever, store


class FakeEmbedder:
    # 3-number "meaning": [cosmetic, dengue, heart]
    WORDS = {"cosmetic": 0, "rhinoplasty": 0, "dengue": 1, "fever": 1, "heart": 2, "angioplasty": 2}

    def _vec(self, text):
        v = [0.01, 0.01, 0.01]
        for word, i in self.WORDS.items():
            if word in text.lower():
                v[i] += 1
        return v

    def embed_documents(self, texts, task_type=None):
        return [self._vec(t) for t in texts]

    def embed_query(self, text, task_type=None):
        return self._vec(text)


@pytest.fixture
def local_store(tmp_path, monkeypatch):
    client = chromadb.PersistentClient(path=str(tmp_path / "db"))
    monkeypatch.setattr(store, "_client", lambda: client)
    monkeypatch.setattr(retriever, "get_embedder", lambda: FakeEmbedder())
    col = store.get_collection()
    texts = ["Section 3.1 Cosmetic surgery NOT covered", "Section 2.1 Dengue fever covered", "Section 2.2 Heart angioplasty covered"]
    col.add(ids=["a", "b", "c"], documents=texts, embeddings=FakeEmbedder().embed_documents(texts),
            metadatas=[{"page": 1}] * 3)
    return col


def test_cosine_distance():
    assert retriever.cosine_distance([1, 0], [1, 0]) == pytest.approx(0)
    assert retriever.cosine_distance([1, 0], [0, 1]) == pytest.approx(1)


def test_search_finds_the_right_section(local_store):
    chunks = retriever.search_policy("Is rhinoplasty covered?")
    assert chunks[0]["text"].startswith("Section 3.1")
    assert all(c["distance"] <= retriever.MAX_DISTANCE for c in chunks)


def test_cloud_mode_uses_cloud_client(monkeypatch):
    seen = {}
    monkeypatch.setattr(store.settings, "chroma_mode", "cloud")
    monkeypatch.setattr(store.settings, "chroma_api_key", "ck-test")
    monkeypatch.setattr(store.settings, "chroma_tenant", "t1")
    monkeypatch.setattr(store.settings, "chroma_database", "claims-db")
    monkeypatch.setattr(store.chromadb, "CloudClient", lambda **kw: seen.update(kw) or "cloud-client")
    store._client.cache_clear()
    try:
        assert store._client() == "cloud-client"
        assert seen == {"api_key": "ck-test", "tenant": "t1", "database": "claims-db"}
    finally:
        store._client.cache_clear()


def test_cloud_mode_without_key_fails_clearly(monkeypatch):
    monkeypatch.setattr(store.settings, "chroma_mode", "cloud")
    monkeypatch.setattr(store.settings, "chroma_api_key", "")
    store._client.cache_clear()
    try:
        with pytest.raises(RuntimeError, match="CHROMA_API_KEY"):
            store._client()
    finally:
        store._client.cache_clear()

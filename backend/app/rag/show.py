# show.py: look inside ChromaDB, like the Supabase table editor (read only)
# Run:  python -m app.rag.show
#       python -m app.rag.show "Is cosmetic surgery covered?"   <- also test a search
import sys

from app.rag.store import CHROMA_DIR, COLLECTION_NAME, get_collection, is_cloud


def show_all() -> None:
    collection = get_collection()
    rows = collection.get(include=["documents", "metadatas", "embeddings"])
    total = len(rows["ids"])

    print(f"\nChromaDB        : {'Chroma Cloud (online)' if is_cloud() else CHROMA_DIR}")
    print(f"Collection      : {COLLECTION_NAME}")
    print(f"Rows (chunks)   : {total}\n")

    if total == 0:
        print("Empty. Run: python -m app.rag.ingest")
        return

    # One "row" per chunk: id | page | text | embedding (list of numbers)
    for chunk_id, text, meta, vector in zip(rows["ids"], rows["documents"], rows["metadatas"], rows["embeddings"]):
        preview = " ".join(text.split())[:110]
        numbers = ", ".join(f"{v:.3f}" for v in vector[:3])
        print(f"[{chunk_id}]  page {meta.get('page')}  |  {len(vector)} numbers: [{numbers}, ...]")
        print(f"   {preview}...\n")


def show_search(question: str) -> None:
    # Same search the policy agent does for every claim
    from app.rag.retriever import search_policy

    print(f'\nSearch: "{question}"\n')
    for rank, chunk in enumerate(search_policy(question), start=1):
        preview = " ".join(chunk["text"].split())[:110]
        print(f"#{rank}  distance {chunk['distance']}  (0 = same meaning)  page {chunk['page']}")
        print(f"   {preview}...\n")


if __name__ == "__main__":
    show_all()
    if len(sys.argv) > 1:
        show_search(" ".join(sys.argv[1:]))

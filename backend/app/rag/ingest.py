# ingest.py: reads the policy PDF, cuts it into chunks, and stores them in ChromaDB.
# Run once (and again whenever the policy changes):  python -m app.rag.ingest
# Startup scripts use:  python -m app.rag.ingest --if-empty   (only loads when nothing is stored yet)
import sys
from pathlib import Path

from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader

from app.rag.store import get_collection, get_embedder, reset_collection

POLICY_PDF = Path(__file__).resolve().parents[2] / "data" / "policy.pdf"

# ~400 characters per chunk, 80 overlap so a rule is not cut in half
CHUNK_SIZE = 400
CHUNK_OVERLAP = 80


def load_pages(pdf_path: Path) -> list[dict]:
    # 1. Read the text of every page
    reader = PdfReader(pdf_path)
    return [
        {"text": page.extract_text() or "", "page": number}
        for number, page in enumerate(reader.pages, start=1)
    ]


def make_chunks(pages: list[dict]) -> list[dict]:
    # 2. Cut pages into chunks. Prefer cutting at "Section", then paragraphs, then lines
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\nSection ", "\n\n", "\n", ". ", " "],
        keep_separator="start",
    )
    chunks = []
    for page in pages:
        for piece in splitter.split_text(page["text"]):
            piece = piece.strip()
            if piece:
                chunks.append({"text": piece, "page": page["page"]})
    return chunks


def ingest() -> int:
    pages = load_pages(POLICY_PDF)
    chunks = make_chunks(pages)
    if not chunks:
        raise RuntimeError(f"No text found in {POLICY_PDF}")

    # 3. Turn every chunk into numbers (embeddings)
    texts = [c["text"] for c in chunks]
    vectors = get_embedder().embed_documents(texts, task_type="RETRIEVAL_DOCUMENT")

    # 4. Start fresh, then save chunks + vectors + page numbers
    reset_collection()
    get_collection().add(
        ids=[f"policy-{i}" for i in range(len(chunks))],
        documents=texts,
        embeddings=vectors,
        metadatas=[{"page": c["page"], "source": POLICY_PDF.name} for c in chunks],
    )
    return len(chunks)


if __name__ == "__main__":
    from app.rag.store import is_cloud

    where = "Chroma Cloud" if is_cloud() else "local ChromaDB folder"
    if "--if-empty" in sys.argv and get_collection().count() > 0:
        print(f"Policy already loaded in {where}. Skipping.")
    else:
        count = ingest()
        print(f"Stored {count} policy chunks in {where}")

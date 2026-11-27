# pdf_reader.py: checks the uploaded bill PDF and reads its text
from io import BytesIO

from pypdf import PdfReader
from pypdf.errors import PdfReadError

# Upload limits
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PAGES = 10
# Less text than this = probably a scanned (photo) PDF
MIN_TEXT_LENGTH = 30


class PDFValidationError(Exception):
    # Our own error for bad uploads (the API turns it into a 400 error)
    pass


def read_pdf(file_bytes: bytes, filename: str, content_type: str | None) -> dict:
    # 1. Only PDF files
    if not filename.lower().endswith(".pdf") or content_type != "application/pdf":
        raise PDFValidationError("Only PDF files are allowed")

    # 2. Size limits
    if len(file_bytes) == 0:
        raise PDFValidationError("The PDF file is empty")
    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise PDFValidationError(f"PDF must be smaller than {MAX_FILE_SIZE_MB} MB")

    # 3. Real PDFs always start with "%PDF"
    if not file_bytes.startswith(b"%PDF"):
        raise PDFValidationError("This file is not a real PDF")

    # 4. Open it safely
    try:
        reader = PdfReader(BytesIO(file_bytes))
        if reader.is_encrypted:
            raise PDFValidationError("Password-protected PDFs are not allowed")
        page_count = len(reader.pages)
    except PDFValidationError:
        raise
    except (PdfReadError, Exception):
        # Any parser error on a strange PDF = a clear 400, never a 500
        raise PDFValidationError("The PDF is damaged and cannot be read")

    # 5. Page limit
    if page_count > MAX_PAGES:
        raise PDFValidationError(f"PDF can have at most {MAX_PAGES} pages")

    # 6. Read all text; very little text means it's probably scanned
    try:
        text = "\n".join(page.extract_text() or "" for page in reader.pages).strip()
    except Exception:
        raise PDFValidationError("The PDF text could not be read")

    return {
        "text": text,
        "page_count": page_count,
        "is_scanned": len(text) < MIN_TEXT_LENGTH,
    }
import pytest

from app.pdf_reader import PDFValidationError, read_pdf


def test_reads_valid_bill(bill_bytes):
    result = read_pdf(bill_bytes, "bill.pdf", "application/pdf")
    assert "Ravi Kumar" in result["text"]
    assert result["page_count"] == 1
    assert result["is_scanned"] is False


def test_rejects_non_pdf_name(bill_bytes):
    with pytest.raises(PDFValidationError, match="Only PDF"):
        read_pdf(bill_bytes, "bill.png", "image/png")


def test_rejects_fake_pdf():
    with pytest.raises(PDFValidationError, match="not a real PDF"):
        read_pdf(b"hello world", "bill.pdf", "application/pdf")


def test_rejects_empty_file():
    with pytest.raises(PDFValidationError, match="empty"):
        read_pdf(b"", "bill.pdf", "application/pdf")

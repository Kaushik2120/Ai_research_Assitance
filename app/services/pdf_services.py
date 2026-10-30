
from io import BytesIO
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> list[dict]:
    """Extract text from a PDF, preserving page numbers."""

    pages = []

    reader = PdfReader(BytesIO(file_bytes), strict=False)

    for page_number, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""

        pages.append({
            "page_number": page_number,
            "text": text.strip(),
        })

    return pages

"""PDF text extraction for CV ingestion.

Turns raw PDF bytes into the plain text rendered inside the document. Kept
deliberately small and dependency-light (pypdf) so the strip node can operate
on clean text. Extraction is tolerant: unreadable input yields an empty string
rather than raising, so the pipeline can record an error and continue.
"""

from __future__ import annotations

import io
import logging

from pypdf import PdfReader

logger = logging.getLogger(__name__)

# PDF files start with this magic marker.
PDF_MAGIC = b"%PDF-"


def looks_like_pdf(data: bytes, filename: str | None = None) -> bool:
    """Heuristically decide whether ``data`` is a PDF.

    Checks the ``%PDF-`` magic header first, then falls back to the filename
    extension when the header is absent (some exports prepend whitespace).
    """
    if data[:1024].lstrip().startswith(PDF_MAGIC):
        return True
    if filename is not None and filename.lower().endswith(".pdf"):
        return True
    return False


def extract_text_from_pdf(data: bytes) -> str:
    """Extract text from PDF bytes, joining pages with blank lines.

    Returns an empty string when the bytes cannot be parsed.
    """
    if not data:
        return ""

    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("Failed to open PDF for extraction: %s", exc)
        return ""

    pages: list[str] = []
    for page in reader.pages:
        try:
            pages.append(page.extract_text() or "")
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to extract a PDF page: %s", exc)
            pages.append("")

    return "\n\n".join(pages).strip()


def extract_cv_text(data: bytes, filename: str | None = None) -> str:
    """Extract plain text from an uploaded CV.

    Uses PDF extraction when the payload looks like a PDF; otherwise decodes the
    bytes as UTF-8 text (for .txt uploads), replacing undecodable bytes.
    """
    if looks_like_pdf(data, filename):
        return extract_text_from_pdf(data)
    return data.decode("utf-8", errors="replace")

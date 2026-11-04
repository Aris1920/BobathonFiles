"""Resume text extraction endpoint.

POST /resume/extract — accepts a PDF or DOCX upload and returns the extracted
plain text.  The file is never persisted; text is extracted and discarded after
the response is sent.
"""
from __future__ import annotations

import io
import re

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/resume", tags=["resume"])

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _clean_text(raw: str) -> str:
    """Collapse runs of whitespace/newlines and strip leading/trailing space."""
    # Collapse multiple spaces/tabs into one
    text = re.sub(r"[^\S\n]+", " ", raw)
    # Collapse 3+ consecutive newlines into two
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _extract_pdf(contents: bytes) -> str:
    import pdfplumber  # lazy import — not needed for DOCX path

    pages: list[str] = []
    with pdfplumber.open(io.BytesIO(contents)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                pages.append(page_text)
    return "\n".join(pages)


def _extract_docx(contents: bytes) -> str:
    import docx  # python-docx exposes the `docx` namespace

    doc = docx.Document(io.BytesIO(contents))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


@router.post("/extract")
async def extract_resume_text(
    file: UploadFile,
    _current_user: User = Depends(get_current_user),
) -> dict[str, object]:
    """Extract plain text from an uploaded PDF or DOCX file.

    - Max file size: 5 MB
    - Supported formats: .pdf, .docx
    - The file is NOT stored anywhere — processed in memory and discarded.
    """
    filename = (file.filename or "").lower()
    if not (filename.endswith(".pdf") or filename.endswith(".docx")):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Only PDF and DOCX files are supported.",
        )

    contents = await file.read()
    if len(contents) > _MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File size exceeds the 5 MB limit.",
        )

    if filename.endswith(".pdf"):
        raw_text = _extract_pdf(contents)
    else:
        raw_text = _extract_docx(contents)

    cleaned = _clean_text(raw_text)
    return {"text": cleaned, "char_count": len(cleaned)}

"""Tests for POST /resume/extract."""
from __future__ import annotations

import io
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

EXTRACT_URL = "/resume/extract"

_USER_EMAIL = "resume_tester@example.com"
_USER_PASSWORD = "strongpass99"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _register_and_token(client: TestClient) -> str:
    """Register a user and return a valid access token."""
    resp = client.post(
        "/auth/register",
        json={"email": _USER_EMAIL, "password": _USER_PASSWORD},
    )
    assert resp.status_code == 201
    return resp.json()["access_token"]


def _auth_headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _make_docx_bytes(text: str) -> bytes:
    """Create a minimal in-memory DOCX file with a single paragraph."""
    import docx

    doc = docx.Document()
    doc.add_paragraph(text)
    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf.read()


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_extract_pdf_text(client: TestClient):
    """PDF text extraction delegates to pdfplumber; mock it out."""
    token = _register_and_token(client)

    # Build a mock pdfplumber page
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Software Engineer Python Django"

    mock_pdf = MagicMock()
    mock_pdf.__enter__ = MagicMock(return_value=mock_pdf)
    mock_pdf.__exit__ = MagicMock(return_value=False)
    mock_pdf.pages = [mock_page]

    with patch("pdfplumber.open", return_value=mock_pdf):
        resp = client.post(
            EXTRACT_URL,
            files={"file": ("resume.pdf", b"%PDF-1.4 fake", "application/pdf")},
            headers=_auth_headers(token),
        )

    assert resp.status_code == 200
    body = resp.json()
    assert "Software Engineer Python Django" in body["text"]
    assert body["char_count"] == len(body["text"])


def test_extract_docx_text(client: TestClient):
    """DOCX text extraction uses python-docx; create a real in-memory DOCX."""
    token = _register_and_token(client)

    docx_bytes = _make_docx_bytes("Data Analyst SQL Python")

    resp = client.post(
        EXTRACT_URL,
        files={
            "file": (
                "resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
        headers=_auth_headers(token),
    )

    assert resp.status_code == 200
    body = resp.json()
    assert "Data Analyst SQL Python" in body["text"]
    assert body["char_count"] == len(body["text"])


def test_extract_unsupported_format(client: TestClient):
    """.txt files must be rejected with 422."""
    token = _register_and_token(client)

    resp = client.post(
        EXTRACT_URL,
        files={"file": ("resume.txt", b"plain text resume", "text/plain")},
        headers=_auth_headers(token),
    )

    assert resp.status_code == 422
    assert "Only PDF and DOCX" in resp.json()["detail"]


def test_extract_file_too_large(client: TestClient):
    """Files larger than 5 MB must be rejected with 422."""
    token = _register_and_token(client)

    # Create 5 MB + 1 byte of fake PDF data
    oversized = b"%PDF-1.4 " + b"x" * (5 * 1024 * 1024 + 1)

    resp = client.post(
        EXTRACT_URL,
        files={"file": ("big.pdf", oversized, "application/pdf")},
        headers=_auth_headers(token),
    )

    assert resp.status_code == 422
    assert "5 MB" in resp.json()["detail"]


def test_extract_requires_auth(client: TestClient):
    """Requests without a Bearer token must be rejected with 401."""
    docx_bytes = _make_docx_bytes("Hello World")

    resp = client.post(
        EXTRACT_URL,
        files={"file": ("resume.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
    )

    assert resp.status_code == 401

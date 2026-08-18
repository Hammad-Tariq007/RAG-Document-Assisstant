"""Text extraction for uploaded files (see ALLOWED_EXTENSIONS in config)."""

import io

from config import ALLOWED_EXTENSIONS
from docx import Document
from fastapi import HTTPException
from pypdf import PdfReader


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Pull plain text out of an uploaded file of a supported type.

    .pdf and .docx are parsed with their respective libraries; every other
    supported extension is read as plain UTF-8 text.
    """
    suffix = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if suffix not in ALLOWED_EXTENSIONS:
        supported = ", ".join(sorted(ALLOWED_EXTENSIONS))
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{suffix}'. Only {supported} are supported.",
        )

    if suffix == ".pdf":
        reader = PdfReader(io.BytesIO(file_bytes))
        text = "\n\n".join(page.extract_text() or "" for page in reader.pages)
    elif suffix == ".docx":
        document = Document(io.BytesIO(file_bytes))
        text = "\n\n".join(p.text for p in document.paragraphs)
    else:
        text = file_bytes.decode("utf-8", errors="replace")

    if not text.strip():
        raise HTTPException(
            status_code=400,
            detail="No extractable text was found in this file.",
        )

    return text

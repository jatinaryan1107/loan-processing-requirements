"""Bounded text extraction; supplied documents are data, never executable input."""

import io
import zipfile
from pathlib import Path
from fastapi import HTTPException


def parse_document(data: bytes, filename: str | None):
    name = Path((filename or "document").replace("\\", "/")).name[:180]
    ext = Path(name).suffix.lower()
    try:
        if ext == ".txt":
            text = data.decode("utf-8-sig")
        elif ext == ".docx":
            from docx import Document

            with zipfile.ZipFile(io.BytesIO(data)) as zipped:
                if (
                    sum(i.file_size for i in zipped.infolist()) > 20 * 1024 * 1024
                    or len(zipped.infolist()) > 1000
                ):
                    raise ValueError("Expanded document exceeds safe limits")
            doc = Document(io.BytesIO(data))
            text = "\n".join(
                [p.text for p in doc.paragraphs]
                + [" | ".join(c.text for c in row.cells) for table in doc.tables for row in table.rows]
            )
        elif ext == ".pdf":
            from pypdf import PdfReader

            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted or len(reader.pages) > 100:
                raise ValueError("Encrypted documents or more than 100 pages are unsupported")
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
        else:
            raise HTTPException(415, "Upload a UTF-8 TXT, text-based PDF or DOCX file.")
        if not 12 <= len(text.strip()) <= 100000 or "\x00" in text:
            raise ValueError("No usable text found or extracted text exceeds 100,000 characters")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            422,
            "Document could not be parsed safely. Use a text-based, unencrypted file, or paste its text. OCR is not supported.",
        ) from exc
    return text.strip(), name

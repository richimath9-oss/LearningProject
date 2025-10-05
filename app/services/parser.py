from __future__ import annotations

import importlib
import io
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from fastapi import UploadFile


def _load_optional(module_name: str):
    spec = importlib.util.find_spec(module_name)
    if spec is None:  # pragma: no cover - optional dependency path
        return None
    return importlib.import_module(module_name)


docx = _load_optional("docx")
pptx = _load_optional("pptx")
pdfplumber = _load_optional("pdfplumber")
extract_msg = _load_optional("extract_msg")


def _read_docx(content: bytes) -> str:
    if not docx:
        return "DOCX parser unavailable in current environment."
    document = docx.Document(io.BytesIO(content))
    return "\n".join(paragraph.text for paragraph in document.paragraphs)


def _read_pdf(content: bytes) -> str:
    if not pdfplumber:
        return "PDF parser unavailable in current environment."
    output = []
    with pdfplumber.open(io.BytesIO(content)) as pdf:
        for page in pdf.pages:
            output.append(page.extract_text() or "")
    return "\n".join(output)


def _read_pptx(content: bytes) -> str:
    if not pptx:
        return "PPTX parser unavailable in current environment."
    presentation = pptx.Presentation(io.BytesIO(content))
    slides = []
    for slide in presentation.slides:
        elements = []
        for shape in slide.shapes:
            if hasattr(shape, "text"):
                elements.append(shape.text)
        slides.append("\n".join(elements))
    return "\n\n".join(slides)


def _read_csv_or_xlsx(content: bytes, suffix: str) -> str:
    if suffix == ".csv":
        text = content.decode("utf-8", errors="ignore")
        sample = "\n".join(text.splitlines()[:50])
        return sample
    with io.BytesIO(content) as buffer:
        df = pd.read_excel(buffer)
    return df.to_csv(index=False)


def _read_email(content: bytes) -> str:
    if not extract_msg:
        return "Email parser unavailable in current environment."
    with io.BytesIO(content) as buffer:
        message = extract_msg.Message(buffer)
        message_message = [f"Subject: {message.subject}", f"From: {message.sender}"]
        message_message.append(message.body or "")
    return "\n".join(message_message)


def parse_upload(file: UploadFile) -> Tuple[str, Dict[str, str]]:
    suffix = Path(file.filename).suffix.lower()
    content = file.file.read()
    metadata: Dict[str, str] = {"filename": file.filename}
    if suffix in {".docx"}:
        text = _read_docx(content)
    elif suffix in {".pdf"}:
        text = _read_pdf(content)
    elif suffix in {".ppt", ".pptx"}:
        text = _read_pptx(content)
    elif suffix in {".xlsx", ".xls", ".csv"}:
        text = _read_csv_or_xlsx(content, suffix)
    elif suffix in {".eml", ".msg"}:
        text = _read_email(content)
    else:
        text = content.decode("utf-8", errors="ignore")
    metadata.update({
        "size": str(len(content)),
        "suffix": suffix,
    })
    return text, metadata

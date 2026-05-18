from pathlib import Path

import fitz

from app.models.schemas import PageText


def extract_text(path: Path, file_type: str) -> list[PageText]:
    if file_type == ".pdf":
        return _extract_pdf_text(path)
    if file_type == ".txt":
        return _extract_txt_text(path)
    msg = f"Unsupported file type: {file_type}"
    raise ValueError(msg)


def _extract_pdf_text(path: Path) -> list[PageText]:
    pages: list[PageText] = []
    with fitz.open(path) as document:
        for index, page in enumerate(document, start=1):
            pages.append(PageText(page_number=index, text=page.get_text().strip()))
    return pages


def _extract_txt_text(path: Path) -> list[PageText]:
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="latin-1")
    return [PageText(page_number=None, text=text.strip())]

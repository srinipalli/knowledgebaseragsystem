from __future__ import annotations

from pathlib import Path

import fitz

from app.parsers.base import BaseParser, TextUnit


class PDFParser(BaseParser):
    name = "pymupdf"

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() == ".pdf"

    def estimate_total_units(self, path: Path) -> int:
        with fitz.open(path) as document:
            return document.page_count

    def iter_units(self, path: Path):
        with fitz.open(path) as document:
            for index, page in enumerate(document, start=1):
                text = page.get_text("text")
                if not text.strip():
                    continue
                yield TextUnit(
                    unit_index=index,
                    text=text,
                    metadata={"page_number": index, "source_type": "pdf"},
                )

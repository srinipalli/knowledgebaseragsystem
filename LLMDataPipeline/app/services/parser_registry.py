from __future__ import annotations

from pathlib import Path

from app.parsers.base import BaseParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.text_parser import TextParser


class ParserRegistry:
    def __init__(self) -> None:
        self.parsers: list[BaseParser] = [PDFParser(), DOCXParser(), TextParser()]

    def resolve(self, path: Path) -> BaseParser:
        for parser in self.parsers:
            if parser.supports(path):
                return parser
        raise ValueError(f"Unsupported file extension: {path.suffix.lower()}")

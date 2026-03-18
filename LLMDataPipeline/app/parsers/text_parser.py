from __future__ import annotations

from pathlib import Path

from app.parsers.base import BaseParser, TextUnit


class TextParser(BaseParser):
    name = "text"
    supported = {".txt", ".md"}

    def supports(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported

    def estimate_total_units(self, path: Path) -> int:
        with path.open("r", encoding="utf-8", errors="ignore") as file_handle:
            return sum(1 for _ in file_handle)

    def iter_units(self, path: Path):
        with path.open("r", encoding="utf-8", errors="ignore") as file_handle:
            for index, line in enumerate(file_handle, start=1):
                text = line.strip()
                if not text:
                    continue
                yield TextUnit(
                    unit_index=index,
                    text=text,
                    metadata={"line_number": index, "source_type": "text"},
                )

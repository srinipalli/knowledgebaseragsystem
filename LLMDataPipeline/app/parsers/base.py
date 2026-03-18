from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Generator


@dataclass
class TextUnit:
    unit_index: int
    text: str
    metadata: dict


class BaseParser:
    name = "base"

    def supports(self, path: Path) -> bool:
        raise NotImplementedError

    def iter_units(self, path: Path) -> Generator[TextUnit, None, None]:
        raise NotImplementedError

    def estimate_total_units(self, path: Path) -> int:
        return 0

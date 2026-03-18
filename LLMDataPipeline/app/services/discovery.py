from __future__ import annotations

from pathlib import Path

from app.core.config import Settings


def discover_files(settings: Settings) -> list[Path]:
    files: list[Path] = []
    for path in settings.input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower() in settings.supported_extensions:
            files.append(path)
    return sorted(files)

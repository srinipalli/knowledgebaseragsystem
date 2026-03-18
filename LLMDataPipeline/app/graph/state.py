from __future__ import annotations

from pathlib import Path
from typing import Any, TypedDict


class PipelineState(TypedDict, total=False):
    file_path: Path
    checksum: str
    parser_name: str
    total_units: int
    processed_units: int
    chunk_index: int
    persisted_chunks: int
    error_message: str | None
    source_file_id: str
    run_id: str
    result: dict[str, Any]

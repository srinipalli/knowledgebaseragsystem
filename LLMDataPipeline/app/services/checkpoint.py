from __future__ import annotations

import json
from pathlib import Path


class CheckpointStore:
    def __init__(self, checkpoint_dir: Path) -> None:
        self.checkpoint_dir = checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

    def path_for(self, file_path: Path) -> Path:
        return self.checkpoint_dir / f"{file_path.name}.checkpoint.json"

    def load(self, file_path: Path) -> dict:
        checkpoint_path = self.path_for(file_path)
        if not checkpoint_path.exists():
            return {}
        return json.loads(checkpoint_path.read_text(encoding="utf-8"))

    def save(self, file_path: Path, payload: dict) -> None:
        checkpoint_path = self.path_for(file_path)
        checkpoint_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def clear(self, file_path: Path) -> None:
        checkpoint_path = self.path_for(file_path)
        if checkpoint_path.exists():
            checkpoint_path.unlink()

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DocumentChunk, FileStatus, IngestionRun, RunStatus, SourceFile


class IngestionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def get_source_by_path(self, path: Path) -> SourceFile | None:
        statement = select(SourceFile).where(SourceFile.path == str(path))
        return self.session.scalar(statement)

    def upsert_source_file(self, *, path: Path, checksum: str, size_bytes: int, extension: str) -> SourceFile:
        source = self.get_source_by_path(path)
        if source is None:
            source = SourceFile(
                path=str(path),
                file_name=path.name,
                extension=extension,
                checksum=checksum,
                size_bytes=size_bytes,
                status=FileStatus.pending,
            )
            self.session.add(source)
        else:
            source.checksum = checksum
            source.size_bytes = size_bytes
            source.extension = extension
            source.error_message = None
        self.session.commit()
        self.session.refresh(source)
        return source

    def start_run(self, source_file: SourceFile) -> IngestionRun:
        source_file.status = FileStatus.processing
        run = IngestionRun(source_file_id=source_file.id, status=RunStatus.running, stage="discovered")
        self.session.add(run)
        self.session.commit()
        self.session.refresh(run)
        return run

    def update_stage(self, run: IngestionRun, stage: str, last_unit: int | None = None) -> None:
        run.stage = stage
        if last_unit is not None:
            run.last_unit = last_unit
        self.session.commit()

    def update_source_progress(self, source_file: SourceFile, *, parser_name: str, processed_units: int, total_units: int) -> None:
        source_file.parser_name = parser_name
        source_file.processed_units = processed_units
        source_file.total_units = total_units
        source_file.updated_at = datetime.utcnow()
        self.session.commit()

    def persist_chunk_batch(self, source_file: SourceFile, run: IngestionRun, rows: list[dict]) -> None:
        for row in rows:
            chunk = DocumentChunk(
                source_file_id=source_file.id,
                chunk_index=row["chunk_index"],
                unit_index=row["unit_index"],
                content=row["content"],
                metadata_json=row["metadata"],
                embedding=row["embedding"],
            )
            self.session.add(chunk)
        run.chunks_persisted += len(rows)
        self.session.commit()

    def complete_run(self, source_file: SourceFile, run: IngestionRun) -> None:
        source_file.status = FileStatus.completed
        run.status = RunStatus.completed
        run.stage = "completed"
        run.completed_at = datetime.utcnow()
        self.session.commit()

    def fail_run(self, source_file: SourceFile, run: IngestionRun, error_message: str, quarantine: bool = False) -> None:
        source_file.status = FileStatus.quarantined if quarantine else FileStatus.failed
        source_file.error_message = error_message
        run.status = RunStatus.failed
        run.stage = "failed"
        run.error_message = error_message
        run.completed_at = datetime.utcnow()
        self.session.commit()

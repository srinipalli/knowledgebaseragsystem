import enum
import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class FileStatus(str, enum.Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"
    quarantined = "quarantined"


class RunStatus(str, enum.Enum):
    running = "running"
    completed = "completed"
    failed = "failed"


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    path: Mapped[str] = mapped_column(String(1024), unique=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    extension: Mapped[str] = mapped_column(String(16), nullable=False)
    checksum: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    size_bytes: Mapped[int] = mapped_column(nullable=False)
    status: Mapped[FileStatus] = mapped_column(Enum(FileStatus), default=FileStatus.pending, nullable=False)
    parser_name: Mapped[str | None] = mapped_column(String(128))
    total_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_units: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    runs: Mapped[list["IngestionRun"]] = relationship(back_populates="source_file", cascade="all, delete-orphan")
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="source_file", cascade="all, delete-orphan")


class IngestionRun(Base):
    __tablename__ = "ingestion_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("source_files.id"), nullable=False)
    status: Mapped[RunStatus] = mapped_column(Enum(RunStatus), default=RunStatus.running, nullable=False)
    stage: Mapped[str] = mapped_column(String(128), default="started", nullable=False)
    last_unit: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    chunks_persisted: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    source_file: Mapped["SourceFile"] = relationship(back_populates="runs")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    __table_args__ = (UniqueConstraint("source_file_id", "chunk_index", name="uq_source_chunk"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_file_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("source_files.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(384), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    source_file: Mapped["SourceFile"] = relationship(back_populates="chunks")

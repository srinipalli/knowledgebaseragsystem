from __future__ import annotations

from pathlib import Path
from shutil import move

from langgraph.graph import END, START, StateGraph

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.base import Base
from app.db.session import engine, get_session
from app.embeddings.sentence_transformer import EmbeddingService
from app.graph.state import PipelineState
from app.repositories.ingestion import IngestionRepository
from app.services.checksum import sha256_file
from app.services.checkpoint import CheckpointStore
from app.services.chunking import ProgressiveChunker
from app.services.parser_registry import ParserRegistry

logger = get_logger(__name__)


class IngestionWorkflow:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.registry = ParserRegistry()
        self.embedder = EmbeddingService()
        self.checkpoints = CheckpointStore(self.settings.checkpoint_dir)
        Base.metadata.create_all(bind=engine)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(PipelineState)
        graph.add_node("inspect_file", self.inspect_file)
        graph.add_node("process_stream", self.process_stream)
        graph.add_node("finalize", self.finalize)
        graph.add_node("fail", self.fail)
        graph.add_edge(START, "inspect_file")
        graph.add_conditional_edges(
            "inspect_file",
            self._route_after_inspect,
            {"process_stream": "process_stream", "fail": "fail"},
        )
        graph.add_conditional_edges(
            "process_stream",
            self._route_after_process,
            {"finalize": "finalize", "fail": "fail"},
        )
        graph.add_edge("finalize", END)
        graph.add_edge("fail", END)
        return graph.compile()

    def run(self, file_path: Path) -> PipelineState:
        return self.graph.invoke({"file_path": file_path})

    def inspect_file(self, state: PipelineState) -> PipelineState:
        file_path = Path(state["file_path"])
        session = get_session()
        repository = IngestionRepository(session)
        try:
            checksum = sha256_file(file_path)
            parser = self.registry.resolve(file_path)
            source_file = repository.upsert_source_file(
                path=file_path,
                checksum=checksum,
                size_bytes=file_path.stat().st_size,
                extension=file_path.suffix.lower(),
            )
            run = repository.start_run(source_file)
            total_units = parser.estimate_total_units(file_path)
            checkpoint = self.checkpoints.load(file_path)
            repository.update_source_progress(
                source_file,
                parser_name=parser.name,
                processed_units=checkpoint.get("processed_units", 0),
                total_units=total_units,
            )
            return {
                **state,
                "checksum": checksum,
                "parser_name": parser.name,
                "total_units": total_units,
                "processed_units": checkpoint.get("processed_units", 0),
                "persisted_chunks": checkpoint.get("persisted_chunks", 0),
                "chunk_index": checkpoint.get("chunk_index", 0),
                "source_file_id": str(source_file.id),
                "run_id": str(run.id),
                "error_message": None,
            }
        except Exception as exc:
            return {**state, "error_message": str(exc)}
        finally:
            session.close()

    def process_stream(self, state: PipelineState) -> PipelineState:
        file_path = Path(state["file_path"])
        session = get_session()
        repository = IngestionRepository(session)
        try:
            source_file = repository.get_source_by_path(file_path)
            if source_file is None:
                raise RuntimeError("Source file was not registered before processing")
            run = source_file.runs[-1]
            parser = self.registry.resolve(file_path)
            repository.update_stage(run, "stream_extract")
            chunker = ProgressiveChunker(
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
                chunk_index=state.get("chunk_index", 0),
            )
            pending_rows: list[dict] = []
            processed_units = 0
            for unit in parser.iter_units(file_path):
                if unit.unit_index <= state.get("processed_units", 0):
                    continue
                processed_units = unit.unit_index
                repository.update_stage(run, "chunking", last_unit=unit.unit_index)
                repository.update_source_progress(
                    source_file,
                    parser_name=parser.name,
                    processed_units=processed_units,
                    total_units=state.get("total_units", 0),
                )
                new_chunks = chunker.push(unit.text, unit.metadata)
                for chunk in new_chunks:
                    pending_rows.append(
                        {
                            "chunk_index": chunk["chunk_index"],
                            "unit_index": unit.unit_index,
                            "content": chunk["content"],
                            "metadata": {
                                **chunk["metadata"],
                                "file_name": file_path.name,
                                "checksum": state["checksum"],
                            },
                        }
                    )
                if len(pending_rows) >= self.settings.embed_batch_size:
                    persisted = len(pending_rows)
                    self._embed_and_persist_batch(repository, source_file, run, pending_rows)
                    state["persisted_chunks"] = state.get("persisted_chunks", 0) + persisted
                    self.checkpoints.save(
                        file_path,
                        {
                            "processed_units": processed_units,
                            "persisted_chunks": state["persisted_chunks"],
                            "chunk_index": chunker.chunk_index,
                        },
                    )
                    pending_rows = []

            final_chunks = chunker.flush({"source_type": file_path.suffix.lower().lstrip(".")})
            for chunk in final_chunks:
                pending_rows.append(
                    {
                        "chunk_index": chunk["chunk_index"],
                        "unit_index": processed_units,
                        "content": chunk["content"],
                        "metadata": {
                            **chunk["metadata"],
                            "file_name": file_path.name,
                            "checksum": state["checksum"],
                        },
                    }
                )
            if pending_rows:
                persisted = len(pending_rows)
                self._embed_and_persist_batch(repository, source_file, run, pending_rows)
                state["persisted_chunks"] = state.get("persisted_chunks", 0) + persisted
                self.checkpoints.save(
                    file_path,
                    {
                        "processed_units": processed_units,
                        "persisted_chunks": state["persisted_chunks"],
                        "chunk_index": chunker.chunk_index,
                    },
                )

            return {
                **state,
                "processed_units": processed_units,
                "chunk_index": chunker.chunk_index,
                "error_message": None,
            }
        except Exception as exc:
            logger.exception("pipeline_processing_failed", file_path=str(file_path), error=str(exc))
            return {**state, "error_message": str(exc)}
        finally:
            session.close()

    def finalize(self, state: PipelineState) -> PipelineState:
        file_path = Path(state["file_path"])
        session = get_session()
        repository = IngestionRepository(session)
        try:
            source_file = repository.get_source_by_path(file_path)
            if source_file is None:
                raise RuntimeError("Unable to finalize missing source file")
            run = source_file.runs[-1]
            repository.complete_run(source_file, run)
            destination = self.settings.processed_dir / file_path.name
            self.checkpoints.clear(file_path)
            move(str(file_path), str(destination))
            return {**state, "result": {"status": "completed", "destination": str(destination)}}
        finally:
            session.close()

    def fail(self, state: PipelineState) -> PipelineState:
        file_path = Path(state["file_path"])
        session = get_session()
        repository = IngestionRepository(session)
        try:
            source_file = repository.get_source_by_path(file_path)
            if source_file is not None and source_file.runs:
                repository.fail_run(source_file, source_file.runs[-1], state.get("error_message", "unknown error"))
            destination = self.settings.failed_dir / file_path.name
            if file_path.exists():
                move(str(file_path), str(destination))
            return {**state, "result": {"status": "failed", "destination": str(destination)}}
        finally:
            session.close()

    def _route_after_inspect(self, state: PipelineState) -> str:
        return "fail" if state.get("error_message") else "process_stream"

    def _route_after_process(self, state: PipelineState) -> str:
        return "fail" if state.get("error_message") else "finalize"

    def _embed_and_persist_batch(self, repository: IngestionRepository, source_file, run, rows: list[dict]) -> None:
        embeddings = self.embedder.embed_texts([row["content"] for row in rows])
        payload = []
        for row, embedding in zip(rows, embeddings, strict=True):
            payload.append({**row, "embedding": embedding})
        repository.update_stage(run, "persisting", last_unit=run.last_unit)
        repository.persist_chunk_batch(source_file, run, payload)

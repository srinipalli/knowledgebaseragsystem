# LLMDataPipeline

`LLMDataPipeline` is a standalone folder-based document ingestion system built with `LangGraph`, `PostgreSQL`, and `pgvector`. It scans an input directory, streams document content progressively, chunks it without loading the full file into memory, generates embeddings, and persists both text chunks and vectors.

## Features

- Folder-based ingestion with `scan-once` and `watch-folder` modes
- Streaming page-by-page PDF processing with `PyMuPDF`
- Incremental DOCX and text parsing
- Progressive chunking with LangChain `RecursiveCharacterTextSplitter` and bounded memory usage for large files
- Local open-source embeddings via `sentence-transformers`
- `Postgres + pgvector` for vector search storage
- LangGraph workflow orchestration with stage tracking

## Project Layout

```text
LLMDataPipeline/
  app/
    cli/
    core/
    db/
    embeddings/
    graph/
    parsers/
    repositories/
    services/
  data/
    input/
    processed/
    failed/
    quarantine/
    checkpoints/
  docker/
  pyproject.toml
  docker-compose.yml
```

## How Large File Handling Works

The pipeline is designed to avoid reading full documents into memory.

- PDFs are processed one page at a time
- DOCX files are processed paragraph by paragraph
- Text files are processed line by line
- A rolling text buffer feeds `langchain-text-splitters` so chunks break on natural boundaries when possible
- Chunks are embedded in small batches and immediately committed to Postgres

This keeps memory bounded even when documents are very large. The practical ceiling still depends on parser behavior, model size, and machine resources, but the architecture is built for large-file ingestion rather than whole-file loading.

## Quick Start

1. Copy `.env.example` to `.env`
2. Start Postgres
3. Install the project
4. Drop documents into `data/input`
5. Run the scanner

```bash
docker compose up -d postgres
pip install -e .
llm-pipeline scan-once
```

Or run watch mode:

```bash
llm-pipeline watch-folder
```

## Environment Variables

- `DATABASE_URL`: SQLAlchemy connection string. Default sample: `postgresql+psycopg://postgres:admin123@localhost:5432/postgres`
- `INPUT_DIR`: folder to watch for incoming files
- `PROCESSED_DIR`: successful files are moved here
- `FAILED_DIR`: failed files are moved here
- `QUARANTINE_DIR`: reserved for unsupported or suspicious files
- `EMBEDDING_MODEL`: sentence-transformers model name
- `CHUNK_SIZE`: target chunk size used by the LangChain splitter
- `CHUNK_OVERLAP`: overlap retained between chunks
- `EMBED_BATCH_SIZE`: number of chunks embedded before persistence

## Notes

- Current supported formats: `PDF`, `DOCX`, `TXT`, `MD`
- The schema uses `pgvector` with dimension `384` by default
- The current implementation creates tables on startup for simplicity
- For production, add Alembic migrations, checkpoint persistence, and a search API

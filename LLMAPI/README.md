# LLMAPI

FastAPI backend for RAG chat over the embeddings stored in PostgreSQL `pgvector`.

## Endpoints

- `GET /api/health`
- `POST /api/chat`

## How It Works

1. Accepts a user question
2. Embeds the question using `sentence-transformers`
3. Searches `document_chunks` in Postgres with `pgvector`
4. Sends top matching chunks plus the question to an Ollama model
5. Returns the answer and source chunks

## Run

```bash
copy .env.example .env
python -m pip install -e .
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Required Data

This API expects the `document_chunks` table created by the ingestion pipeline, including:

- `content`
- `chunk_index`
- `unit_index`
- `metadata`
- `embedding`

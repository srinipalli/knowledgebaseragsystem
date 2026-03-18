CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TABLE IF NOT EXISTS chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(128) NOT NULL,
    title VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    message_text TEXT NOT NULL,
    model_name VARCHAR(128),
    sequence_no INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_chat_messages_session_sequence UNIQUE (session_id, sequence_no)
);

CREATE TABLE IF NOT EXISTS chat_message_sources (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    source_file_name VARCHAR(255),
    chunk_id UUID,
    chunk_index INTEGER,
    unit_index INTEGER,
    score DOUBLE PRECISION,
    content TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES chat_messages(id) ON DELETE CASCADE,
    user_id VARCHAR(128) NOT NULL,
    rating SMALLINT NOT NULL CHECK (rating IN (-1, 1)),
    comments TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS chat_session_context (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    context_key VARCHAR(100) NOT NULL,
    context_value TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_user_id
    ON chat_sessions(user_id);

CREATE INDEX IF NOT EXISTS ix_chat_sessions_updated_at
    ON chat_sessions(updated_at DESC);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_id
    ON chat_messages(session_id);

CREATE INDEX IF NOT EXISTS ix_chat_messages_session_sequence
    ON chat_messages(session_id, sequence_no);

CREATE INDEX IF NOT EXISTS ix_chat_message_sources_message_id
    ON chat_message_sources(message_id);

CREATE INDEX IF NOT EXISTS ix_chat_feedback_message_id
    ON chat_feedback(message_id);

CREATE INDEX IF NOT EXISTS ix_chat_session_context_session_id
    ON chat_session_context(session_id);

DROP TRIGGER IF EXISTS trg_chat_sessions_updated_at ON chat_sessions;
CREATE TRIGGER trg_chat_sessions_updated_at
BEFORE UPDATE ON chat_sessions
FOR EACH ROW
EXECUTE FUNCTION set_updated_at();


CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE source_files (
  id UUID PRIMARY KEY,
  path VARCHAR(1024) UNIQUE NOT NULL,
  file_name VARCHAR(255) NOT NULL,
  extension VARCHAR(16) NOT NULL,
  checksum VARCHAR(128) NOT NULL,
  size_bytes BIGINT NOT NULL,
  status VARCHAR(32) NOT NULL,
  parser_name VARCHAR(128),
  total_units INTEGER NOT NULL DEFAULT 0,
  processed_units INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE ingestion_runs (
  id UUID PRIMARY KEY,
  source_file_id UUID NOT NULL REFERENCES source_files(id),
  status VARCHAR(32) NOT NULL,
  stage VARCHAR(128) NOT NULL,
  last_unit INTEGER NOT NULL DEFAULT 0,
  chunks_persisted INTEGER NOT NULL DEFAULT 0,
  error_message TEXT,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ
);

CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  source_file_id UUID NOT NULL REFERENCES source_files(id),
  chunk_index INTEGER NOT NULL,
  unit_index INTEGER NOT NULL DEFAULT 0,
  content TEXT NOT NULL,
  metadata JSON NOT NULL,
  embedding VECTOR(384) NOT NULL,
  created_at TIMESTAMPTZ NOT NULL,
  CONSTRAINT uq_source_chunk UNIQUE (source_file_id, chunk_index)
);

CREATE INDEX ix_source_files_checksum ON source_files(checksum);


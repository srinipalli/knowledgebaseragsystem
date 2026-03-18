from sqlalchemy import text

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.session import get_session

logger = get_logger(__name__)


class PgVectorRetriever:
    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query_embedding: list[float], top_k: int | None = None) -> list[dict]:
        limit = top_k or self.settings.top_k
        logger.info("pgvector_search_started", top_k=limit, embedding_size=len(query_embedding))
        statement = text(
            """
            SELECT
                dc.chunk_index,
                dc.unit_index,
                dc.content,
                dc.metadata->>'file_name' AS file_name,
                1 - (dc.embedding <=> CAST(:embedding AS vector)) AS score
            FROM document_chunks dc
            ORDER BY dc.embedding <=> CAST(:embedding AS vector)
            LIMIT :limit
            """
        )

        with get_session() as session:
            rows = session.execute(
                statement,
                {
                    "embedding": str(query_embedding),
                    "limit": limit,
                },
            ).mappings()
            results = [dict(row) for row in rows]
            logger.info("pgvector_search_completed", results=len(results))
            return results

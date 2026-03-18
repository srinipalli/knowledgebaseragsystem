from sentence_transformers import SentenceTransformer

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        self.settings = get_settings()
        logger.info("embedding_model_loading_started", model=self.settings.embedding_model)
        self.model = SentenceTransformer(self.settings.embedding_model)
        logger.info("embedding_model_loading_completed", model=self.settings.embedding_model)

    def embed_query(self, text: str) -> list[float]:
        logger.info("embedding_query_started", text_length=len(text))
        vector = self.model.encode(text, normalize_embeddings=True)
        logger.info("embedding_query_completed", dimension=len(vector))
        return vector.tolist()

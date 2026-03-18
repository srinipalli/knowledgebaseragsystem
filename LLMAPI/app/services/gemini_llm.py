from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class GeminiService:
    def __init__(self) -> None:
        self.settings = get_settings()
        logger.info("gemini_model_loading_started", model=self.settings.gemini_model)
        self.client = ChatGoogleGenerativeAI(
            model=self.settings.gemini_model,
            google_api_key=self.settings.gemini_api_key,
            temperature=0.2,
        )
        logger.info("gemini_model_loading_completed", model=self.settings.gemini_model)

    def generate_answer(self, question: str, contexts: list[dict]) -> str:
        context_text = "\n\n".join(
            f"Source: {item['file_name']} | Chunk: {item['chunk_index']} | Score: {item['score']:.4f}\n{item['content']}"
            for item in contexts
        )
        logger.info("gemini_generate_started", model=self.settings.gemini_model, context_count=len(contexts))
        try:
            response = self.client.invoke(
                [
                    SystemMessage(
                        content=(
                            "You are a helpful RAG assistant. Answer only from the provided context. "
                            "If the answer is not present, say you do not have enough information."
                        )
                    ),
                    HumanMessage(
                        content=f"Question:\n{question}\n\nContext:\n{context_text}\n\nAnswer:"
                    ),
                ]
            )
            answer = response.content if isinstance(response.content, str) else str(response.content)
            logger.info("gemini_generate_completed", answer_length=len(answer))
            return answer.strip()
        except Exception as exc:
            logger.error("gemini_generate_failed", error=str(exc))
            raise RuntimeError("Could not get a response from Gemini.") from exc

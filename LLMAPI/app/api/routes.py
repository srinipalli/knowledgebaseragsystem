from fastapi import APIRouter

from app.api.schemas import ChatRequest, ChatResponse
from app.core.logging import get_logger
from app.services.rag import RagService

router = APIRouter()
rag_service = RagService()
logger = get_logger(__name__)


@router.get("/health")
def health() -> dict:
    logger.info("health_check_requested")
    return {"status": "ok"}


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    logger.info(
        "chat_request_received",
        question=request.question,
        top_k=request.top_k,
    )
    response = rag_service.ask(request.question, top_k=request.top_k)
    logger.info(
        "chat_request_completed",
        answer_length=len(response.answer),
        source_count=len(response.sources),
    )
    return response

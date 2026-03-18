from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from app.api.schemas import ChatResponse, SourceChunk
from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.embeddings import EmbeddingService
from app.services.gemini_llm import GeminiService
from app.services.retriever import PgVectorRetriever

logger = get_logger(__name__)


class RagState(TypedDict, total=False):
    question: str
    top_k: int
    query_vector: list[float]
    contexts: list[dict]
    answer: str


class RagService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.embedder = EmbeddingService()
        self.retriever = PgVectorRetriever()
        self.llm = GeminiService()
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(RagState)
        graph.add_node("retrieve_context", self.retrieve_context)
        graph.add_node("generate_answer", self.generate_answer)
        graph.add_edge(START, "retrieve_context")
        graph.add_edge("retrieve_context", "generate_answer")
        graph.add_edge("generate_answer", END)
        return graph.compile()

    def retrieve_context(self, state: RagState) -> RagState:
        query_vector = self.embedder.embed_query(state["question"])
        contexts = self.retriever.search(query_vector, top_k=state["top_k"])
        return {
            **state,
            "query_vector": query_vector,
            "contexts": contexts,
        }

    def generate_answer(self, state: RagState) -> RagState:
        contexts = state.get("contexts", [])
        if not contexts:
            logger.info("rag_no_context_found")
            return {
                **state,
                "answer": "I could not find relevant context in Postgres for this question.",
            }

        try:
            answer = self.llm.generate_answer(state["question"], contexts)
        except RuntimeError as exc:
            logger.error("rag_generation_failed", error=str(exc))
            answer = (
                "I retrieved relevant context from Postgres, but the Gemini model is unavailable right now. "
                "Please review the source snippets below."
            )
        return {**state, "answer": answer}

    def ask(self, question: str, top_k: int | None = None) -> ChatResponse:
        logger.info("rag_request_started", question=question, top_k=top_k or self.settings.top_k)
        state = self.graph.invoke(
            {
                "question": question,
                "top_k": top_k or self.settings.top_k,
            }
        )
        contexts = state.get("contexts", [])
        answer = state.get("answer", "No answer generated.")
        logger.info("rag_request_completed", source_count=len(contexts))
        return ChatResponse(
            question=question,
            answer=answer,
            model=self.settings.gemini_model,
            sources=[
                SourceChunk(
                    file_name=item.get("file_name") or "unknown",
                    chunk_index=item["chunk_index"],
                    unit_index=item["unit_index"],
                    content=item["content"],
                    score=float(item["score"]),
                )
                for item in contexts
            ],
        )

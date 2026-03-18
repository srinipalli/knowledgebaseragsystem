from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(min_length=3)
    top_k: int | None = Field(default=None, ge=1, le=20)


class SourceChunk(BaseModel):
    file_name: str
    chunk_index: int
    unit_index: int
    content: str
    score: float


class ChatResponse(BaseModel):
    question: str
    answer: str
    model: str
    sources: list[SourceChunk]

from __future__ import annotations

from dataclasses import dataclass, field

from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass
class ProgressiveChunker:
    chunk_size: int
    chunk_overlap: int
    buffer: str = ""
    chunk_index: int = 0
    splitter: RecursiveCharacterTextSplitter = field(init=False)

    def __post_init__(self) -> None:
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
            length_function=len,
        )

    def push(self, text: str, metadata: dict) -> list[dict]:
        cleaned = text.strip()
        if not cleaned:
            return []

        separator = "\n" if self.buffer else ""
        self.buffer += f"{separator}{cleaned}"
        emitted: list[dict] = []

        if len(self.buffer) < self.chunk_size + self.chunk_overlap:
            return emitted

        safe_cutoff = max(self.chunk_size, len(self.buffer) - self.chunk_overlap)
        stable_text = self.buffer[:safe_cutoff]
        trailing_text = self.buffer[safe_cutoff:]

        split_chunks = self.splitter.split_text(stable_text)
        if not split_chunks:
            return emitted

        for chunk_text in split_chunks[:-1]:
            normalized = chunk_text.strip()
            if not normalized:
                continue
            emitted.append(
                {
                    "chunk_index": self.chunk_index,
                    "content": normalized,
                    "metadata": metadata,
                }
            )
            self.chunk_index += 1

        last_chunk = split_chunks[-1].strip()
        self.buffer = f"{last_chunk}\n{trailing_text}".strip() if last_chunk else trailing_text.strip()
        return emitted

    def flush(self, metadata: dict) -> list[dict]:
        if not self.buffer.strip():
            return []

        chunks = []
        for chunk_text in self.splitter.split_text(self.buffer):
            normalized = chunk_text.strip()
            if not normalized:
                continue
            chunks.append(
                {
                    "chunk_index": self.chunk_index,
                    "content": normalized,
                    "metadata": metadata,
                }
            )
            self.chunk_index += 1

        self.buffer = ""
        return chunks

from app.services.chunking import ProgressiveChunker


def test_progressive_chunker_emits_chunks_and_flushes_tail():
    chunker = ProgressiveChunker(chunk_size=10, chunk_overlap=2)

    chunks = chunker.push("abcdefghij", {"page_number": 1})
    assert len(chunks) == 1
    assert chunks[0]["content"] == "abcdefghij"

    tail = chunker.flush({"page_number": 1})
    assert len(tail) == 1
    assert tail[0]["content"] == "ij"

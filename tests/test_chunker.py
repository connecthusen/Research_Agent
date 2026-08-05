# tests/test_chunker.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.chunker import Chunker

def test_chunker():
    # Sample text (2 sentences)
    text = "This is the first sentence. This is the second sentence."
    chunker = Chunker(chunk_size=5, overlap=1)
    chunks = chunker.chunk_text(text, source_id="test_source")

    print(f"[INFO] Original text: {text}")
    print(f"[CHUNKS] Chunks:")
    for chunk in chunks:
        print(f"  - Chunk {chunk['chunk_index']}: {chunk['text']} (Source: {chunk['source_id']})")

    assert len(chunks) >= 1, "Expected at least 1 chunk"
    assert all("source_id" in chunk for chunk in chunks), "Missing source_id in chunks"
    print("[PASS] Chunker test passed!")

if __name__ == "__main__":
    test_chunker()
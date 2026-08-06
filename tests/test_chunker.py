# tests/test_chunker.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.chunker import Chunker

def test_chunker_fallback():
    text = "This is the first sentence. This is the second sentence."
    chunker = Chunker(chunk_size=5, overlap=1, use_tokenizer=False)
    chunks = chunker.chunk_text(text, source_id="test_source")

    assert len(chunks) >= 1, "Expected at least 1 chunk"
    assert all("source_id" in chunk for chunk in chunks), "Missing source_id in chunks"
    print("[PASS] Fallback chunker test passed!")


def test_true_token_chunker():
    text = "Artificial intelligence and machine learning models use sub-word tokenization methods."
    chunker = Chunker(chunk_size=10, overlap=2, use_tokenizer=True)

    # Test count function directly
    count = chunker._count_tokens("tokenization")
    assert count > 1, "Expected sub-word tokenization to count > 1 token for 'tokenization'"

    chunks = chunker.chunk_text(text, source_id="test_source")
    assert len(chunks) >= 1
    print("[PASS] True token chunker test passed!")


if __name__ == "__main__":
    test_chunker_fallback()
    test_true_token_chunker()
    print("[PASS] All chunker tests passed!")
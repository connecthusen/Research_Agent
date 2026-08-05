# tests/test_vector_store.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.ingestion.chunker import Chunker
from src.embedding.vector_store import VectorStore

def test_vector_store():
    # Step 1: Create sample chunks
    text = "This is a test sentence. This is another test sentence."
    chunker = Chunker(chunk_size=5, overlap=1)
    chunks = chunker.chunk_text(text, source_id="test_source")

    # Step 2: Add chunks to ChromaDB
    vector_store = VectorStore(collection_name="test_collection")
    vector_store.add_chunks(chunks)

    # Step 3: Query ChromaDB
    results = vector_store.query("What is the test sentence?", k=2)
    print("[INFO] Query: 'What is the test sentence?'")
    print("[CHUNKS] Results:")
    for result in results:
        print(f"  - Text: {result['text']}")
        print(f"    Source: {result['source_id']}, Chunk: {result['chunk_index']}, Score: {result['score']:.4f}")

    # Step 4: Clean up
    vector_store.clear()
    print("[PASS] VectorStore test passed!")

if __name__ == "__main__":
    test_vector_store()
# main.py
from src.ingestion.source_loader import SourceLoader
from src.ingestion.chunker import Chunker
from src.embedding.vector_store import VectorStore
from src.retrieval.keyword_search import KeywordSearch
from src.retrieval.hybrid_retriever import HybridRetriever
from src.generation.qa_engine import QAEngine
from config.settings import TOP_K_CHUNKS

def main():
    print("[Search] Research Agent - Ask a question (or 'quit' to exit)")

    # Step 1: Load sources
    loader = SourceLoader()
    sources, failures = loader.fetch_all()
    if failures:
        print(f"[WARN] Failed to fetch {len(failures)} sources. Proceeding with {len(sources)} successful sources.")

    # Step 2: Chunk sources
    chunker = Chunker()
    chunks = chunker.chunk_sources(sources)
    print(f"[INFO] Generated {len(chunks)} chunks from {len(sources)} sources.")

    # Step 3: Build vector store and keyword index
    vector_store = VectorStore()
    vector_store.add_chunks(chunks)

    keyword_search = KeywordSearch()
    keyword_search.build(chunks)
    keyword_search.save()

    # Step 4: Initialize retriever and QA engine
    retriever = HybridRetriever(vector_store, keyword_search)
    qa_engine = QAEngine(retriever)

    # Step 5: Interactive Q&A
    while True:
        question = input("\nQuestion: ").strip()
        if question.lower() == "quit":
            break

        chunks = retriever.retrieve(question, k=TOP_K_CHUNKS)
        result = qa_engine.answer_question(question, k=TOP_K_CHUNKS)

        print("\nAnswer:")
        print(result["answer"])
        print("\nCitations:", result["citations"])
        print("Confidence:", f"{result['confidence']:.2f}")

if __name__ == "__main__":
    main()
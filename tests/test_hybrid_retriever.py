# tests/test_hybrid_retriever.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.retrieval.hybrid_retriever import HybridRetriever


class FakeVectorStore:
    """Returns fixed 0-1 'similarity' scores, mimicking the fixed vector_store.py."""
    def query(self, query, k=5):
        return [
            {"text": "chess en passant rule", "source_id": "chess_guide_pdf", "chunk_index": 0, "score": 0.91},
            {"text": "chess opening principles", "source_id": "chess_guide_pdf", "chunk_index": 1, "score": 0.40},
            {"text": "unrelated cricket text", "source_id": "cricket_rules_pdf", "chunk_index": 2, "score": 0.10},
        ][:k]


class FakeKeywordSearch:
    """Returns unbounded BM25-style scores."""
    def query(self, query, k=5):
        return [
            {"text": "chess en passant rule", "source_id": "chess_guide_pdf", "chunk_index": 0, "score": 12.4},
            {"text": "cricket LBW explanation", "source_id": "cricket_rules_pdf", "chunk_index": 5, "score": 3.1},
        ][:k]


class FakeVectorStoreAllZero:
    def query(self, query, k=5):
        return []


class FakeKeywordSearchAllZero:
    def query(self, query, k=5):
        return []


def test_fusion_prefers_chunk_strong_on_both_signals():
    retriever = HybridRetriever(FakeVectorStore(), FakeKeywordSearch(), alpha=0.5, use_reranker=False)
    results = retriever.retrieve("en passant rule", k=3)

    assert results[0]["source_id"] == "chess_guide_pdf"
    assert results[0]["chunk_index"] == 0, "Chunk strong in both vector and keyword should rank #1"
    assert 0.0 <= results[0]["score"] <= 1.0, "Fused score should stay in 0-1 after normalization"
    print("[PASS] Fusion ranking test passed!")


def test_union_keeps_single_signal_chunks():
    retriever = HybridRetriever(FakeVectorStore(), FakeKeywordSearch(), alpha=0.5, use_reranker=False)
    results = retriever.retrieve("test", k=10)
    ids = {(r["source_id"], r["chunk_index"]) for r in results}

    # cricket_rules_pdf chunk_index=5 only appeared in keyword results
    assert ("cricket_rules_pdf", 5) in ids, "Chunk found by only one retriever should still surface"
    print("[PASS] Union-of-candidates test passed!")


def test_is_answerable_threshold():
    retriever = HybridRetriever(FakeVectorStore(), FakeKeywordSearch(), alpha=0.5, use_reranker=False)
    results = retriever.retrieve("en passant rule", k=3)
    assert retriever.is_answerable(results, threshold=0.15) is True

    assert retriever.is_answerable([], threshold=0.15) is False, "No results should never be answerable"
    print("[PASS] is_answerable threshold test passed!")


def test_empty_results_from_both_retrievers():
    retriever = HybridRetriever(FakeVectorStoreAllZero(), FakeKeywordSearchAllZero(), alpha=0.5, use_reranker=False)
    results = retriever.retrieve("anything", k=5)
    assert results == []
    assert retriever.is_answerable(results) is False
    print("[PASS] Empty-retrievers edge case test passed!")


class FakeReranker:
    def predict(self, pairs):
        scores = []
        for query, text in pairs:
            if "opening" in text:
                scores.append(2.0)
            elif "passant" in text:
                scores.append(0.5)
            else:
                scores.append(-2.0)
        return scores


def test_reranker_sorting_and_sigmoid():
    retriever = HybridRetriever(FakeVectorStore(), FakeKeywordSearch(), alpha=0.5, use_reranker=True)
    retriever.reranker = FakeReranker()
    results = retriever.retrieve("chess rule", k=3)

    # "chess opening principles" should be ranked first because logit 2.0 (sigmoid ~ 0.88) > logit 0.5 (sigmoid ~ 0.62)
    assert "opening" in results[0]["text"]
    assert "passant" in results[1]["text"]

    import math
    expected_score_0 = 1 / (1 + math.exp(-2.0))
    expected_score_1 = 1 / (1 + math.exp(-0.5))
    assert abs(results[0]["score"] - expected_score_0) < 1e-5
    assert abs(results[1]["score"] - expected_score_1) < 1e-5
    print("[PASS] Reranker sorting and sigmoid test passed!")


if __name__ == "__main__":
    test_fusion_prefers_chunk_strong_on_both_signals()
    test_union_keeps_single_signal_chunks()
    test_is_answerable_threshold()
    test_empty_results_from_both_retrievers()
    test_reranker_sorting_and_sigmoid()
    print("\n[PASS] All hybrid_retriever tests passed!")
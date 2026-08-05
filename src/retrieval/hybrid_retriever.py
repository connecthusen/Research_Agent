# src/retrieval/hybrid_retriever.py
"""
Fuses VectorStore (semantic, cosine similarity, 0-1, higher=better) and
KeywordSearch (BM25, unbounded, higher=better) results.

Both retrievers already return "higher = more relevant" scores (see the
vector_store.py fix), so no inversion is needed here -- but the *scales*
differ (0-1 bounded vs unbounded BM25). Fusing raw scores would let vector
similarity dominate every query regardless of actual relevance, so each
side is min-max normalized to 0-1 first. This is the same class of bug
already caught twice in this project (raw distance vs similarity) --
don't skip it here too.
"""
from typing import List, Dict

from config.settings import (
    HYBRID_ALPHA,
    CANDIDATE_K_CHUNKS,
    NO_ANSWER_THRESHOLD,
)


class HybridRetriever:
    def __init__(self, vector_store, keyword_search, alpha: float = HYBRID_ALPHA):
        """
        Args:
            vector_store: an initialized VectorStore instance.
            keyword_search: an initialized KeywordSearch instance
                             (already built or loadable from disk).
            alpha: weight on the normalized vector score;
                   (1 - alpha) goes to the normalized keyword score.
        """
        self.vector_store = vector_store
        self.keyword_search = keyword_search
        self.alpha = alpha

    @staticmethod
    def _normalize(results: List[Dict]) -> Dict[str, float]:
        """Min-max normalize scores to 0-1, keyed by a stable chunk id.
        If every score is identical, all normalized scores collapse to 1.0
        (they were all equally relevant, not equally irrelevant)."""
        if not results:
            return {}
        scores = [r["score"] for r in results]
        lo, hi = min(scores), max(scores)
        span = hi - lo
        return {
            f"{r['source_id']}_{r['chunk_index']}": (1.0 if span == 0 else (r["score"] - lo) / span)
            for r in results
        }

    def retrieve(self, query: str, k: int = 5, candidate_k: int = CANDIDATE_K_CHUNKS) -> List[Dict]:
        """
        Returns the top-k fused chunks, each with a 0-1 'score' field
        (weighted combination of normalized vector + keyword scores).
        """
        vector_results = self.vector_store.query(query, k=candidate_k)
        keyword_results = self.keyword_search.query(query, k=candidate_k)

        vector_norm = self._normalize(vector_results)
        keyword_norm = self._normalize(keyword_results)

        # Union of candidates from both sides, keyed by chunk id, so a chunk
        # that only one retriever surfaced still gets scored (with 0 on the
        # side that missed it) instead of being dropped.
        by_id: Dict[str, Dict] = {}
        for r in vector_results + keyword_results:
            key = f"{r['source_id']}_{r['chunk_index']}"
            by_id.setdefault(key, {
                "text": r["text"],
                "source_id": r["source_id"],
                "chunk_index": r["chunk_index"],
            })

        fused = []
        for key, chunk in by_id.items():
            v_score = vector_norm.get(key, 0.0)
            k_score = keyword_norm.get(key, 0.0)
            fused_score = self.alpha * v_score + (1 - self.alpha) * k_score
            fused.append({**chunk, "score": fused_score})

        fused.sort(key=lambda r: r["score"], reverse=True)
        return fused[:k]

    def is_answerable(self, results: List[Dict], threshold: float = NO_ANSWER_THRESHOLD) -> bool:
        """
        Top fused score below threshold => treat the question as
        'sources don't contain the answer' rather than letting the LLM
        potentially hallucinate a response from weak context.
        """
        if not results:
            return False
        return results[0]["score"] >= threshold
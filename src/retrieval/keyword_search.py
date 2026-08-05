# src/retrieval/keyword_search.py
"""
BM25-based keyword search over the same chunks that get embedded into
ChromaDB. Persisted to disk (pickle) so a fresh process can query without
re-running ingestion, mirroring how VectorStore persists via data/chroma_db/.

Requires: pip install rank-bm25
"""
from typing import List, Dict
import os
import pickle
import re

from rank_bm25 import BM25Okapi

DEFAULT_INDEX_PATH = "data/bm25_index.pkl"


class KeywordSearch:
    def __init__(self, index_path: str = DEFAULT_INDEX_PATH):
        self.index_path = index_path
        self.bm25 = None
        self.chunks: List[Dict] = []  # parallel to the BM25 corpus, holds metadata

    @staticmethod
    def _tokenize(text: str) -> List[str]:
        # Simple, deterministic tokenizer: lowercase, alphanumeric only.
        return re.findall(r"[a-z0-9]+", text.lower())

    def build(self, chunks: List[Dict]) -> None:
        """
        Build the BM25 index from chunks -- same shape VectorStore.add_chunks
        expects: [{"text", "source_id", "chunk_index"}, ...]
        Call this during ingestion, right alongside vector_store.add_chunks().
        """
        if not chunks:
            raise ValueError("Cannot build a keyword index from an empty chunk list.")

        self.chunks = chunks
        tokenized_corpus = [self._tokenize(c["text"]) for c in chunks]
        self.bm25 = BM25Okapi(tokenized_corpus)

    def save(self) -> None:
        if self.bm25 is None:
            raise RuntimeError("Nothing to save -- call build() first.")
        os.makedirs(os.path.dirname(self.index_path) or ".", exist_ok=True)
        with open(self.index_path, "wb") as f:
            pickle.dump({"bm25": self.bm25, "chunks": self.chunks}, f)
        print(f"[PASS] Saved BM25 index ({len(self.chunks)} chunks) to {self.index_path}")

    def load(self) -> bool:
        """Returns True if an index was found on disk and loaded."""
        if not os.path.exists(self.index_path):
            return False
        with open(self.index_path, "rb") as f:
            data = pickle.load(f)
        self.bm25 = data["bm25"]
        self.chunks = data["chunks"]
        return True

    def query(self, query: str, k: int = 5) -> List[Dict]:
        """
        Returns top-k chunks with a BM25 score. Higher = more relevant --
        same "higher is better" convention as VectorStore.query()'s
        similarity score, so hybrid_retriever.py can fuse them without
        inverting either one (only normalizing for scale).
        """
        if self.bm25 is None:
            if not self.load():
                raise RuntimeError(
                    "Keyword index not built or found on disk. "
                    "Call build() + save() during ingestion first."
                )

        tokenized_query = self._tokenize(query)
        scores = self.bm25.get_scores(tokenized_query)

        ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
        results = []
        for i in ranked_indices:
            chunk = self.chunks[i]
            results.append({
                "text": chunk["text"],
                "source_id": chunk["source_id"],
                "chunk_index": chunk["chunk_index"],
                "score": float(scores[i]),  # unbounded, higher = more relevant
            })
        return results
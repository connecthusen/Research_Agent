# src/embedding/vector_store.py
from typing import List, Dict
import chromadb
from sentence_transformers import SentenceTransformer
import os
from config.settings import Settings


class VectorStore:
    def __init__(self, collection_name: str = "research_agent", model_name: str = "all-MiniLM-L6-v2"):
        """
        Initialize ChromaDB and the embedding model.
        Args:
            collection_name: Name of the ChromaDB collection.
            model_name: Sentence Transformer model for embeddings.
        """
        self.collection_name = collection_name

        # HF_TOKEN is optional (public model) -- only set env var if present,
        # so this doesn't crash when it's unset.
        if Settings.HF_TOKEN:
            os.environ["HF_TOKEN"] = Settings.HF_TOKEN

        self.model = SentenceTransformer(model_name)
        self.client = chromadb.PersistentClient(path="data/chroma_db")
        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create a ChromaDB collection, explicitly on cosine space.
        get_or_create_collection is the built-in convenience method --
        no need to catch a version-fragile NotFoundError.

        NOTE: if metadata is only applied on *creation*, an existing
        collection created before this fix (default L2 space) will keep
        using L2. If you already ran ingestion before this fix, delete
        data/chroma_db/ once and re-run ingestion so cosine space takes
        effect.
        """
        return self.client.get_or_create_collection(
            self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def _generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts).tolist()

    def add_chunks(self, chunks: List[Dict]) -> None:
        """
        Add (or update) chunks in ChromaDB with embeddings. Uses upsert
        so re-running ingestion on the same source doesn't error on
        duplicate deterministic IDs (source_id_chunkindex).
        Args:
            chunks: List of chunks (from Chunker.chunk_sources()).
        """
        if not chunks:
            print("[WARN] No chunks to add.")
            return

        texts = [chunk["text"] for chunk in chunks]
        embeddings = self._generate_embeddings(texts)

        metadatas = [
            {
                "source_id": chunk["source_id"],
                "chunk_index": chunk["chunk_index"],
            }
            for chunk in chunks
        ]

        self.collection.upsert(
            documents=texts,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=[f"{chunk['source_id']}_{chunk['chunk_index']}" for chunk in chunks],
        )
        print(f"[PASS] Upserted {len(chunks)} chunks into ChromaDB.")

    def query(self, query: str, k: int = 3) -> List[Dict]:
        """
        Query ChromaDB for top-k similar chunks.
        Args:
            query: User's question.
            k: Number of results to return.
        Returns:
            List of top-k chunks with a 0-1 similarity score (higher = more
            similar), so it fuses correctly with BM25 scores downstream.
        """
        query_embedding = self.model.encode([query]).tolist()[0]
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=k,
        )

        formatted_results = []
        docs = results["documents"][0] if results["documents"] else []
        for i in range(len(docs)):
            distance = results["distances"][0][i]  # cosine distance, lower = more similar
            similarity = 1 - distance  # valid conversion only because space="cosine"
            formatted_results.append({
                "text": docs[i],
                "source_id": results["metadatas"][0][i]["source_id"],
                "chunk_index": results["metadatas"][0][i]["chunk_index"],
                "score": similarity,  # higher = more similar, matches BM25 convention
            })
        return formatted_results

    def clear(self) -> None:
        """Clear the ChromaDB collection by deleting and recreating it."""
        try:
            self.client.delete_collection(self.collection_name)
            self.collection = self._get_or_create_collection()
            print("[INFO] Cleared ChromaDB collection.")
        except Exception as e:
            print(f"[WARN] Failed to clear collection: {e}")
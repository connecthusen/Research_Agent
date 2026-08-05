# src/generation/qa_engine.py
from groq import Groq
from config.settings import Settings
from ..retrieval.hybrid_retriever import HybridRetriever
import os

class QAEngine:
    def __init__(self, retriever: HybridRetriever):
        self.client = Groq(api_key=Settings.GROQ_API_KEY)  # Load from .env
        self.retriever = retriever
        self.REFUSAL_MESSAGE = "The provided sources do not contain this information."

    def _generate_prompt(self, question: str, chunks: List[Dict]) -> str:
        """Build a prompt that forces the LLM to cite sources."""
        context = "\n".join(
            f"[Source: {chunk['source_id']}] {chunk['text']}"
            for chunk in chunks
        )
        return f"""
        You are a research assistant. Answer the question using ONLY the provided context.
        For every claim, cite the source ID in square brackets (e.g., [source1]).
        If the answer is not in the context, respond with: "{self.REFUSAL_MESSAGE}"

        Context:
        {context}

        Question: {question}
        Answer:
        """

    def answer_question(self, question: str, min_relevance_score: float = 0.3) -> Dict:
        """Retrieve chunks, then synthesize an answer with citations."""
        # Step 1: Retrieve relevant chunks
        chunks, is_answerable = self.retriever.retrieve(
            query=question,
            k=3,
            min_relevance=min_relevance_score
        )

        # Step 2: Hard refusal if no relevant chunks
        if not is_answerable:
            return {
                "answer": self.REFUSAL_MESSAGE,
                "citations": [],
                "confidence": 0.0
            }

        # Step 3: Generate answer with citations
        prompt = self._generate_prompt(question, chunks)
        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=1024,
            )
            answer = response.choices[0].message.content.strip()

            # Step 4: Extract citations (basic parsing for demo)
            citations = self._extract_citations(answer)
            confidence = self._estimate_confidence(chunks, answer)

            return {
                "answer": answer,
                "citations": citations,
                "confidence": confidence
            }
        except Exception as e:
            return {
                "answer": f"Error generating answer: {str(e)}",
                "citations": [],
                "confidence": 0.0
            }

    def _extract_citations(self, answer: str) -> List[str]:
        """Extract [source_id] citations from the answer."""
        import re
        return re.findall(r"\[(source\w+)\]", answer)

    def _estimate_confidence(self, chunks: List[Dict], answer: str) -> float:
        """Estimate confidence based on chunk relevance scores."""
        if not chunks:
            return 0.0
        avg_relevance = sum(chunk["score"] for chunk in chunks) / len(chunks)
        return min(1.0, avg_relevance * 1.2)  # Scale to 0-1
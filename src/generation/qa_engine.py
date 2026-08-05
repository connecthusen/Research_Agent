# src/generation/qa_engine.py
from typing import List, Dict
import os
from groq import Groq
from config.settings import Settings, NO_ANSWER_MESSAGE, GROQ_MODEL
from src.retrieval.hybrid_retriever import HybridRetriever
from src.utils.security import PromptInjectionDetector

class QAEngine:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.client = Groq(api_key=Settings.GROQ_API_KEY)
        self.model = GROQ_MODEL
        self.refusal_message = NO_ANSWER_MESSAGE
        self.security_detector = PromptInjectionDetector()

    def answer_question(self, question: str, k: int = 3) -> Dict:
        """
        Args:
            question: User's question.
            k: Number of chunks to retrieve.
        Returns:
            Dict: {"answer": str, "citations": List[str], "confidence": float}
        """
        # Security check first
        if not self.security_detector.is_safe(question):
            return {
                "answer": self.security_detector.get_restricted_response(),
                "citations": [],
                "confidence": 0.0,
            }

        # Retrieve chunks
        chunks = self.retriever.retrieve(question, k=k)
        is_answerable = self.retriever.is_answerable(chunks)

        if not is_answerable:
            return {
                "answer": self.refusal_message,
                "citations": [],
                "confidence": 0.0,
            }

        # Generate answer with Groq
        answer = self._generate_answer(question, chunks)
        citations = self._extract_citations(answer)
        confidence = self._estimate_confidence(chunks)

        return {
            "answer": answer,
            "citations": citations,
            "confidence": confidence,
        }

    def _generate_answer(self, question: str, chunks: List[Dict]) -> str:
        """Generate an answer using Groq LLaMA."""
        context = "\n".join(
            f"[Source: {chunk['source_id']}] {chunk['text']}"
            for chunk in chunks
        )
        prompt = f"""
        You are a research assistant. Answer the question using ONLY the provided context.
        For every claim, cite the source ID in square brackets (e.g., [source1]).
        If the answer is not in the context, respond with: "{self.refusal_message}"

        Context:
        {context}

        Question: {question}
        Answer:
        """

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=1024,
        )
        return response.choices[0].message.content.strip()

    def _extract_citations(self, answer: str) -> List[str]:
        """Extract [source_id] citations from the answer."""
        import re
        return re.findall(r"\[([\w\-]+)\]", answer)

    def _estimate_confidence(self, chunks: List[Dict]) -> float:
        """Estimate confidence based on chunk scores."""
        if not chunks:
            return 0.0
        avg_score = sum(chunk["score"] for chunk in chunks) / len(chunks)
        return min(1.0, avg_score * 1.2)
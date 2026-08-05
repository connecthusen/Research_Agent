# config/settings.py
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    HF_TOKEN = os.getenv("HF_TOKEN")  # optional

    @classmethod
    def require_groq(cls):
        """Call this only where a real LLM call is about to happen
        (inside qa_engine.py), not on import."""
        if not cls.GROQ_API_KEY:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file, or "
                "run qa_engine.py in mock mode."
            )


GROQ_MODEL = "llama-3.3-70b-versatile"
NO_ANSWER_MESSAGE = "I don't have data regarding this in the provided sources."

# --- Retrieval tuning (used by src/retrieval/hybrid_retriever.py) ---
TOP_K_CHUNKS = 5              # chunks handed to the LLM as final context
CANDIDATE_K_CHUNKS = 15       # candidates pulled from each retriever pre-fusion
HYBRID_ALPHA = 0.5            # weight on vector score; (1 - alpha) on keyword score
NO_ANSWER_THRESHOLD = 0.15    # fused top score below this => "not answerable"
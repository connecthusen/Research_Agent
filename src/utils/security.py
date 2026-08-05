# src/utils/security.py
import re
from typing import List

class PromptInjectionDetector:
    def __init__(self):
        # List of regex patterns for restricted queries
        self.restricted_patterns = [
            # API keys / secrets
            r"(?i)(groq|openai|api[\s_-]?key|secret|password|token|credential)",
            # System access
            r"(?i)(rm[\s_-]?rf|sudo|bash|sh|exec|execute|system|subprocess)",
            # File system access
            r"(?i)(read[\s_-]?file|write[\s_-]?file|delete|overwrite|mkdir|chmod|passwd|etc/passwd|etc/shadow|boot\.ini)",
            # Code execution
            r"(?i)(eval|exec|compile|import[\s_-]?os|import[\s_-]?subprocess)",
            # Personal data
            r"(?i)(ssn|credit[\s_-]?card|bank|account[\s_-]?number|private[\s_-]?key)",
            # Debugging
            r"(?i)(debug|test[\s_-]?mode|internal|admin|root)",
            # Bypass attempts
            r"(?i)(ignore[\s_-]?previous|disregard|forget[\s_-]?all|override[\s_-]?safety)",
        ]

        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern) for pattern in self.restricted_patterns]

    def is_safe(self, query: str) -> bool:
        """
        Check if the query is safe (no prompt injection).
        Args:
            query: User's input.
        Returns:
            bool: True if safe, False if restricted.
        """
        if not query:
            return True

        for pattern in self.compiled_patterns:
            if pattern.search(query):
                return False
        return True

    def get_restricted_response(self) -> str:
        """
        Return a standardized refusal message for restricted queries.
        """
        return "I am restricted from answering this question."
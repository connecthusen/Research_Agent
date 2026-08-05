# src/ingestion/chunker.py
from typing import List, Dict
import re


class Chunker:
    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """
        Args:
            chunk_size: Target size per chunk, in whitespace tokens.
            overlap: Number of TOKENS to carry into the next chunk.
                     (Bug fixed: previously sliced by sentence *count* using
                     a number meant for tokens, so overlap=50 pulled in
                     almost every prior sentence -- massive duplication.)
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def _split_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]

    def _count_tokens(self, text: str) -> int:
        return len(text.split())

    def _split_long_sentence(self, sentence: str) -> List[str]:
        """Fallback for a single 'sentence' longer than chunk_size -- common
        in messy PDF extraction where periods get lost. Splits by raw word
        count so nothing silently produces one giant oversized chunk."""
        words = sentence.split()
        return [
            " ".join(words[i:i + self.chunk_size])
            for i in range(0, len(words), self.chunk_size)
        ]

    def _take_token_overlap(self, sentences: List[str]) -> List[str]:
        """Walk backward through `sentences`, keeping whole sentences until
        ~self.overlap tokens are collected. Token-based, not sentence-count."""
        if self.overlap <= 0 or not sentences:
            return []
        kept = []
        token_total = 0
        for sentence in reversed(sentences):
            if token_total >= self.overlap:
                break
            kept.insert(0, sentence)
            token_total += self._count_tokens(sentence)
        return kept

    def chunk_text(self, text: str, source_id: str) -> List[Dict]:
        raw_sentences = self._split_sentences(text)

        # Pre-split any sentence that alone exceeds chunk_size
        sentences = []
        for s in raw_sentences:
            if self._count_tokens(s) > self.chunk_size:
                sentences.extend(self._split_long_sentence(s))
            else:
                sentences.append(s)

        chunks = []
        current_chunk: List[str] = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_tokens = self._count_tokens(sentence)

            if current_length + sentence_tokens <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += sentence_tokens
            else:
                if current_chunk:
                    chunks.append({
                        "text": " ".join(current_chunk),
                        "source_id": source_id,
                        "chunk_index": chunk_index,
                    })
                    chunk_index += 1

                overlap_sentences = self._take_token_overlap(current_chunk)
                current_chunk = overlap_sentences + [sentence]
                current_length = sum(self._count_tokens(s) for s in current_chunk)

        if current_chunk:
            chunks.append({
                "text": " ".join(current_chunk),
                "source_id": source_id,
                "chunk_index": chunk_index,
            })

        return chunks

    def chunk_sources(self, sources: List[Dict]) -> List[Dict]:
        all_chunks = []
        for source in sources:
            chunks = self.chunk_text(source["text"], source["id"])
            all_chunks.extend(chunks)
        return all_chunks
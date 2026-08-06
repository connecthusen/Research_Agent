# 📘 Design Notes - Research Agent RAG System

This document captures the architectural decisions, math, algorithms, and engineering choices behind the **Research Agent** Retrieval-Augmented Generation (RAG) system.

---

## 1. Hybrid Retrieval & Score Fusion Strategy

A classic problem in RAG systems is the disparity in scale and meaning of scores returned by different retrieval algorithms:
*   **Dense Vectors (Semantic)**: Cosine similarity outputs scores strictly bounded between `0.0` (completely dissimilar) and `1.0` (identical vectors) in the embedding space.
*   **Sparse Keywords (BM25)**: Scores represent term frequency/inverse document frequency metrics and are theoretically unbounded (`0` to `+inf`), usually scaling with query size and document length.

### The Scale Disparity Challenge
If we were to directly sum raw BM25 scores and Cosine similarity scores:
$$\text{Score}_{\text{raw}} = \text{Score}_{\text{cosine}} + \text{Score}_{\text{BM25}}$$
BM25 scores (often ranging from `5.0` to `25.0` or higher) would completely wash out cosine similarity changes (which vary in fractions between `0.1` and `0.9`).

### Resolution: Min-Max Normalization & Weighted Fusion
To resolve this, the system performs a localized min-max normalization on candidate chunks retrieved by each search method before fusion:

$$\text{Score}_{\text{normalized}} = \frac{\text{Score} - \text{Score}_{\text{min}}}{\text{Score}_{\text{max}} - \text{Score}_{\text{min}}}$$

This scales candidates from both retrievers to a consistent $[0.0, 1.0]$ range. We then compute the final hybrid score:

$$\text{Score}_{\text{hybrid}} = \alpha \cdot \text{Score}_{\text{vector-norm}} + (1 - \alpha) \cdot \text{Score}_{\text{keyword-norm}}$$

*   `alpha` is set to `0.5` by default to give equal weight to semantic meaning and exact keyword matching.
*   Retrieval yields the top-K chunks with the highest hybrid scores.

---

## 2. Preventing LLM Hallucinations (Answerability Check)

Large Language Models (LLMs) tend to fabricate details (hallucinate) when asked questions for which no relevant source text is provided. 
To safeguard against this, the system implements an **Answerability Threshold** check in `HybridRetriever`:
*   `NO_ANSWER_THRESHOLD` is set to `0.15` by default.
*   If the highest hybrid score of the retrieved context chunks is below this threshold, the query is marked as "unanswerable from current sources".
*   In this case, the `QAEngine` completely bypasses the LLM execution and immediately returns:
    `"I don't have data regarding this in the provided sources."`

---

## 3. Ingestion & Token-Aware Chunker Design

### Sentence-Preserving Sliding Window
To avoid cutting sentences in half (which destroys semantic readability and local cohesion), the chunker:
1.  Splits input text into sentences using lookbehind regex (`(?<=[.!?])\s+`).
2.  Aggregates whole sentences until they approach the target `chunk_size` limit (default `512` whitespace tokens).
3.  Carries over an overlap window calculated in tokens (default `50` tokens) by pulling in whole sentences from the end of the previous chunk.

### Long Sentence Fallback
In document extraction (particularly noisy PDFs), punctuation marks like periods can get lost, resulting in single giant strings of words. If a single "sentence" exceeds the 512-token limit, the chunker falls back to splitting by raw token count so that chunks do not grow unbounded.

---

## 4. Multi-Layer Input Security Layer

The `PromptInjectionDetector` class acts as a fast, pre-execution regex firewall.

### Precompiled Fast Patterns
The detector uses compiled case-insensitive regex patterns targeting:
1.  **API/Credential Exposure**: Block queries seeking api keys, system passwords, or tokens (e.g. `groq`, `openai`, `api_key`).
2.  **System/Shell Commands**: Intercept attempts to inject unix/dos commands (e.g. `rm -rf`, `sudo`, `bash`, `subprocess`).
3.  **File System Bypass**: Detect attempts to read/write/overwrite standard file directories or target system files (e.g. `passwd`, `/etc/passwd`, `/etc/shadow`, `boot.ini`).
4.  **Bypass Attempts**: Block instructions aiming to wipe LLM context instructions (e.g., `"ignore previous instructions"`, `"forget all safety overrides"`).

### Robust Tokenizer Separator Support
Instead of checking literal words or strictly requiring hyphens/underscores (`[_-]?`), all patterns allow standard space characters (`[\s_-]?`). This ensures human phrases (such as `"ignore previous"` or `"api key"`) trigger the safety block.

---

## 5. Output Citation Extraction

To maintain verifiable citations, we instruct the LLM to cite source IDs in square brackets (e.g., `[chess_strategy_url]`).
The extraction regex matches any alphanumeric/hyphen string within brackets:
`r"\[([\w\-]+)\]"`
This allows the parser to successfully match document keys like `chess_strategy_url` or `cricket-laws-wiki` and populate the clean `citations` list returned to the user.

---

## 6. Premium Streamlit User Interface & Dashboard Architecture

To make the RAG system accessible and highly interactive, the **Research Agent** features a premium Streamlit web application.

### Glassmorphic & Custom CSS Theme
Custom CSS injection overrides default Streamlit interface wrappers to establish an ultra-premium dark theme (`#080c14` background, `#c9d1e0` foreground). Key UI overrides include:
*   **Typography**: Imports Google Fonts to render UI elements in *Inter* and code segments/source labels in *JetBrains Mono*.
*   **Chat Bubbles**: Renders user messages as blue gradients and assistant answers in deep steel blue (`#0d1626`) with glowing left-side highlights.
*   **Dynamic Layout**: Sets main containers to full-bleed wide-mode width (`95%`) for maximum layout efficiency.
*   **Adversarial Visual Hooks**: Injects glowing red warning boxes and visual bypass indicators into the message timeline when a security threat is detected.

### Dynamic Knowledge Base Management
Rather than relying on a static index built beforehand, the sidebar dashboard acts as an administration control center:
1.  **Source Upload/Removal**: Handles local PDF saves into `data/pdfs` and standardizes URL domain paths before writing/clearing objects in `config/sources.json`.
2.  **Live Reindexing Trigger**: Clicking "Build / Reindex Knowledge Base" runs the full ingestion-retrieval pipeline asynchronously:
    $$\text{SourceLoader} \rightarrow \text{Chunker} \rightarrow \text{VectorStore} \rightarrow \text{KeywordSearch}$$
    This reconstructs and overwrites both semantic and keyword databases on the fly without restarting the web server process.

### Interactive Citation & Evidence Viewer
*   **URL Clickable Badges**: Ingested webpage links are parsed and rendered as rich, stylized CSS button tags. When hovered, they animate and link directly to the target external resource.
*   **Retrieved Evidence Explorer**: Provides an expandable accordion breakdown for all matching chunks. This shows the top `k` source text snippets, chunk indices, and their raw hybrid fusion scores so that researchers can trace exactly why the LLM produced a given claim.


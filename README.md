# 🔍 Research Agent

An intelligent, secure Retrieval-Augmented Generation (RAG) system designed to answer complex research questions based on curated document sources. It leverages a hybrid retrieval engine (combining dense vector embeddings and sparse keyword BM25 indexes) fused with semantic reranking and robust prompt-injection safety controls.

---

## 🛠️ Architecture & System Design

The system is structured as modular, clean packages:

```
Research Agent/
├── config/                  # Configuration & Global Settings
│   ├── settings.py          # Tuning params, prompt limits, model definitions
│   └── sources.json         # Ingestion registry (URLs & PDFs)
├── data/                    # Local storage (ChromaDB, BM25 Index, raw data)
├── src/                     # Core Source Code
│   ├── embedding/           # Vector representation & persistence
│   │   └── vector_store.py  # ChromaDB wrapper using cosine similarity & embeddings
│   ├── generation/          # Large Language Model integration
│   │   └── qa_engine.py     # Context stitching, citation matching & Groq interface
│   ├── ingestion/           # Source parsing & extraction
│   │   ├── chunker.py       # Sentence-based token-controlled sliding chunker
│   │   └── source_loader.py # BS4 HTML cleaner & PyPDF document reader
│   ├── retrieval/           # Search & Fusion algorithms
│   │   ├── keyword_search.py # Rank-BM25 Sparse search over chunks
│   │   └── hybrid_retriever.py # RRF normalizing retriever with answerability checks
│   └── utils/               # Utilities & Helpers
│       └── security.py      # PromptInjectionDetector with precompiled regex limits
├── tests/                   # Automated Pytest Suite
└── main.py                  # CLI Bootstrap Script
```

---

## 🚀 Key Features

1. **Robust Ingestion Pipeline**:
   * Extracts clean web text (cleaning navigation menus, footers, stylesheets, scripts) via BeautifulSoup.
   * Extracts local PDF contents accurately via `pypdf`.
2. **Token-Aware Sentence Chunker**:
   * Splits texts into target chunks (512 tokens) preserving sentence boundaries.
   * Employs sliding overlap (50 tokens) to preserve context boundaries without duplicate redundancy.
   * Fallback limits split extremely long blocks lacking periods (e.g. table data).
3. **Normalized Hybrid Retriever**:
   * **Dense Semantic Search**: Cosine similarity index over `all-MiniLM-L6-v2` embeddings in ChromaDB.
   * **Sparse Keyword Search**: BM25 keyword score ranking.
   * **Reciprocal Rank Fusion (RRF)**: Normalizes raw scores (0 to 1 scaling) from both pipelines and combines them using custom weights (`alpha=0.5`).
   * **Bypass/Answerability Checks**: Checks top fusion scores against a strict confidence threshold (`0.15`). If context matches are too weak, the LLM is bypassed to prevent hallucination.
4. **LLM Generation with Citation Mapping**:
   * Connects to Groq Cloud API using `llama-3.3-70b-versatile` for high-fidelity reasoning.
   * Strict prompt rules to answer strictly on context.
   * Auto-extracts citation tags mapped directly to original files/URLs (e.g. `[chess_strategy_url]`).
5. **Multi-Layer Input Security**:
   * Pre-execution prompt scanning checks for malicious attempts (e.g., bypass instructions, credential queries like Groq keys, file system commands, `/etc/passwd` requests).
   * Refuses unsafe prompts immediately without triggering unnecessary API calls.

---

## ⚙️ Installation & Setup

### Prerequisites
* Python 3.10+
* Groq API Key

### Step 1: Clone & Configure Virtual Environment
```powershell
# Create Virtual Environment
python -m venv .venv

# Activate Virtual Environment (Windows)
.venv\Scripts\Activate.ps1
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Set Environment Variables
Create a `.env` file in the root directory:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
HF_TOKEN=optional_huggingface_token
```

---

## 🏃 Running the Application

To download reference documents, build the search indexes, and launch the interactive CLI:

```powershell
python main.py
```

Example usage inside CLI:
```text
[Search] Research Agent - Ask a question (or 'quit' to exit)
[PASS] Successfully fetched: chess_guide_pdf
...
[PASS] Upserted 167 chunks into ChromaDB.
[PASS] Saved BM25 index (167 chunks) to data/bm25_index.pkl

Question: What is checkmate?

Answer:
Checkmate occurs when the opponent's king is in check, and there is no legal way to get it out of check [chess_strategy_url].

Citations: ['chess_strategy_url']
Confidence: 0.82

Question: quit
```

---

## 🧪 Running Unit Tests

We use `pytest` to run verification checks across ingestion, embedding, retriever, and security files:

```powershell
.venv\Scripts\pytest.exe
```

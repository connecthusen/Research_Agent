# app.py  –  Research Agent  |  Premium Streamlit Interface
import os
import json
import base64
import datetime
import uuid
import streamlit as st
import pandas as pd
from typing import List, Dict
from markdown_it import MarkdownIt

# ─────────────────────────────── Page config ────────────────────────────────
st.set_page_config(
    page_title="Research Agent",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ────────────────────────────── Utilities ───────────────────────────────────
md = MarkdownIt()

def get_b64(path: str) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

LOGO_B64 = get_b64("data/logo.png")
LOGO_SRC  = f"data:image/png;base64,{LOGO_B64}" if LOGO_B64 else ""

# ─────────────────────────────── Global CSS ─────────────────────────────────
st.html(f"""
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* ── Reset & Base ── */
html, body, [class*="css"], .stApp {{
    font-family: 'Inter', sans-serif !important;
    background-color: #080c14 !important;
    color: #c9d1e0 !important;
}}

/* ── Main block container width ── */
div[data-testid="stAppViewBlockContainer"],
div[data-testid="stMainBlockContainer"],
.stAppViewBlockContainer,
.block-container,
.main .block-container,
div[data-testid="stBottomBlockContainer"] {{
    max-width: 95% !important;
    width: 95% !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
}}

/* ── Sidebar ── */
[data-testid="stSidebar"][data-collapsed="false"] {{
    background: linear-gradient(180deg, #0b1120 0%, #090d1a 100%) !important;
    border-right: 1px solid #1a2540 !important;
    min-width: 280px !important;
}}

/* ── Top navigation bar ── */
header[data-testid="stHeader"] {{
    background: rgba(8, 12, 20, 0.85) !important;
    backdrop-filter: blur(12px) !important;
    border-bottom: 1px solid #1a2540 !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{ width:5px; height:5px; }}
::-webkit-scrollbar-track {{ background:#0b1120; }}
::-webkit-scrollbar-thumb {{ background:#1e2e50; border-radius:4px; }}
::-webkit-scrollbar-thumb:hover {{ background:#3b6fd4; }}

/* ── Buttons ── */
.stButton > button {{
    background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 8px 18px !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 2px 10px rgba(37,99,235,0.25) !important;
}}
.stButton > button:hover {{
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    box-shadow: 0 4px 18px rgba(59,130,246,0.4) !important;
    transform: translateY(-1px) !important;
}}

/* ── Text inputs ── */
.stTextInput > div > div > input {{
    background-color: #0f1829 !important;
    color: #c9d1e0 !important;
    border: 1px solid #1a2540 !important;
    border-radius: 8px !important;
    font-size: 0.88rem !important;
}}
.stTextInput > div > div > input:focus {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 2px rgba(37,99,235,0.2) !important;
}}

/* ── File uploader ── */
[data-testid="stFileUploader"] {{
    background-color: #0d1626 !important;
    border: 1.5px dashed #1e2e50 !important;
    border-radius: 10px !important;
    padding: 12px !important;
}}
[data-testid="stFileUploader"]:hover {{
    border-color: #2563eb !important;
}}

/* ── Code blocks ── */
pre {{
    background-color: #0a0f1e !important;
    border: 1px solid #1a2540 !important;
    border-radius: 8px !important;
    padding: 14px !important;
    color: #a8b5cc !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    overflow-x: auto !important;
}}
code {{
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.85rem !important;
    color: #7dd3fc !important;
}}

/* ── Chat containers ── */
div[data-testid="stChatMessage"] {{
    background-color: transparent !important;
    border: none !important;
    padding: 0 !important;
}}

/* ── Chat input — aggressive dark override for Streamlit 1.59 ── */
div[data-testid="stChatInput"] {{
    border: 1.5px solid #1e2e50 !important;
    border-radius: 14px !important;
    background-color: #0d1626 !important;
    box-shadow: 0 4px 24px rgba(0,0,0,0.6) !important;
    padding: 4px !important;
    transition: border-color 0.25s !important;
}}
div[data-testid="stChatInput"]:focus-within {{
    border-color: #2563eb !important;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.18), 0 4px 24px rgba(0,0,0,0.5) !important;
}}
/* Inner wrapper */
div[data-testid="stChatInput"] > div {{
    background-color: #0d1626 !important;
    border-radius: 12px !important;
}}
/* Textarea itself */
div[data-testid="stChatInput"] textarea,
div[data-testid="stChatInput"] input {{
    background-color: #0d1626 !important;
    color: #c9d1e0 !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.92rem !important;
    caret-color: #3b82f6 !important;
}}
div[data-testid="stChatInput"] textarea::placeholder {{
    color: #3b4f6b !important;
}}
/* Bottom sticky bar that wraps the input */
div[data-testid="stBottom"],
div[data-testid="stBottom"] > div,
div[data-testid="stBottomBlockContainer"] {{
    background: #080c14 !important;
    background-color: #080c14 !important;
    border-top: none !important;
    padding-top: 16px !important;
}}
/* Send button inside chat input */
div[data-testid="stChatInput"] button {{
    background: linear-gradient(135deg, #2563eb, #1d4ed8) !important;
    border-radius: 8px !important;
    border: none !important;
    color: white !important;
}}
div[data-testid="stChatInput"] button:hover {{
    background: #3b82f6 !important;
    box-shadow: 0 0 10px rgba(59,130,246,0.4) !important;
}}

/* ── Expander ── */
[data-testid="stExpander"] {{
    background-color: #0d1626 !important;
    border: 1px solid #1a2540 !important;
    border-radius: 8px !important;
}}
[data-testid="stExpander"] summary {{
    color: #7dd3fc !important;
    font-weight: 500 !important;
}}
[data-testid="stExpander"] > div {{
    background-color: #0a0f1e !important;
}}

/* ── Divider ── */
hr {{ border-color: #1a2540 !important; margin: 14px 0 !important; }}

/* ── Spinner text ── */
[data-testid="stSpinner"] p {{ color: #7dd3fc !important; }}

/* ── Warning / Info / Error boxes ── */
div[data-testid="stAlert"] {{
    background-color: #0d1626 !important;
    border-radius: 8px !important;
    font-size: 0.87rem !important;
}}

/* ── Animations ── */
@keyframes fadeSlideIn {{
    from {{ opacity: 0; transform: translateY(8px); }}
    to   {{ opacity: 1; transform: translateY(0); }}
}}
@keyframes pulse-dot {{
    0%, 100% {{ opacity: 1; }}
    50%       {{ opacity: 0.3; }}
}}

/* ── Sidebar section label ── */
.sidebar-section-label {{
    font-size: 0.68rem;
    font-weight: 700;
    color: #3b6fd4;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    margin: 16px 0 8px 0;
    padding: 0 4px;
}}

/* ── Sidebar Column Buttons (Title Buttons) ── */
[data-testid="stSidebar"] [data-testid="column"]:first-child button {{
    background: #0d1626 !important;
    border: 1px solid #1a2540 !important;
    color: #94a3b8 !important;
    text-align: left !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    border-radius: 6px !important;
    width: 100% !important;
    height: 38px !important;
    margin-top: 1px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: flex-start !important;
    padding: 0 10px !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stSidebar"] [data-testid="column"]:first-child button:hover {{
    background: #111d35 !important;
    border-color: #2563eb !important;
    color: #7dd3fc !important;
}}

/* ── Sidebar Delete Buttons (Trash Icon) ── */
[data-testid="stSidebar"] [data-testid="column"]:last-child button {{
    background: #1e1212 !important;
    border: 1px solid #4a1414 !important;
    color: #f87171 !important;
    box-shadow: none !important;
    padding: 6px 0 !important;
    border-radius: 6px !important;
    width: 100% !important;
    height: 38px !important;
    margin-top: 1px !important;
    font-size: 0.8rem !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.2s ease !important;
}}
[data-testid="stSidebar"] [data-testid="column"]:last-child button:hover {{
    background: #7f1d1d !important;
    color: #ffffff !important;
    border-color: #f87171 !important;
    box-shadow: 0 0 8px rgba(127, 29, 29, 0.4) !important;
}}
</style>
""")

# ─────────────────────────── Core module imports ────────────────────────────
from src.ingestion.source_loader import SourceLoader
from src.ingestion.chunker import Chunker
from src.embedding.vector_store import VectorStore
from src.retrieval.keyword_search import KeywordSearch
from src.retrieval.hybrid_retriever import HybridRetriever
from src.generation.qa_engine import QAEngine
from config.settings import TOP_K_CHUNKS, NO_ANSWER_MESSAGE

# ────────────────────────── Path constants ──────────────────────────────────
CONFIG_PATH = "config/sources.json"
PDF_DIR     = "data/pdfs"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs("data", exist_ok=True)

# ──────────────────────── Sources.json helpers ───────────────────────────────
def load_sources() -> List[Dict]:
    if not os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "w") as f:
            json.dump({"sources": []}, f, indent=2)
    with open(CONFIG_PATH, "r") as f:
        try:
            return json.load(f).get("sources", [])
        except json.JSONDecodeError:
            return []

def save_sources(sources: List[Dict]):
    with open(CONFIG_PATH, "w") as f:
        json.dump({"sources": sources}, f, indent=2)

def get_source_label_mapping() -> Dict[str, str]:
    mapping = {}
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                data = json.load(f)
                for src in data.get("sources", []):
                    src_id = src.get("id")
                    src_type = src.get("type")
                    src_value = src.get("value")
                    if src_id and src_value:
                        if src_type == "pdf":
                            mapping[src_id] = os.path.basename(src_value)
                        else:
                            mapping[src_id] = src_value
        except Exception:
            pass
    return mapping

def safe_id(name: str) -> str:
    c = name.replace(" ", "_").replace("-", "_").lower()
    return "".join(ch for ch in c if ch.isalnum() or ch == "_")

sources = load_sources()

# ──────────────────────── Session History Helpers ─────────────────────────────
def init_sessions():
    if "sessions" not in st.session_state or not st.session_state["sessions"]:
        new_id = str(uuid.uuid4())
        st.session_state["sessions"] = [{
            "id": new_id,
            "title": "New Session",
            "messages": []
        }]
        st.session_state["active_session_id"] = new_id
    elif "active_session_id" not in st.session_state:
        st.session_state["active_session_id"] = st.session_state["sessions"][0]["id"]

def get_active_session() -> Dict:
    init_sessions()
    active_id = st.session_state["active_session_id"]
    for sess in st.session_state["sessions"]:
        if sess["id"] == active_id:
            return sess
    return st.session_state["sessions"][0]

# ─────────────────────────── Chat renderers ─────────────────────────────────

def confidence_color(score: float) -> str:
    if score >= 0.7:
        return "#22d3a8"
    elif score >= 0.4:
        return "#f59e0b"
    return "#f87171"

def confidence_label(score: float) -> str:
    if score >= 0.7:
        return "High"
    elif score >= 0.4:
        return "Medium"
    return "Low"

def render_user_message(content: str):
    html_body = md.render(content)
    st.markdown(f"""
    <div style="display:flex; justify-content:flex-end; margin:16px 0; align-items:flex-start; animation:fadeSlideIn 0.35s ease-out;">
        <div style="
            background: linear-gradient(135deg, #1d4ed8 0%, #2563eb 100%);
            color:#ffffff;
            padding:12px 18px;
            border-radius:16px 16px 4px 16px;
            max-width:68%;
            box-shadow:0 4px 18px rgba(37,99,235,0.25);
            font-size:0.9rem;
            line-height:1.55;
        ">{html_body}</div>
        <div style="
            margin-left:10px;
            background:linear-gradient(135deg,#2563eb,#1d4ed8);
            color:#fff;
            width:34px; height:34px;
            border-radius:50%;
            display:flex; align-items:center; justify-content:center;
            font-weight:700; font-size:0.85rem;
            border:2px solid #3b82f6;
            box-shadow:0 2px 10px rgba(37,99,235,0.3);
            flex-shrink:0;
        ">U</div>
    </div>
    """, unsafe_allow_html=True)


def render_assistant_message(content: str, metadata: dict = None):
    html_body = md.render(content)

    meta_html = ""
    if metadata:
        conf       = metadata.get("confidence", 0.0)
        cits       = metadata.get("citations", [])
        restricted = metadata.get("restricted", False)

        c_color = confidence_color(conf)
        c_label = confidence_label(conf)

        if cits:
            # Deduplicate citations while preserving order
            unique_cits = list(dict.fromkeys(cits))
            
            badges_list = []
            for c in unique_cits:
                if c.startswith(("http://", "https://")):
                    # Extract a clean, friendly label from the URL
                    parts = c.rstrip("/").split("/")
                    label = parts[-1].replace("_", " ").replace("-", " ")
                    if not label or label.startswith("www."):
                        label = parts[-2]
                    label = f"🌐 {label}"
                    
                    badges_list.append(
                        f"<a href='{c}' target='_blank' style='display:inline-block; background:#111d35; color:#7dd3fc; "
                        f"border:1px solid #1e3a6e; border-radius:5px; padding:3px 9px; margin:2px; "
                        f"font-size:0.75rem; font-weight:600; text-decoration:none; transition:all 0.2s;' "
                        f"onmouseover='this.style.background=\"#1e3a6e\"; this.style.borderColor=\"#3b82f6\";' "
                        f"onmouseout='this.style.background=\"#111d35\"; this.style.borderColor=\"#1e3a6e\";'>"
                        f"{label}</a>"
                    )
                else:
                    label = f"📄 {c}"
                    badges_list.append(
                        f"<span style='display:inline-block; background:#111d35; color:#7dd3fc; "
                        f"border:1px solid #1e3a6e; border-radius:5px; padding:3px 9px; margin:2px; "
                        f"font-size:0.75rem; font-weight:600; cursor:default;'>"
                        f"{label}</span>"
                    )
            badges = "".join(badges_list)
        else:
            badges = "<span style='color:#6b7280;font-size:0.8rem;font-style:italic;'>No citations</span>"

        if restricted:
            status_txt = "Blocked"
            status_col = "#f87171"
        elif content == NO_ANSWER_MESSAGE:
            status_txt = "No Answer"
            status_col = "#f59e0b"
        else:
            status_txt = "Verified"
            status_col = "#22d3a8"

        meta_html = f"""<div style="margin-top:14px; border-top:1px solid #1a2540; padding-top:12px; display:grid; grid-template-columns:1fr 2fr 1fr; gap:10px;">
<div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:8px;padding:10px 8px;text-align:center;">
<div style="font-size:0.67rem;color:#4b5a75;text-transform:uppercase;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">Confidence</div>
<div style="font-size:1.25rem;font-weight:800;color:{c_color};">{conf:.2f}</div>
<div style="font-size:0.68rem;color:{c_color};font-weight:600;">{c_label}</div>
</div>
<div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:8px;padding:10px 8px;text-align:center;">
<div style="font-size:0.67rem;color:#4b5a75;text-transform:uppercase;font-weight:700;letter-spacing:0.8px;margin-bottom:6px;">Source Citations</div>
<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:2px;">{badges}</div>
</div>
<div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:8px;padding:10px 8px;text-align:center;">
<div style="font-size:0.67rem;color:#4b5a75;text-transform:uppercase;font-weight:700;letter-spacing:0.8px;margin-bottom:4px;">Status</div>
<div style="font-size:0.88rem;font-weight:700;color:{status_col};">{status_txt}</div>
</div>
</div>"""

    logo_html = (
        f'<img src="{LOGO_SRC}" style="width:34px;height:34px;border-radius:50%;'
        f'margin-right:10px;border:2px solid #1e3a6e;background:#0a0f1e;'
        f'object-fit:cover;flex-shrink:0;" />'
        if LOGO_SRC else
        '<div style="width:34px;height:34px;border-radius:50%;margin-right:10px;'
        'background:linear-gradient(135deg,#1e3a6e,#2563eb);display:flex;align-items:center;'
        'justify-content:center;color:#fff;font-weight:700;font-size:0.8rem;flex-shrink:0;">R</div>'
    )

    st.markdown(f"""<div style="display:flex;margin:16px 0;align-items:flex-start;animation:fadeSlideIn 0.35s ease-out;">
{logo_html}
<div style="background:#0d1626; border:1px solid #1a2540; border-left:3px solid #2563eb; border-radius:4px 14px 14px 14px; padding:16px 18px; max-width:82%; box-shadow:0 4px 24px rgba(0,0,0,0.3);">
<div style="font-size:0.9rem;line-height:1.65;color:#c9d1e0;">{html_body}</div>
{meta_html}
</div>
</div>""", unsafe_allow_html=True)

    # Evidence chunk viewer
    if metadata and metadata.get("chunks") and not metadata.get("restricted") and content != NO_ANSWER_MESSAGE:
        with st.expander("🔬 Retrieved Evidence Chunks"):
            src_mapping = get_source_label_mapping()
            for idx, chunk in enumerate(metadata["chunks"]):
                score_color = confidence_color(chunk.get("score", 0))
                clean_name = src_mapping.get(chunk['source_id'], chunk['source_id'])
                if clean_name.startswith(("http://", "https://")):
                    parts = clean_name.rstrip("/").split("/")
                    display_name = parts[-1].replace("_", " ").replace("-", " ")
                    if not display_name or display_name.startswith("www."):
                        display_name = parts[-2]
                    display_name = f"🌐 {display_name}"
                else:
                    display_name = f"📄 {clean_name}"
                
                # Make header clickable if source is a URL
                source_html = f"<span style='color:#7dd3fc;'>{display_name}</span>"
                if clean_name.startswith(("http://", "https://")):
                    source_html = f"<a href='{clean_name}' target='_blank' style='color:#7dd3fc; text-decoration:none; font-weight:600;'>{display_name}</a>"

                st.markdown(f"""<div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:8px;padding:12px;margin-bottom:10px;">
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px;">
<span style="font-family:'JetBrains Mono',monospace;font-size:0.8rem;font-weight:600;">{source_html} &middot; Chunk #{chunk['chunk_index']}</span>
<span style="background:#111d35;border:1px solid #1e3a6e;border-radius:4px;padding:2px 8px;font-size:0.75rem;font-weight:700;color:{score_color};">Score: {chunk['score']:.4f}</span>
</div>
<div style="font-size:0.82rem;color:#8a9bb5;line-height:1.55;border-top:1px solid #1a2540;padding-top:8px;">{chunk['text'][:400]}{'...' if len(chunk['text']) > 400 else ''}</div>
</div>""", unsafe_allow_html=True)

# ══════════════════════════════ SIDEBAR ═════════════════════════════════════
with st.sidebar:
    # ── Brand header ──
    logo_icon = f"<img src='{LOGO_SRC}' style='width:28px;height:28px;border-radius:6px;object-fit:cover;'/>" if LOGO_SRC else "🔬"
    st.markdown(f"""
    <div style="padding:20px 20px 10px 20px;">
        <div style="display:flex;align-items:center;gap:12px;margin-bottom:6px;">
            <div style="background:linear-gradient(135deg,#1e3a6e 0%,#2563eb 100%);
                        border-radius:10px;padding:7px;
                        box-shadow:0 4px 14px rgba(37,99,235,0.35);">
                {logo_icon}
            </div>
            <div>
                <div style="font-size:1.1rem;font-weight:800;color:#ffffff;line-height:1.1;
                    background:linear-gradient(135deg,#7dd3fc 0%,#3b82f6 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                    Research Agent
                </div>
                <div style="font-size:0.62rem;color:#3b6fd4;font-weight:600;letter-spacing:1px;text-transform:uppercase;">
                    RAG &middot; Citation Engine
                </div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:6px;margin-top:10px;">
            <div style="width:7px;height:7px;border-radius:50%;background:#22d3a8;
                box-shadow:0 0 6px rgba(34,211,168,0.6);animation:pulse-dot 2s infinite;"></div>
            <span style="font-size:0.72rem;color:#22d3a8;font-weight:600;">Engine Active</span>
        </div>
    </div>
    <hr style="margin:10px 0;border-color:#1a2540;">
    """, unsafe_allow_html=True)

    if st.button("＋  New Session", use_container_width=True):
        new_id = str(uuid.uuid4())
        st.session_state["sessions"].insert(0, {
            "id": new_id,
            "title": "New Session",
            "messages": []
        })
        st.session_state["active_session_id"] = new_id
        st.rerun()

    # ── Session history ──
    st.markdown("<div class='sidebar-section-label'>Session History</div>", unsafe_allow_html=True)
    init_sessions()
    active_id = st.session_state["active_session_id"]
    sessions = st.session_state["sessions"]

    if sessions:
        for idx, sess in enumerate(sessions):
            col1, col2 = st.columns([0.82, 0.18], gap="small")
            is_active = (sess["id"] == active_id)
            title = sess["title"]
            label = f"▶ {title}" if is_active else f"💬 {title}"
            with col1:
                if st.button(label, key=f"sess_title_{sess['id']}_{idx}", use_container_width=True):
                    st.session_state["active_session_id"] = sess["id"]
                    st.rerun()
            with col2:
                if st.button("🗑️", key=f"del_sess_{sess['id']}_{idx}", use_container_width=True):
                    sessions.pop(idx)
                    if not sessions:
                        new_id = str(uuid.uuid4())
                        st.session_state["sessions"] = [{
                            "id": new_id,
                            "title": "New Session",
                            "messages": []
                        }]
                        st.session_state["active_session_id"] = new_id
                    elif active_id == sess["id"]:
                        st.session_state["active_session_id"] = st.session_state["sessions"][0]["id"]
                    st.rerun()
    else:
        st.markdown("<div style='font-size:0.76rem;color:#374151;padding:6px 4px;font-style:italic;'>No chat sessions</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:12px 0;border-color:#1a2540;'>", unsafe_allow_html=True)

    # ── Knowledge Base Manager ──
    st.markdown("<div class='sidebar-section-label'>Knowledge Base</div>", unsafe_allow_html=True)

    with st.expander("📄 Add PDF Document"):
        uploaded_file = st.file_uploader("Browse PDF", type=["pdf"], label_visibility="collapsed")
        if uploaded_file is not None:
            file_path = os.path.join(PDF_DIR, uploaded_file.name)
            if not os.path.exists(file_path):
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                src_id = f"{safe_id(os.path.splitext(uploaded_file.name)[0])}_pdf"
                if not any(s["id"] == src_id for s in sources):
                    sources.append({"id": src_id, "type": "pdf", "value": f"data/pdfs/{uploaded_file.name}"})
                    save_sources(sources)
                    st.success(f"Added: {uploaded_file.name}")
                    st.rerun()
            else:
                st.info("Already in knowledge base.")

    with st.expander("🔗 Add URL Source"):
        url_input = st.text_input("Enter URL", placeholder="https://en.wikipedia.org/wiki/...", label_visibility="collapsed")
        if st.button("Register URL", use_container_width=True):
            url = url_input.strip()
            if url:
                domain = url.split("//")[-1].split("/")[0]
                page   = url.rstrip("/").split("/")[-1] or "page"
                src_id = f"{safe_id(domain + '_' + page)}_url"
                if not any(s["value"] == url for s in sources):
                    sources.append({"id": src_id, "type": "url", "value": url})
                    save_sources(sources)
                    st.success("URL registered!")
                    st.rerun()
                else:
                    st.warning("URL already in knowledge base.")
            else:
                st.error("Enter a valid URL.")

    with st.expander(f"📂 Sources  ({len(sources)})"):
        if sources:
            for idx, src in enumerate(sources):
                icon = "📄" if src["type"] == "pdf" else "🌐"
                col1, col2 = st.columns([0.8, 0.2], gap="small")
                with col1:
                    st.markdown(f"""
                    <div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:6px;
                                padding:7px 10px;margin-bottom:4px;font-size:0.78rem;overflow:hidden;text-overflow:ellipsis;">
                        <span style="margin-right:6px;">{icon}</span>
                        <span style="color:#7dd3fc;font-weight:600;">{src['id']}</span>
                        <div style="color:#4b5a75;margin-top:2px;font-size:0.7rem;overflow:hidden;
                                    white-space:nowrap;text-overflow:ellipsis;">{src['value']}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    if st.button("🗑️", key=f"del_{src['id']}_{idx}", use_container_width=True):
                        if src["type"] == "pdf":
                            file_path = src["value"]
                            if os.path.exists(file_path):
                                try:
                                    os.remove(file_path)
                                except Exception as e:
                                    st.error(f"Error removing file: {e}")
                        sources.pop(idx)
                        save_sources(sources)
                        st.success(f"Deleted: {src['id']}")
                        st.rerun()
            if st.button("Clear All Sources", use_container_width=True):
                save_sources([])
                sources.clear()
                st.success("Cleared.")
                st.rerun()
        else:
            st.markdown("<div style='font-size:0.78rem;color:#374151;font-style:italic;padding:4px;'>No sources registered</div>", unsafe_allow_html=True)

    st.markdown("<hr style='margin:12px 0;border-color:#1a2540;'>", unsafe_allow_html=True)

    if st.button("⚡  Build / Reindex Knowledge Base", use_container_width=True):
        with st.spinner("Indexing sources — please wait…"):
            try:
                loader = SourceLoader(config_path=CONFIG_PATH)
                fetched, failures = loader.fetch_all()
                if failures:
                    st.warning(f"{len(failures)} source(s) failed to load.")
                chunker  = Chunker()
                chunks   = chunker.chunk_sources(fetched)
                vs       = VectorStore();  vs.clear();  vs.add_chunks(chunks)
                ks       = KeywordSearch(); ks.build(chunks); ks.save()
                retriever = HybridRetriever(vs, ks)
                st.session_state["retriever"]   = retriever
                st.session_state["qa_engine"]   = QAEngine(retriever)
                st.session_state["initialized"] = True
                st.session_state["indexed_at"]  = datetime.datetime.now().strftime("%H:%M:%S")
                st.session_state["chunk_count"] = len(chunks)
                st.success(f"Indexed {len(chunks)} chunks from {len(fetched)} sources")
                st.rerun()
            except Exception as e:
                st.error(f"Indexing failed: {e}")

    # Engine status panel
    if st.session_state.get("initialized"):
        indexed_at  = st.session_state.get("indexed_at", "–")
        chunk_count = st.session_state.get("chunk_count", "–")
        st.markdown(f"""
        <div style="background:#0a0f1e;border:1px solid #1a2540;border-radius:8px;padding:10px 12px;margin-top:4px;">
            <div style="font-size:0.67rem;color:#3b6fd4;font-weight:700;text-transform:uppercase;letter-spacing:0.8px;margin-bottom:6px;">Engine Status</div>
            <div style="display:flex;justify-content:space-between;align-items:center;">
                <span style="font-size:0.75rem;color:#7dd3fc;">Hybrid RAG</span>
                <span style="font-size:0.72rem;color:#22d3a8;font-weight:700;">Ready</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:3px;">
                <span style="font-size:0.75rem;color:#4b5a75;">Last indexed</span>
                <span style="font-size:0.72rem;color:#94a3b8;">{indexed_at}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:3px;">
                <span style="font-size:0.75rem;color:#4b5a75;">Chunks</span>
                <span style="font-size:0.72rem;color:#94a3b8;">{chunk_count}</span>
            </div>
            <div style="display:flex;justify-content:space-between;align-items:center;margin-top:3px;">
                <span style="font-size:0.75rem;color:#4b5a75;">Sources</span>
                <span style="font-size:0.72rem;color:#94a3b8;">{len(sources)}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # User info at bottom
    st.markdown(f"""
    <div style="margin-top:20px;">
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:10px;padding:10px 12px;
                    display:flex;align-items:center;gap:10px;">
            <div style="background:linear-gradient(135deg,#1e3a6e,#2563eb);color:#fff;
                        width:32px;height:32px;border-radius:8px;display:flex;
                        align-items:center;justify-content:center;font-weight:800;
                        font-size:0.85rem;flex-shrink:0;">U</div>
            <div>
                <div style="font-size:0.82rem;color:#e2e8f0;font-weight:600;">Researcher</div>
                <div style="font-size:0.7rem;color:#3b6fd4;font-weight:500;">LLaMA 3.3 70B &middot; Groq</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════ MAIN AREA ═══════════════════════════════════

# ── Page header ──
logo_tag = f"<img src='{LOGO_SRC}' style='width:42px;height:42px;border-radius:10px;border:2px solid #1e3a6e;object-fit:cover;box-shadow:0 4px 14px rgba(37,99,235,0.3);'/>" if LOGO_SRC else ""
st.markdown(f"""
<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;">
    <div style="display:flex;align-items:center;gap:14px;">
        {logo_tag}
        <div>
            <h1 style="font-size:1.6rem;font-weight:800;color:#ffffff;margin:0;line-height:1.1;
                background:linear-gradient(135deg,#7dd3fc 0%,#3b82f6 55%,#6366f1 100%);
                -webkit-background-clip:text;-webkit-text-fill-color:transparent;">
                Research Agent
            </h1>
            <div style="font-size:0.72rem;color:#3b6fd4;font-weight:600;letter-spacing:0.9px;
                        text-transform:uppercase;margin-top:2px;">
                Intelligent &middot; Cited &middot; Source-Grounded Answers
            </div>
        </div>
    </div>
    <div style="display:flex;gap:8px;align-items:center;">
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:8px;padding:6px 14px;
                    font-size:0.75rem;font-weight:600;color:#7dd3fc;">
            LLaMA 3.3 70B
        </div>
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:8px;padding:6px 14px;
                    font-size:0.75rem;font-weight:600;color:#22d3a8;">
            Hybrid RAG
        </div>
    </div>
</div>
<div style="background:linear-gradient(90deg,#1e3a6e 0%,#1a2540 60%,transparent 100%);
            height:2px;border-radius:2px;margin-bottom:22px;"></div>
""", unsafe_allow_html=True)

active_session = get_active_session()
active_messages = active_session["messages"]

# ── Capability cards (shown only on empty active session) ──
if not active_messages:
    st.markdown("""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:26px;">
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:10px;padding:16px;">
            <div style="font-size:1.2rem;margin-bottom:8px;">📖</div>
            <div style="font-size:0.82rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">Document QA</div>
            <div style="font-size:0.73rem;color:#4b5a75;line-height:1.45;">Answer questions grounded in your uploaded PDFs and web pages</div>
        </div>
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:10px;padding:16px;">
            <div style="font-size:1.2rem;margin-bottom:8px;">🔗</div>
            <div style="font-size:0.82rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">Source Citations</div>
            <div style="font-size:0.73rem;color:#4b5a75;line-height:1.45;">Every claim is backed by an exact reference from your knowledge base</div>
        </div>
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:10px;padding:16px;">
            <div style="font-size:1.2rem;margin-bottom:8px;">🔀</div>
            <div style="font-size:0.82rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">Hybrid Retrieval</div>
            <div style="font-size:0.73rem;color:#4b5a75;line-height:1.45;">BM25 keyword + semantic vector search fused via Reciprocal Rank Fusion</div>
        </div>
        <div style="background:#0d1626;border:1px solid #1a2540;border-radius:10px;padding:16px;">
            <div style="font-size:1.2rem;margin-bottom:8px;">🛡</div>
            <div style="font-size:0.82rem;font-weight:700;color:#e2e8f0;margin-bottom:4px;">Prompt Guard</div>
            <div style="font-size:0.73rem;color:#4b5a75;line-height:1.45;">Injection detection automatically blocks adversarial system-probing queries</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ── RAG Engine auto-load ──
if "initialized" not in st.session_state:
    try:
        if os.path.exists("data/bm25_index.pkl") and os.path.exists("data/chroma_db"):
            vs  = VectorStore()
            ks  = KeywordSearch()
            if ks.load():
                ret = HybridRetriever(vs, ks)
                st.session_state["retriever"]   = ret
                st.session_state["qa_engine"]   = QAEngine(ret)
                st.session_state["initialized"] = True
            else:
                st.session_state["initialized"] = False
        else:
            st.session_state["initialized"] = False
    except Exception:
        st.session_state["initialized"] = False

# ── Not-indexed notice ──
if not st.session_state.get("initialized", False):
    st.markdown("""
    <div style="background:#0d1626;border:1px solid #2563eb;border-left:4px solid #2563eb;
                border-radius:10px;padding:18px 20px;margin-bottom:20px;">
        <div style="font-size:0.92rem;font-weight:700;color:#7dd3fc;margin-bottom:6px;">
            Knowledge Base Not Indexed
        </div>
        <div style="font-size:0.83rem;color:#4b5a75;line-height:1.55;">
            Add PDF documents or URLs using the <strong style="color:#94a3b8;">Knowledge Base</strong>
            panel in the sidebar, then click
            <strong style="color:#7dd3fc;">Build / Reindex Knowledge Base</strong> to activate the Research Agent.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# ── Session messages ──
for msg in active_messages:
    if msg["role"] == "user":
        render_user_message(msg["content"])
    else:
        render_assistant_message(msg["content"], msg.get("metadata"))

# ── Chat input ──
if question := st.chat_input("Ask a research question…"):
    if active_session["title"] == "New Session":
        short_title = question[:28] + ("…" if len(question) > 28 else "")
        active_session["title"] = short_title

    render_user_message(question)
    active_messages.append({"role": "user", "content": question})

    qa_engine = st.session_state["qa_engine"]
    retriever = st.session_state["retriever"]
    is_safe   = qa_engine.security_detector.is_safe(question)

    if not is_safe:
        answer = qa_engine.security_detector.get_restricted_response()
        st.markdown("""
        <div style="background:#1a0d0d;border:1px solid #7f1d1d;border-radius:8px;
                    padding:12px 16px;margin-bottom:8px;font-size:0.85rem;color:#fca5a5;">
            <strong>Security Alert</strong> — Prompt injection or restricted pattern detected. Query blocked.
        </div>
        """, unsafe_allow_html=True)
        meta = {"answer": answer, "citations": [], "confidence": 0.0, "restricted": True, "chunks": []}
    else:
        with st.spinner("Retrieving evidence & generating cited answer…"):
            result          = qa_engine.answer_question(question, k=TOP_K_CHUNKS)
            answer          = result["answer"]
            retrieved_chunks = retriever.retrieve(question, k=TOP_K_CHUNKS)
            meta = {
                "answer":     answer,
                "citations":  result["citations"],
                "confidence": result["confidence"],
                "restricted": False,
                "chunks":     retrieved_chunks,
            }

    render_assistant_message(answer, meta)
    active_messages.append({"role": "assistant", "content": answer, "metadata": meta})
    st.rerun()

# ── Footer ──
st.markdown("""
<div style="text-align:center;color:#1e2e50;font-size:0.7rem;padding:16px;margin-top:20px;">
    Research Agent &middot; Answers are grounded in provided sources only
</div>
""", unsafe_allow_html=True)

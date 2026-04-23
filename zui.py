import streamlit as st
import os
import pandas as pd
from datetime import datetime
import warnings
import requests

warnings.filterwarnings("ignore", message="Accessing `__path__` from .*")

# ============================================================
# API CONFIG
# ============================================================
API_URL = "http://20.189.119.41:8000"
DOCS_DIR = "/tmp/smartfiles_uploads"
LOGS_DIR  = ""
API_PERFORMANCE_CSV = ""
os.makedirs(DOCS_DIR, exist_ok=True)

# ============================================================
# API WRAPPERS  (replace all direct service calls)
# ============================================================
def bot(query: str) -> str:
    r = requests.post(f"{API_URL}/query", json={"query": query}, timeout=120)
    r.raise_for_status()
    return r.json().get("response", "No response from agent.")

def get_all_files_from_db() -> list:
    r = requests.get(f"{API_URL}/files", timeout=15)
    r.raise_for_status()
    return r.json().get("data", [])

def upload_file_bytes(file_name: str, file_bytes: bytes) -> dict:
    r = requests.post(
        f"{API_URL}/upload-file",
        files={"file": (file_name, file_bytes)},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()

def process_link_api(url: str) -> dict:
    r = requests.post(f"{API_URL}/upload", json={"path": url}, timeout=60)
    r.raise_for_status()
    return r.json()




# ============================================================
# PAGE CONFIG
# ============================================================
st.set_page_config(
    page_title="SmartFiles AI",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# GLOBAL CSS
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Mono:wght@300;400;500&family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&display=swap');

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    color: #e8e6e1;
}

.stApp {
    background: #0d0d0f;
    background-image:
        radial-gradient(ellipse 80% 60% at 20% 0%, rgba(99,69,255,0.13) 0%, transparent 60%),
        radial-gradient(ellipse 60% 50% at 80% 100%, rgba(0,210,170,0.08) 0%, transparent 55%);
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }

/* ── Typography ── */
h1, h2, h3, h4 {
    font-family: 'Syne', sans-serif;
    letter-spacing: -0.02em;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: #111115 !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] .stMarkdown p { color: #9996a8; font-size: 0.82rem; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0;
    background: #111115;
    border-radius: 12px;
    padding: 4px;
    border: 1px solid rgba(255,255,255,0.06);
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 10px 24px;
    font-family: 'Syne', sans-serif;
    font-size: 0.82rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #6b6878;
    background: transparent;
    border: none;
    transition: all 0.2s ease;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #6345ff 0%, #4f8eff 100%) !important;
    color: white !important;
    box-shadow: 0 2px 12px rgba(99,69,255,0.35);
}

/* ── Buttons ── */
.stButton > button {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.8rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
    background: rgba(255,255,255,0.04);
    color: #e8e6e1;
    padding: 10px 20px;
    transition: all 0.2s ease;
}
.stButton > button:hover {
    background: rgba(99,69,255,0.2);
    border-color: rgba(99,69,255,0.5);
    color: white;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6345ff 0%, #4f8eff 100%);
    border: none;
    color: white;
    box-shadow: 0 4px 15px rgba(99,69,255,0.4);
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(99,69,255,0.6);
    transform: translateY(-1px);
}

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #18181e !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e8e6e1 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.9rem !important;
    transition: border-color 0.2s ease;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(99,69,255,0.5) !important;
    box-shadow: 0 0 0 3px rgba(99,69,255,0.1) !important;
}

/* ── Select box ── */
.stSelectbox > div > div {
    background: #18181e !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 10px !important;
    color: #e8e6e1 !important;
}

/* ── Metrics ── */
[data-testid="stMetric"] {
    background: #18181e;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px;
    padding: 16px 20px;
}
[data-testid="stMetricLabel"] { color: #6b6878 !important; font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.1em; }
[data-testid="stMetricValue"] { font-family: 'Syne', sans-serif; color: #e8e6e1 !important; }

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #18181e;
    border: 1px dashed rgba(255,255,255,0.12);
    border-radius: 12px;
    padding: 12px;
}

/* ── Containers / borders ── */
[data-testid="stContainer"] {
    border-color: rgba(255,255,255,0.06) !important;
    background: #16161c !important;
    border-radius: 14px !important;
}

/* ── Expander ── */
.streamlit-expanderHeader {
    background: #18181e !important;
    border-radius: 8px !important;
    color: #9996a8 !important;
    font-family: 'DM Mono', monospace !important;
    font-size: 0.8rem !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 10px !important;
}

/* ── Caption ── */
.stCaption { color: #6b6878 !important; font-size: 0.78rem !important; }

/* ── Spinner ── */
.stSpinner > div { border-top-color: #6345ff !important; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(99,69,255,0.3); border-radius: 4px; }

/* ── Custom classes ── */
.page-header {
    padding: 32px 0 20px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    margin-bottom: 28px;
}
.page-header h1 {
    font-family: 'Syne', sans-serif;
    font-size: 2rem;
    font-weight: 800;
    margin: 0 0 6px;
    background: linear-gradient(90deg, #fff 0%, #a89fff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}
.page-header p { color: #6b6878; font-size: 0.88rem; margin: 0; }

.agent-mode-card {
    background: #18181e;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
    text-align: center;
    height: 100%;
}
.agent-mode-card:hover {
    border-color: rgba(99,69,255,0.4);
    background: rgba(99,69,255,0.08);
}
.agent-mode-card.active {
    border-color: #6345ff;
    background: rgba(99,69,255,0.12);
    box-shadow: 0 0 0 1px rgba(99,69,255,0.3);
}
.agent-mode-card .icon { font-size: 2rem; margin-bottom: 10px; }
.agent-mode-card .title {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 0.9rem;
    color: #e8e6e1;
    margin-bottom: 6px;
}
.agent-mode-card .desc { font-size: 0.75rem; color: #6b6878; line-height: 1.5; }

.response-bubble {
    background: #18181e;
    border: 1px solid rgba(255,255,255,0.06);
    border-left: 3px solid #6345ff;
    border-radius: 14px;
    padding: 24px;
    margin: 16px 0;
}
.response-bubble .q-label {
    font-family: 'DM Mono', monospace;
    font-size: 1.2rem;
    color: #6345ff;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.response-bubble .q-text {
    font-weight: 500;
    font-size: 1.5rem;
    color: #c8c5d8;
    margin-bottom: 16px;
    line-height: 1.6;
}
.response-bubble .a-label {
    font-family: 'DM Mono', monospace;
    font-size: 1.2rem;
    color: #00d2aa;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    margin-bottom: 8px;
}
.response-bubble .a-text {
    font-size: 1.5rem;
    color: #e8e6e1;
    line-height: 1.75;
}
.response-bubble .meta {
    margin-top: 14px;
    padding-top: 14px;
    border-top: 1px solid rgba(255,255,255,0.06);
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #4d4b5a;
}

.sample-chip {
    display: inline-block;
    background: #1e1e26;
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 20px;
    padding: 7px 16px;
    font-size: 0.8rem;
    color: #9996a8;
    margin: 4px 4px 4px 0;
    cursor: pointer;
    transition: all 0.2s;
    font-family: 'DM Sans', sans-serif;
}
.sample-chip:hover {
    border-color: rgba(99,69,255,0.4);
    color: #c8c5d8;
    background: rgba(99,69,255,0.08);
}

.history-item {
    background: #16161c;
    border: 1px solid rgba(255,255,255,0.05);
    border-radius: 10px;
    padding: 14px 18px;
    margin-bottom: 8px;
}
.history-item .h-time {
    font-family: 'DM Mono', monospace;
    font-size: 0.68rem;
    color: #4d4b5a;
    margin-bottom: 6px;
}
.history-item .h-q { font-size: 0.82rem; color: #9996a8; margin-bottom: 4px; }
.history-item .h-a { font-size: 0.85rem; color: #c8c5d8; line-height: 1.6; }

.file-card {
    background: #16161c;
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 14px;
    padding: 20px;
    transition: border-color 0.2s;
}
.file-card:hover { border-color: rgba(255,255,255,0.12); }
.file-card .fc-name {
    font-family: 'Syne', sans-serif;
    font-weight: 700;
    font-size: 1rem;
    color: #e8e6e1;
    margin-bottom: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.file-card .fc-badge {
    display: inline-block;
    border-radius: 6px;
    padding: 2px 10px;
    font-size: 0.68rem;
    font-family: 'DM Mono', monospace;
    font-weight: 500;
    margin-right: 6px;
    margin-bottom: 6px;
    color: white;
}
.file-card .fc-meta {
    font-size: 0.75rem;
    color: #6b6878;
    font-family: 'DM Mono', monospace;
    margin-top: 8px;
}

.upload-zone {
    background: #18181e;
    border: 1px dashed rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 32px 24px;
    text-align: center;
}
.upload-zone h3 {
    font-family: 'Syne', sans-serif;
    font-size: 1rem;
    color: #e8e6e1;
    margin-bottom: 6px;
}
.upload-zone p { font-size: 0.8rem; color: #6b6878; margin: 0 0 20px; }

.sidebar-logo {
    font-family: 'Syne', sans-serif;
    font-weight: 800;
    font-size: 1.3rem;
    background: linear-gradient(90deg, #fff 0%, #a89fff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: -0.03em;
    margin-bottom: 4px;
}
.sidebar-tagline { font-size: 0.72rem; color: #4d4b5a; font-family: 'DM Mono', monospace; }

.status-dot {
    display: inline-block;
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #00d2aa;
    margin-right: 6px;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

.mode-indicator {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(99,69,255,0.12);
    border: 1px solid rgba(99,69,255,0.25);
    border-radius: 20px;
    padding: 5px 14px;
    font-family: 'DM Mono', monospace;
    font-size: 0.72rem;
    color: #a89fff;
    margin-bottom: 20px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# HELPERS
# ============================================================
def run_service(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        return None, str(e)

PLATFORM_META = {
    "aws":   {"label": "AWS S3",       "color": "#FF9900"},
    "drive": {"label": "Google Drive", "color": "#34A853"},
    "azure": {"label": "Azure Blob",   "color": "#0078D4"},
    "gcp":   {"label": "GCP Storage",  "color": "#4285F4"},
    "local": {"label": "Local",        "color": "#6345ff"},
    "mongo": {"label": "MongoDB",      "color": "#4DB33D"},
}

AGENT_MODES = [
    {
        "id": "semantic",
        "icon": "🔍",
        "title": "Semantic Search",
        "desc": "Find documents by meaning, not just keywords. ",
        "placeholder": "e.g. Find research papers about transformer attention mechanisms",
        "samples": [
            "Find me research paper on h2ogpt",
            "Find me document on stock watchlist assistant",
            "Find me a dataset for sales",
            "Find me resume of jainil patel",
        ],
    },
    {
        "id": "rag",
        "icon": "📖",
        "title": "Document Q&A",
        "desc": "Ask questions and get answers grounded in your uploaded documents using RAG.",
        "placeholder": "e.g. Why was my leave application rejected?",
        "samples": [
            "Why was my leave application rejected?",
            "What is tech stack of ai sales analyst?",
            "What are kpis of stock watchlist assistant?",
            "How many sick leaves do i get?",
        ],
    },
    {
        "id": "sql",
        "icon": "🗄️",
        "title": "Text → SQL",
        "desc": "Convert plain English into SQL queries. Works with structured CSV/database files.",
        "placeholder": "e.g. Find patients older than 50 with blood group A+ admitted under Emergency",
        "samples": [
            "Find patients older than 50 with blood group A+ admitted under Emergency",
            "Show top 10 sales records from last quarter sorted by revenue",
            "List all employees in the Engineering department hired after 2022",
            "Count the number of transactions above $5000 per month",
        ],
    },
]

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.markdown('<div class="sidebar-logo">⬡ SmartFiles</div>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-tagline">AI-Powered Document Intelligence</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown("""
    <div style="background:#1e1e26;border-radius:10px;padding:14px 16px;margin-bottom:16px;">
        <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4d4b5a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;">System Status</div>
        <div style="font-size:0.8rem;color:#9996a8;"><span class="status-dot"></span>FastAPI Backend</div>
        <div style="font-size:0.8rem;color:#9996a8;margin-bottom:6px;"><span class="status-dot"></span>Agent Online</div>
        <div style="font-size:0.8rem;color:#9996a8;"><span class="status-dot"></span>API Mode</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("↺ Refresh", use_container_width=True):
        st.rerun()

    st.markdown("---")
    st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:0.8rem;font-weight:700;color:#6b6878;text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;">Performance Logs</div>', unsafe_allow_html=True)

    if os.path.exists(API_PERFORMANCE_CSV):
        df = pd.read_csv(API_PERFORMANCE_CSV)
        col_a, col_b = st.columns(2)
        col_a.metric("Total Logs", len(df))
        col_b.metric("Recent", min(10, len(df)))
        st.dataframe(df.tail(10), hide_index=True, use_container_width=True)
    else:
        st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.75rem;color:#4d4b5a;padding:10px 0;">No performance data found.</div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown('<div style="font-size:0.72rem;color:#4d4b5a;font-family:\'DM Mono\',monospace;line-height:1.7;">Connected to FastAPI backend.<br>All calls routed via REST API.</div>', unsafe_allow_html=True)

# ============================================================
# MAIN CONTENT
# ============================================================
tab1, tab2, tab3 = st.tabs(["⬡  Agent", "◫  Storage", "⬆  Ingest"])

# ============================================================
# TAB 1 — QUERY AGENT
# ============================================================
with tab1:
    
    

    if "query_history" not in st.session_state:
        st.session_state.query_history = []
    if "active_mode" not in st.session_state:
        st.session_state.active_mode = "semantic"
    if "prefill_query" not in st.session_state:
        st.session_state.prefill_query = ""


    mode_cols = st.columns(4)
    with mode_cols[0]:
        st.markdown("""
    <div class="page-header">
        <h1>AI Agent</h1>
        <p>Semantic search · Document Q&A · Text-to-SQL — all in one interface</p>
    </div>
    """, unsafe_allow_html=True)
    for i, mode in enumerate(AGENT_MODES):
        with mode_cols[i+1]:
            is_active = st.session_state.active_mode == mode["id"]
            card_class = "agent-mode-card active" if is_active else "agent-mode-card"
            st.markdown(f"""
            <div class="{card_class}">
                <div class="icon">{mode['icon']}</div>
                <div class="title">{mode['title']}</div>
                <div class="desc">{mode['desc']}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"{'✓ Active' if is_active else 'Select'}", key=f"mode_{mode['id']}", use_container_width=True):
                st.session_state.active_mode = mode["id"]
                st.session_state.prefill_query = ""
                st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Active mode indicator ──
    active_mode = next(m for m in AGENT_MODES if m["id"] == st.session_state.active_mode)
    
    # ── Sample questions ──
    st.markdown('<div style="font-family:\'DM Mono\',monospace;font-size:0.7rem;color:#4d4b5a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">Quick Questions</div>', unsafe_allow_html=True)

    chip_cols = st.columns(2)
    for idx, sample in enumerate(active_mode["samples"]):
        with chip_cols[idx % 2]:
            if st.button(f"↗ {sample}", key=f"chip_{idx}", use_container_width=True):
                st.session_state.prefill_query = sample

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Query input ──
    query = st.text_area(
        "Ask anything",
        value=st.session_state.prefill_query,
        placeholder=active_mode["placeholder"],
        height=110,
        label_visibility="collapsed",
    )

    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 6])
    with btn_col1:
        ask_clicked = st.button("⬡  Run Query", type="primary", use_container_width=True)
    with btn_col2:
        if st.button("✕  Clear", use_container_width=True):
            st.session_state.query_history = []
            st.session_state.prefill_query = ""
            st.rerun()

    if ask_clicked:
        if query.strip():
            with st.spinner("Agent is processing…"):
                res, error = run_service(bot, query)
                if error:
                    st.error(f"Agent error: {error}")
                else:
                    st.session_state.query_history.insert(0, {
                        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "query": query.strip(),
                        "response": res,
                        "mode": active_mode["title"],
                        "mode_icon": active_mode["icon"],
                    })
            st.session_state.prefill_query = ""
            st.rerun()
        else:
            st.warning("Please enter a question first.")

    # ── Response display ──
    if st.session_state.query_history:
        latest = st.session_state.query_history[0]
        st.markdown(f"""
        <div class="response-bubble">
            <div class="q-label">{latest.get('mode_icon','🔍')} {latest.get('mode','Agent')} · {latest['timestamp']}</div>
            <div class="q-text">{latest['query']}</div>
            <div class="a-label">◈ Response</div>
            <div class="a-text">{latest['response']}</div>
        </div>
        """, unsafe_allow_html=True)
        # # Render response as proper markdown (handles bold, lists, code, etc.)
        # st.markdown(
        #     f"<div style='background:#18181e;border:1px solid rgba(255,255,255,0.06);border-left:3px solid #00d2aa;border-radius:0 0 14px 14px;padding:20px 24px;margin-top:-2px;font-size:0.92rem;color:#e8e6e1;line-height:1.75;'>",
        #     unsafe_allow_html=True
        # )
        # st.markdown(latest['response'])
        st.markdown("</div>", unsafe_allow_html=True)
        if len(st.session_state.query_history) > 1:
            st.markdown('<div style="font-family:\'Syne\',sans-serif;font-size:0.82rem;font-weight:700;color:#6b6878;text-transform:uppercase;letter-spacing:.08em;margin:24px 0 12px;">Previous Queries</div>', unsafe_allow_html=True)
            for item in st.session_state.query_history[1:]:
                with st.expander(f"{item.get('mode_icon','🔍')}  {item['timestamp']}  ·  {item['query'][:60]}{'…' if len(item['query'])>60 else ''}"):
                    st.markdown(f"**Q:** {item['query']}")
                    st.markdown(item['response'])
    else:
        st.markdown("""
        <div style="text-align:center;padding:60px 0;border:1px dashed rgba(255,255,255,0.06);border-radius:14px;margin-top:16px;">
            <div style="font-size:2.5rem;margin-bottom:16px;">⬡</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#6b6878;margin-bottom:6px;">No queries yet</div>
            <div style="font-size:0.8rem;color:#4d4b5a;">Select a mode, pick a sample question, or type your own.</div>
        </div>
        """, unsafe_allow_html=True)    

# ============================================================
# TAB 2 — STORAGE
# ============================================================
with tab2:
    

    files_list, error = run_service(get_all_files_from_db)

    if error:
        st.error(f"Database error: {error}")
    elif files_list:
        total = len(files_list)
        ftypes = set(d.get("file_type", "?") for d in files_list)
        platforms = set(d.get("source_platform", "local") for d in files_list)

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("""
            <div class="page-header">
                <h1>My Files</h1>
                <h5>All your files from connected sources</p>
            </div>
            """, unsafe_allow_html=True)
        with m3:
            st.markdown("<br>", unsafe_allow_html=True)
            m3.metric("Total Files", total)
        with m4:
            st.markdown("<br>", unsafe_allow_html=True)
            m4.metric("File Types", len(ftypes))

        search = st.text_input("", placeholder="🔎  Filter files by name, type, or source…", label_visibility="collapsed")
        display_docs = [d for d in files_list if search.lower() in str(d).lower()] if search else files_list

        if not display_docs:
            st.markdown('<div style="text-align:center;padding:40px;color:#4d4b5a;font-size:0.85rem;">No files match your filter.</div>', unsafe_allow_html=True)
        else:
            pairs = [display_docs[i:i+2] for i in range(0, len(display_docs), 2)]
            for pair in pairs:
                cols = st.columns([1, 0.04, 1])
                for col, doc in zip([cols[0], cols[2]], pair):
                    p_info = PLATFORM_META.get(doc.get("source_platform", "local").lower(), {"label": "Unknown", "color": "#6B7280"})
                    ftype = doc.get("file_type", "?").upper()
                    ftype_colors = {"PDF": "#ef4444", "CSV": "#10b981", "TXT": "#f59e0b", "DOCX": "#3b82f6"}
                    ftype_color = ftype_colors.get(ftype, "#6345ff")
                    file_size = doc.get("file_size")
                    size_str = f"{file_size/1024:.1f} KB" if isinstance(file_size, (int, float)) else "—"
                    version = doc.get("version", 0)
                    desc = doc.get("description", "")
                    hosted = doc.get("hosted_link", "")

                    with col:
                        # Fallback for hosted link if it's not a full URL
                        display_link = hosted if hosted and hosted.startswith("http") else ""

                        with st.container(border=True):
                            st.markdown(f"### **{doc.get('file_name', 'Untitled')}**")
                            c1, c2, c3, c4, c5 = st.columns([2, 2, 2, 2, 2])
                            c1.markdown(f"File Type: `{doc.get('file_type', '?').upper()}`")
                            c2.markdown(f"Version: `v{doc.get('version', 0)}`")
                            c3.markdown(f"Source: <span style='background:{p_info['color']};color:white;border-radius:20px;padding:2px 10px;font-size:0.75rem;'>{p_info['label']}</span>", unsafe_allow_html=True)
                            # File size (KB) if available
                            file_size = doc.get('file_size')
                            size_str = f"File Size: {file_size/1024:.1f} KB" if isinstance(file_size, (int, float)) else "N/A"
                            c4.markdown(f"`{size_str}`")
                            # Description if present
                            desc = doc.get('description')
                            c5.markdown(f"Description: {desc}" if desc else "")

                            # with st.expander(" View Links"):
                            hosted = doc.get("hosted_link", "")
                            if hosted.startswith("http"):
                                st.markdown(f" **URL:**  [Open File]({hosted})")
                            else:
                                st.caption("URL: `Not available`")

                st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="text-align:center;padding:80px 0;border:1px dashed rgba(255,255,255,0.06);border-radius:14px;">
            <div style="font-size:2.5rem;margin-bottom:16px;">◫</div>
            <div style="font-family:'Syne',sans-serif;font-weight:700;color:#6b6878;margin-bottom:6px;">No files indexed</div>
            <div style="font-size:0.8rem;color:#4d4b5a;">Go to the Ingest tab to upload your first file.</div>
        </div>
        """, unsafe_allow_html=True)

# ============================================================
# TAB 3 — INGESTION
# ============================================================
with tab3:
    st.markdown("""
    <div class="page-header">
        <h1>Ingest & Embed</h1>
        <p>Upload files or sync cloud sources — converted to vector embeddings automatically</p>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns(2, gap="large")

    with left:
        st.markdown("""
        <div class="upload-zone">
            <h3>◈ Local File Upload</h3>
            <p>Supports PDF, TXT, and CSV files.<br>Chunked, embedded, and indexed automatically.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        file = st.file_uploader(
            "Upload file",
            type=["pdf", "txt", "csv"],
            label_visibility="collapsed",
        )

        if st.button("⬆  Index File", type="primary", use_container_width=True):
            if file:
                with st.spinner("Uploading to backend…"):
                    try:
                        result = upload_file_bytes(file.name, file.getvalue())
                        db_status = result.get("data", {}).get("db_status", 1)
                        fname = result.get("data", {}).get("file_name", file.name)
                        db_msg = result.get("data", {}).get("message", "")
                        upload_result = result.get("data", {}).get("upload_result", "")
                        if db_status == 2:
                            st.warning(f"**{fname}** — identical file already exists in the index.")
                        elif upload_result == "versioned":
                            st.success(f"**{fname}** — new version saved. {db_msg}")
                        else:
                            st.success(f"**{fname}** — indexed and embedded successfully!")
                    except Exception as e:
                        st.error(f"Upload error: {e}")
            else:
                st.warning("Please select a file first.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#18181e;border-radius:10px;padding:14px 16px;">
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4d4b5a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">Supported Formats</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <span style="background:#ef4444;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">PDF</span>
                <span style="background:#10b981;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">CSV</span>
                <span style="background:#f59e0b;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">TXT</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        st.markdown("""
        <div class="upload-zone">
            <h3>☁ Cloud Source Sync</h3>
            <p>Paste a direct link from Google Drive, AWS S3,<br>Azure Blob, or GCP Storage.</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

        url_input = st.text_input(
            "Cloud URL",
            placeholder="https://drive.google.com/… or s3://bucket/file.pdf",
            label_visibility="collapsed",
        )

        if st.button("☁  Sync Source", use_container_width=True):
            if url_input.strip():
                with st.spinner("Sending to backend…"):
                    try:
                        result = process_link_api(url_input.strip())
                        db_status = result.get("data", {}).get("db_status", 1)
                        fname = result.get("data", {}).get("file_name", url_input)
                        if db_status == 2:
                            st.warning(f"**{fname}** — already exists in the index.")
                        else:
                            st.success(f"**{fname}** — synced and embedded!")
                    except Exception as e:
                        st.error(f"Sync error: {e}")
            else:
                st.warning("Please provide a URL.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("""
        <div style="background:#18181e;border-radius:10px;padding:14px 16px;">
            <div style="font-family:'DM Mono',monospace;font-size:0.7rem;color:#4d4b5a;text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;">Supported Sources</div>
            <div style="display:flex;gap:8px;flex-wrap:wrap;">
                <span style="background:#FF9900;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">AWS S3</span>
                <span style="background:#34A853;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">Google Drive</span>
                <span style="background:#0078D4;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">Azure Blob</span>
                <span style="background:#4285F4;border-radius:6px;padding:3px 10px;font-size:0.72rem;color:white;font-family:'DM Mono',monospace;">GCP</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("""
    <div style="background:#18181e;border:1px solid rgba(255,255,255,0.05);border-radius:12px;padding:18px 24px;">
        <div style="font-family:'Syne',sans-serif;font-size:0.8rem;font-weight:700;color:#6b6878;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;">How Ingestion Works</div>
        <div style="display:flex;gap:0;align-items:center;flex-wrap:wrap;">
            <div style="text-align:center;flex:1;min-width:100px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">📄</div>
                <div style="font-size:0.72rem;color:#9996a8;">Upload / Link</div>
            </div>
            <div style="color:#4d4b5a;font-size:1.2rem;padding:0 8px;">→</div>
            <div style="text-align:center;flex:1;min-width:100px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">✂️</div>
                <div style="font-size:0.72rem;color:#9996a8;">Chunk & Parse</div>
            </div>
            <div style="color:#4d4b5a;font-size:1.2rem;padding:0 8px;">→</div>
            <div style="text-align:center;flex:1;min-width:100px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">⬡</div>
                <div style="font-size:0.72rem;color:#9996a8;">Embed</div>
            </div>
            <div style="color:#4d4b5a;font-size:1.2rem;padding:0 8px;">→</div>
            <div style="text-align:center;flex:1;min-width:100px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">🗄️</div>
                <div style="font-size:0.72rem;color:#9996a8;">Index & Store</div>
            </div>
            <div style="color:#4d4b5a;font-size:1.2rem;padding:0 8px;">→</div>
            <div style="text-align:center;flex:1;min-width:100px;">
                <div style="font-size:1.5rem;margin-bottom:6px;">🔍</div>
                <div style="font-size:0.72rem;color:#9996a8;">Query Ready</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
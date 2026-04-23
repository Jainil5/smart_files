import streamlit as st
import os
import sys
import pandas as pd
from datetime import datetime
import warnings

# Suppress repetitive model path warnings
warnings.filterwarnings("ignore", message="Accessing `__path__` from .*")

# --- Path Optimization ---
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)
# Add app folder to path for imports
_APP_DIR = os.path.join(_ROOT_DIR, "app")
if _APP_DIR not in sys.path:
    sys.path.insert(0, _APP_DIR)

# --- Direct Service Imports (Bypassing API) ---
from app.services.main_agent import bot
from app.services.new_link import process_link_api
from app.services.main_db import get_all_files_from_db
from app.services.embedder import embed_file
from app.services.config import DOCS_DIR, LOGS_DIR, API_PERFORMANCE_CSV

# ============================================
# Configuration
# ============================================
st.set_page_config(
    page_title="Smart Files (Direct)",
    page_icon="",
    layout="wide"
)

# Helper to handle direct service calls like API responses
def run_service(func, *args, **kwargs):
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        return None, str(e)

# ============================================
# Main UI
# ============================================
st.title(" AI File System Interface (Direct Service Mode)")
st.markdown("---")

tab1, tab2, tab3 = st.tabs([
    " Query Agent", 
    " View Files",
    " Upload File"
])

# ============================================
# TAB 3: Data Ingestion
# ============================================
with tab3:
    st.title("📤 Ingestion & Analysis Pipeline")
    st.write("Convert raw unstructured files into high-dimensional vector embeddings.")

    left, right = st.columns(2)

    with left:
        st.markdown("### 📁 Physical File Upload")
        st.caption("Upload files directly for server-side processing.")
        
        file = st.file_uploader("Upload PDF, TXT, or CSV", type=['pdf', 'txt', 'csv'], label_visibility="collapsed")
        
        if st.button("Index Physical File", type="primary", width='stretch'):
            if file:
                with st.spinner("Chunking & Embedding..."):
                    try:
                        # 1. Save file locally
                        save_path = os.path.join(DOCS_DIR, file.name)
                        with open(save_path, "wb") as f:
                            f.write(file.getvalue())
                        
                        # 2. Process via Service
                        result = process_link_api(save_path)
                        upload_result = result.get("data", {}).get("upload_result")
                        
                        # 3. Embed if not duplicate
                        if upload_result != "duplicate":
                            embed_file(save_path)
                        
                        # 4. Display Result
                        db_status = result.get("data", {}).get("db_status", 1)
                        fname = result.get("data", {}).get("file_name", file.name)
                        db_msg = result.get("data", {}).get("message", "")
                        
                        if db_status == 2:
                            st.warning(f"File**{fname}** — identical file already exists.")
                        elif upload_result == "versioned":
                            st.success(f"**{fname}** — new version saved. ({db_msg})")
                        else:
                            st.success(f"**{fname}** — indexed successfully!")
                            
                    except Exception as e:
                        st.error(f"Processing Error: {e}")
            else:
                st.warning("Please choose a file.")

    with right:
        st.markdown("### 🌐 Cloud Link Sync")
        st.caption("Provide a URL from GDrive, S3, or Azure.")
        
        url_input = st.text_input("Paste Link Here", placeholder="https://...", label_visibility="collapsed")
        
        if st.button("Sync Cloud Source", width='stretch'):
            if url_input:
                with st.spinner("Connecting to Cloud..."):
                    try:
                        # 1. Process link
                        result = process_link_api(url_input)
                        upload_result = result.get("data", {}).get("upload_result")
                        local_path = result.get("data", {}).get("local_path")
                        
                        # 2. Embed if successful
                        if local_path and upload_result != "duplicate":
                            embed_file(local_path)
                            
                        # 3. Display Result
                        db_status = result.get("data", {}).get("db_status", 1)
                        fname = result.get("data", {}).get("file_name", url_input)
                        
                        if db_status == 2:
                            st.warning(f"**{fname}** — already exists.")
                        else:
                            st.success(f"**{fname}** — synced and embedded!")
                    except Exception as e:
                        st.error(f"Sync failed: {e}")
            else:
                st.warning("Please provide a URL.")

# ============================================
# TAB 1: Query Agent
# ============================================
with tab1:
    st.header(" Query AI Agent")
    
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    # Predefined example queries for quick access
    sample_questions = [
        "Find me research paper on h2ogpt.",
        "Why was my leave application rejected?",
        "Find patients older than 50 with blood group A+ admitted under Emergency."
    ]

    # Dropdown to select a sample query (empty option resets)
    selected_sample = st.selectbox(
        "Select a sample question",
        options=[""] + sample_questions,
        format_func=lambda x: x if x else "None"
    )

    # Text area for the actual query, pre‑filled with the selected sample
    query = st.text_area(
        "Your Question",
        value=selected_sample,
        placeholder="Ask something about your files...",
        height=100,
    )

    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button(" Ask", type="primary"):
            if query:
                with st.spinner("Thinking..."):
                    res, error = run_service(bot, query)
                    if error:
                        st.error(f"Agent Error: {error}")
                    else:
                        st.session_state.query_history.insert(0, {
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "query": query,
                            "response": res
                        })
            else:
                st.error("Please enter a question")
    
    if st.button(" Clear History", key="clear_q"):
        st.session_state.query_history = []
        st.rerun()
    
    if st.session_state.query_history:
        st.markdown("###  Latest Response")
        latest = st.session_state.query_history[0]
        
        # Premium chat-like response bubble
        st.markdown(f"""
        <div style="background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #0078D4; margin-bottom: 20px;">
            <p style="color: #555; font-size: 0.8rem; margin-bottom: 5px;">{latest['timestamp']}</p>
            <p style="font-weight: 600; margin-bottom: 10px;">Q: {latest['query']}</p>
            <div style="background-color: white; padding: 15px; border-radius: 10px; border: 1px solid #e6e9ef;">
                {latest['response']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if len(st.session_state.query_history) > 1:
            st.markdown("###  Query History")
            for item in st.session_state.query_history[1:]:
                with st.expander(f" {item['timestamp']} - {item['query'][:50]}..."):
                    st.markdown(f"**Q:** {item['query']}")
                    st.markdown(f"**A:** {item['response']}")


# ============================================
# TAB 2: Knowledge Storage
# ============================================
with tab2:
    st.title(" Knowledge Storage")
    
    PLATFORM_META = {
        "aws":   {"label": "AWS S3",       "color": "#FF9900"},
        "drive": {"label": "Google Drive", "color": "#34A853"},
        "azure": {"label": "Azure Blob",   "color": "#0078D4"},
        "gcp":   {"label": "GCP Storage",  "color": "#4285F4"},
        "local": {"label": "Local Disk",   "color": "#6B7280"},
        "mongo": {"label": "MongoDB",      "color": "#4DB33D"},
    }

    files_list, error = run_service(get_all_files_from_db)
    
    if error:
        st.error(f"DB Error: {error}")
    elif files_list:
        total = len(files_list)
        ftypes = set(d.get("file_type", "?") for d in files_list)

        s1, s2 = st.columns(2)
        s1.metric(" Total Files", total)
        s2.metric(" File Types", len(ftypes))

        search = st.text_input(" Search files...", placeholder="Filter...")
        display_docs = [d for d in files_list if search.lower() in str(d).lower()] if search else files_list

        pairs = [display_docs[i:i+2] for i in range(0, len(display_docs), 2)]
        for pair in pairs:
            cols = st.columns([10, 0.05, 10])
            for col, doc in zip([cols[0], cols[2]], pair):
                p_info = PLATFORM_META.get(doc.get("source_platform", "local").lower(), {"label": "Unknown", "color": "#9CA3AF"})
                with col:
                    with st.container(border=True):
                        st.markdown(f"### **{doc.get('file_name', 'Untitled')}**")
                        c1, c2, c3, c4, c5 = st.columns([1, 1, 1.5, 1, 2])
                        c1.markdown(f"`File Type: {doc.get('file_type', '?').upper()}`")
                        c2.markdown(f"`Version: v{doc.get('version', 0)}`")
                        c3.markdown(f"<span style='background:{p_info['color']};color:white;border-radius:20px;padding:2px 10px;font-size:0.75rem;'>{p_info['label']}</span>", unsafe_allow_html=True)
                        # File size (KB) if available
                        file_size = doc.get('file_size')
                        size_str = f"File Size: {file_size/1024:.1f} KB" if isinstance(file_size, (int, float)) else "N/A"
                        c4.markdown(f"`{size_str}`")
                        # Description if present
                        desc = doc.get('description')
                        c5.markdown(f"Description: {desc}" if desc else "")

                        st.divider()
                        with st.expander(" View Links"):
                            hosted = doc.get("hosted_link", "")
                            if hosted.startswith("http"):
                                st.markdown(f" **Hosted URL:** [Open File]({hosted})")
                            else:
                                st.caption(" Hosted URL: `Not available`")
    else:
        st.info("No files indexed yet.")

# ============================================
# Sidebar
# ============================================
with st.sidebar:
    st.title("Smart Files (Direct)")
    st.markdown("""
    **Direct Service Integration**
    This UI interacts directly with the Python services, bypassing the FastAPI layer.
    """)
    st.divider()
    
    if st.button(" Refresh UI"):
        st.rerun()

    st.markdown("---")
    st.header(" Performance Data")
    if os.path.exists(API_PERFORMANCE_CSV):
        df = pd.read_csv(API_PERFORMANCE_CSV)
        st.metric("Total API Logs", len(df))
        st.dataframe(df.tail(10), hide_index=True)
    else:
        st.caption("No performance logs found.")

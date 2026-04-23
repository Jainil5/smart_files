import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd

# ============================================
# Configuration
# ============================================
st.set_page_config(
    page_title="Smart Files",
    page_icon="",
    layout="wide"
)

API_BASE_URL = "http://20.189.119.41:8000"

def make_request(method, endpoint, **kwargs):
    url = f"{API_BASE_URL}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, **kwargs)
        elif method == "POST":
            response = requests.post(url, **kwargs)
        
        response.raise_for_status()
        return response.json(), None
    except requests.exceptions.ConnectionError:
        return None, f" Cannot connect to {API_BASE_URL}. Is the server running?"
    except requests.exceptions.HTTPError as e:
        return None, f" HTTP Error: {e.response.status_code} - {e.response.text}"
    except Exception as e:
        return None, f" Error: {str(e)}"
# ============================================
# Main UI
# ============================================
st.title(" AI File System Interface")
st.markdown("---")

tab1, tab2, tab3= st.tabs([
    " Query Agent", 
    " View Files",
    " Upload File"
])

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
                        files = {"file": (file.name, file.getvalue(), file.type)}
                        res = requests.post(f"{API_BASE_URL}/upload-file", files=files)
                        if res.status_code == 200:
                            data      = res.json().get("data", {})
                            db_status = data.get("db_status", 1)
                            result    = data.get("upload_result", "new")
                            fname     = data.get("file_name", file.name)
                            db_msg    = data.get("message", "")
                            if db_status == 2:
                                st.warning(f"⚠️ **{fname}** — identical file already exists. No changes made.")
                            elif result == "versioned":
                                st.success(f"🔄 **{fname}** — new version saved & embedded. *({db_msg})*")
                            else:
                                st.success(f"✅ **{fname}** — indexed and embedded successfully!")
                        else:
                            st.error(f"Error {res.status_code}: {res.text}")
                    except Exception as e:
                        st.error(f"Failed to reach API: {e}")
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
                        res = requests.post(f"{API_BASE_URL}/upload", json={"path": url_input})
                        if res.status_code == 200:
                            data      = res.json().get("data", {})
                            db_status = data.get("db_status", 1)
                            result    = data.get("upload_result", "new")
                            fname     = data.get("file_name", url_input)
                            db_msg    = data.get("message", "")
                            if db_status == 2:
                                st.warning(f"⚠️ **{fname}** — identical file already exists. No changes made.")
                            elif result == "versioned":
                                st.success(f"🔄 **{fname}** — new version synced & embedded. *({db_msg})*")
                            else:
                                st.success(f"✅ **{fname}** — synced and embedded successfully!")
                        else:
                            st.error("Sync failed. Check URL accessibility.")
                    except Exception as e:
                        st.error(f"Connection Error: {e}")
            else:
                st.warning("Please provide a URL.")

    st.divider()
    st.info("**Architecture Note:** Every upload triggers a background task that generates ChromaDB embeddings for the AI Agent Hub.")

# ============================================
# TAB 1: Query Agent
# ============================================
with tab1:
    st.header(" Query AI Agent")
    st.markdown("Ask questions to the AI agent about your files")
    
    # Query history in session state
    if 'query_history' not in st.session_state:
        st.session_state.query_history = []
    
    query = st.text_area(
        "Your Question",
        placeholder="Ask something about your files...",
        height=100
    )
    
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button(" Ask", type="primary"):
            if not query:
                st.error("Please enter a question")
            else:
                with st.spinner("Thinking..."):
                    data, error = make_request("POST", "/query", json={"query": query})
                    
                    if error:
                        st.error(error)
                    else:
                        if data.get("status") == "success":
                            response = data.get("response", "No response")
                            
                            # Add to history
                            st.session_state.query_history.insert(0, {
                                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                "query": query,
                                "response": response
                            })
                            
                            st.success(" Response received!")
    
    with col2:
        if st.button(" Clear History"):
            st.session_state.query_history = []
            st.rerun()
    
    # Display current response
    if st.session_state.query_history:
        st.markdown("###  Latest Response")
        latest = st.session_state.query_history[0]
        st.info(latest["response"])
        
        # Show history
        if len(st.session_state.query_history) > 1:
            st.markdown("###  Query History")
            for i, item in enumerate(st.session_state.query_history[1:], 1):
                with st.expander(f" {item['timestamp']} - {item['query'][:50]}..."):
                    st.markdown(f"**Q:** {item['query']}")
                    st.markdown(f"**A:** {item['response']}")

# with tab2:
#     st.header(" All Files in Database")
    
#     if st.button(" Refresh Files", type="primary"):
#         with st.spinner("Fetching files..."):
#             data, error = make_request("GET", "/files")
            
#             if error:
#                 st.error(error)
#             else:
#                 if data.get("status") == "success":
#                     files = data.get("data", [])
                    
#                     if files:
#                         st.success(f" Found {len(files)} file(s)")
                        
#                         # Convert to DataFrame for better display
#                         df = pd.DataFrame(files)
                        
#                         # Display metrics
#                         col1, col2, col3 = st.columns(3)
#                         with col1:
#                             st.metric("Total Files", len(files))
#                         with col2:
#                             if 'version' in df.columns:
#                                 st.metric("Total Versions", df['version'].sum())
#                         with col3:
#                             if 'file_name' in df.columns:
#                                 unique_files = df['file_name'].nunique()
#                                 st.metric("Unique Files", unique_files)
                        
#                         # Display table
#                         st.dataframe(
#                             df,
#                             use_container_width=True,
#                             hide_index=True
#                         )
                        
#                         # Download as CSV
#                         csv = df.to_csv(index=False)
#                         st.download_button(
#                             label=" Download as CSV",
#                             data=csv,
#                             file_name=f"files_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
#                             mime="text/csv"
#                         )
                        
#                         # Show raw JSON
#                         with st.expander(" View Raw JSON"):
#                             st.json(files)
#                     else:
#                         st.info("No files found in database")


with tab2:
    PLATFORM_META = {
    "aws":   {"icon": "",  "label": "AWS S3",       "color": "#FF9900"},
    "drive": {"icon": "",  "label": "Google Drive", "color": "#34A853"},
    "azure": {"icon": "",  "label": "Azure Blob",   "color": "#0078D4"},
    "gcp":   {"icon": "",  "label": "GCP Storage",  "color": "#4285F4"},
    "local": {"icon": "",  "label": "Local Disk",   "color": "#6B7280"},
    "mongo": {"icon": "",  "label": "MongoDB",      "color": "#4DB33D"},
    }   

    FILE_ICONS = {
        "pdf": "", "csv": "", "xlsx": "", "xls": "",
        "png": "", "jpg": "", "jpeg": "",
        "doc": "", "docx": "", "txt": "",
    }

    def get_platform_info(source_platform: str) -> dict:
        key = (source_platform or "local").lower()
        for k, v in PLATFORM_META.items():
            if k in key:
                return v
        return {"icon": "", "label": (source_platform or "UNKNOWN").upper(), "color": "#9CA3AF"}

    def get_file_icon(file_type: str) -> str:
        return FILE_ICONS.get((file_type or "").lower(), "")


    # ------------------ PAGE ------------------ #
    st.title(" Knowledge Storage")
    \
    try:
        response = requests.get(f"{API_BASE_URL}/files")
        raw_data = response.json()

        if isinstance(raw_data, dict) and raw_data.get("status") == "success":
            files_list = raw_data.get("data", [])
        else:
            files_list = raw_data if isinstance(raw_data, list) else []

        if files_list:
            # --- Stats ---
            total     = len(files_list)
            platforms = set(d.get("source_platform", "local") for d in files_list)
            ftypes    = set(d.get("file_type", "?") for d in files_list)

            s1, s2, s3 = st.columns(3)
            s1.metric(" Total Files", total)
            # s2.metric(" Platforms", len(platforms))
            s3.metric(" File Types", len(ftypes))

            search = st.text_input(" Search files...", placeholder="Filter by name, type, or platform...")
            display_docs = [d for d in files_list if search.lower() in str(d).lower()] if search else files_list

            # --- 2-column grid ---
            pairs = [display_docs[i:i+2] for i in range(0, len(display_docs), 2)]

            for pair in pairs:
                left_col, gap_col, right_col = st.columns([10, 0.05, 10])

                for col, doc in zip([left_col, right_col], pair):
                    name        = doc.get("file_name", "Untitled")
                    f_type      = (doc.get("file_type") or "?").lower()
                    source_plat = doc.get("source_platform") or "local"
                    hosted      = (doc.get("hosted_link") or "").strip()
                    local       = (doc.get("local_path") or "").strip()
                    version     = doc.get("version", 0)
                    file_size   = doc.get("file_size")

                    p_info   = get_platform_info(source_plat)
                    f_icon   = get_file_icon(f_type)
                    size_str = f"{file_size / 1024:.1f} KB" if file_size else "N/A"

                    with col:
                        with st.container(border=True):
                            # Title
                            st.markdown(f"**{f_icon} {name}**")

                            # Chips row  use columns for inline layout
                            c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
                            c1.markdown(f" `{f_type.upper()}`")
                            c2.markdown(f" `v{version}`")
                            c3.markdown(f" `{size_str}`")
                            c4.markdown(
                                f"<span style='background:{p_info['color']};color:white;"
                                f"border-radius:20px;padding:2px 10px;font-size:0.78rem;"
                                f"font-weight:600;'>{p_info['icon']} {p_info['label']}</span>",
                                unsafe_allow_html=True
                            )

                            st.divider()

                            # Click-to-reveal links
                            with st.expander(" View Links"):
                                if hosted.startswith("http"):
                                    st.markdown(f" **Hosted URL:** [Open File]({hosted})")
                                else:
                                    st.caption(" Hosted URL: `Setup Cloud Auth to access!`")

                                # if local:
                                #     st.markdown(f" **Local Path:** `{local}`")
                                    
                                #     # Convert local system path to API served endpoint
                                #     clean_local = local.split("data/")[-1] if "data/" in local else local
                                #     local_url = f"{BASE_URL}/data/{clean_local}"
                                #     st.markdown(f" **Web View:** <a href='{local_url}' target='_blank'>Open in new tab</a>", unsafe_allow_html=True)
                                # else:
                                #     st.caption(" Local Path: `Not available`")

                # Visual column divider
                with gap_col:
                    st.markdown(
                        "<div style='border-left:1.5px solid rgba(128,128,128,0.2);height:100%;min-height:180px;'></div>",
                        unsafe_allow_html=True
                    )

        else:
            st.info("No files indexed yet. Head to **Data Ingestion** to add your first document.")

    except Exception as e:
        st.error(f"Failed to fetch files: {str(e)}")
        st.caption("Make sure the FastAPI backend is running at http://127.0.0.1:8000")


# ============================================
# Sidebar Info
# ============================================
with st.sidebar:
    st.title("Smart Files AI")
    st.markdown("""
    **Unified AI Document Engine**
    
    This system enables intelligent interaction with your files using advanced RAG and metadata tracking.
    
    ### Features:
    *   **AI Assistant**: Ask questions across all your documents. Uses semantic search to find answers and can even generate SQL for structured data.
    *   **Knowledge Storage**: A centralized hub to manage indexed files. Track versions, source platforms (S3, Drive, etc.), and file metadata.
    *   **Data Ingestion**: Seamlessly import data from local uploads or cloud URLs. Files are automatically chunked and embedded into ChromaDB.
    *   **Performance Monitoring**: Track API latency and system health in real-time.
    """)
    
    st.markdown("---")
    st.markdown("### System Status")
    
    # Test connection
    if st.button(" Test Connection"):
        with st.spinner("Testing..."):
            data, error = make_request("GET", "/")
            if error:
                st.error(" Disconnected")
            else:
                st.success(" Connected")
    
    st.markdown("---")
    st.header(" API Performance Logs")
    st.markdown("View performance metrics from your API")
    
    logs_url = st.text_input(
        "Performance CSV URL",
        value=f"{API_BASE_URL}/logs/api_performance.csv",
        help="URL to your api_performance.csv file"
    )
    
    if st.button(" Load Performance Data", type="primary"):
        with st.spinner("Loading performance logs..."):
            try:
                response = requests.get(logs_url)
                response.raise_for_status()
                
                # Parse CSV
                from io import StringIO
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                
                if not df.empty:
                    st.success(f" Loaded {len(df)} log entries")
                    
                    # Metrics
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Total Requests", len(df))
                    with col2:
                        success_rate = (df['status'] == 'success').sum() / len(df) * 100
                        st.metric("Success Rate", f"{success_rate:.1f}%")
                    with col3:
                        avg_latency = df['latency'].mean()
                        st.metric("Avg Latency", f"{avg_latency:.3f}s")
                    with col4:
                        max_latency = df['latency'].max()
                        st.metric("Max Latency", f"{max_latency:.3f}s")
                    
                    
                    
                    # Recent logs
                    st.markdown("### Recent Requests")
                    st.dataframe(
                        df.tail(20).sort_values('timestamp', ascending=False),
                        use_container_width=True,
                        hide_index=True
                    )
                    
                else:
                    st.info("No performance data available yet")
                    
            except requests.exceptions.HTTPError as e:
                st.error(f" Cannot access logs: {e.response.status_code}")
                st.info("Make sure your FastAPI server has the /logs path mounted")
            except Exception as e:
                st.error(f" Error loading logs: {str(e)}")
    
    
            st.markdown("Made with  using Streamlit")
import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Ingestion", page_icon="📤", layout="wide")

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
                    res = requests.post(f"{BASE_URL}/upload-file", files=files)
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
                    res = requests.post(f"{BASE_URL}/upload", json={"path": url_input})
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
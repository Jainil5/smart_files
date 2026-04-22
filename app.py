import streamlit as st
import requests
import json

BASE_URL = "http://20.189.119.41:8000"

st.set_page_config(page_title="Smart Files AI", page_icon="🤖", layout="wide")

# Theme-aware CSS
st.markdown("""
    <style>
    .stTabs [aria-selected="true"] { background-color: #2E5BFF !important; }
    .agent-card {
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #2E5BFF;
        background-color: rgba(128, 128, 128, 0.05);
        margin-bottom: 20px;
        white-space: pre-wrap;
    }
    </style>
    """, unsafe_allow_html=True)

def render_ai_response(response_content):
    try:
        parsed = json.loads(response_content)
        # Handle SQL
        if isinstance(parsed, dict) and "text" in parsed:
            st.subheader("📊 SQL Query")
            st.code(parsed["text"], language="sql")
        # Handle RAG
        elif isinstance(parsed, dict) and "response" in parsed:
            st.markdown(f"<div class='agent-card'><h4>🤖 Agent Answer</h4><p>{parsed['response']}</p></div>", unsafe_allow_html=True)
            if "hosted_link" in parsed: st.link_button("Open Source", parsed['hosted_link'])
        # Handle Search
        elif isinstance(parsed, list):
            st.subheader("🔍 Search Results")
            st.table(parsed)
    except:
        st.markdown(f"<div class='agent-card'>{response_content}</div>", unsafe_allow_html=True)

st.title("🤖 Smart Files AI Agent")
st.write("Ask your multimodal agent about company files, clinical reports, or financial data.")

# Quick Demos
st.markdown("### ⚡ Quick Samples")
c1, c2, c3 = st.columns(3)
trigger_q = ""
if c1.button("🔍 Search Leave Policy"): trigger_q = "Find me a file related to leave policy"
if c2.button("📖 Explain Benefits"): trigger_q = "Explain the maternity leave policy"
if c3.button("📊 SQL Revenue"): trigger_q = "Total revenue for female customers?"

query_input = st.text_input("Enter Query:", value=trigger_q)

if st.button("Run Agent", type="primary") or trigger_q:
    if query_input:
        with st.spinner("Processing..."):
            res = requests.post(f"{BASE_URL}/query", json={"query": query_input}).json()
            render_ai_response(res.get("response"))
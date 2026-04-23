import streamlit as st
import requests

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="My Storage", page_icon="📂", layout="wide")

# ------------------ HELPERS ------------------ #
PLATFORM_META = {
    "aws":   {"icon": "☁️",  "label": "AWS S3",       "color": "#FF9900"},
    "drive": {"icon": "🟢",  "label": "Google Drive", "color": "#34A853"},
    "azure": {"icon": "🔵",  "label": "Azure Blob",   "color": "#0078D4"},
    "gcp":   {"icon": "🟣",  "label": "GCP Storage",  "color": "#4285F4"},
    "local": {"icon": "💾",  "label": "Local Disk",   "color": "#6B7280"},
    "mongo": {"icon": "🍃",  "label": "MongoDB",      "color": "#4DB33D"},
}

FILE_ICONS = {
    "pdf": "📄", "csv": "📊", "xlsx": "📊", "xls": "📊",
    "png": "🖼️", "jpg": "🖼️", "jpeg": "🖼️",
    "doc": "📝", "docx": "📝", "txt": "📃",
}

def get_platform_info(source_platform: str) -> dict:
    key = (source_platform or "local").lower()
    for k, v in PLATFORM_META.items():
        if k in key:
            return v
    return {"icon": "📁", "label": (source_platform or "UNKNOWN").upper(), "color": "#9CA3AF"}

def get_file_icon(file_type: str) -> str:
    return FILE_ICONS.get((file_type or "").lower(), "📁")


# ------------------ PAGE ------------------ #
st.title("📂 Knowledge Storage")
\
try:
    response = requests.get(f"{BASE_URL}/files")
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
        s1.metric("📁 Total Files", total)
        s2.metric("☁️ Platforms", len(platforms))
        s3.metric("🗂 File Types", len(ftypes))
        st.divider()

        search = st.text_input("🔍 Search files...", placeholder="Filter by name, type, or platform...")
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

                        # Chips row — use columns for inline layout
                        c1, c2, c3, c4 = st.columns([1, 1, 1, 1.5])
                        c1.markdown(f"📦 `{f_type.upper()}`")
                        c2.markdown(f"🔢 `v{version}`")
                        c3.markdown(f"📏 `{size_str}`")
                        c4.markdown(
                            f"<span style='background:{p_info['color']};color:white;"
                            f"border-radius:20px;padding:2px 10px;font-size:0.78rem;"
                            f"font-weight:600;'>{p_info['icon']} {p_info['label']}</span>",
                            unsafe_allow_html=True
                        )

                        st.divider()

                        # Click-to-reveal links
                        with st.expander("🔗 View Links"):
                            if hosted.startswith("http"):
                                st.markdown(f"🌐 **Hosted URL:** [Open File]({hosted})")
                            else:
                                st.caption("🌐 Hosted URL: `Setup Cloud Auth to access!`")

                            # if local:
                            #     st.markdown(f"💾 **Local Path:** `{local}`")
                                
                            #     # Convert local system path to API served endpoint
                            #     clean_local = local.split("data/")[-1] if "data/" in local else local
                            #     local_url = f"{BASE_URL}/data/{clean_local}"
                            #     st.markdown(f"📂 **Web View:** <a href='{local_url}' target='_blank'>Open in new tab</a>", unsafe_allow_html=True)
                            # else:
                            #     st.caption("💾 Local Path: `Not available`")

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
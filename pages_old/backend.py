import streamlit as st
import requests
import pandas as pd

BASE_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="Backend Checks", page_icon="📂", layout="wide")

with st.container(border=True): 
    st.header("📊 API Performance Logs")
    st.markdown("View performance metrics from your API")
    
    logs_url = st.text_input(
        "Performance CSV URL",
        value=f"{BASE_URL}/logs/api_performance.csv",
        help="URL to your api_performance.csv file"
    )
    
    if st.button("📈 Load Performance Data", type="primary"):
        with st.spinner("Loading performance logs..."):
            try:
                response = requests.get(logs_url)
                response.raise_for_status()
                
                # Parse CSV
                from io import StringIO
                csv_data = StringIO(response.text)
                df = pd.read_csv(csv_data)
                
                if not df.empty:
                    st.success(f"✅ Loaded {len(df)} log entries")
                    
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
                st.error(f"❌ Cannot access logs: {e.response.status_code}")
                st.info("Make sure your FastAPI server has the /logs path mounted")
            except Exception as e:
                st.error(f"❌ Error loading logs: {str(e)}")
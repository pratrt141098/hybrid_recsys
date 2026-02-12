import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import os

# Config: Check Streamlit Secrets -> Env Var -> Localhost
if "API_URL" in st.secrets:
    API_URL = st.secrets["API_URL"]
elif os.getenv("API_URL"):
    API_URL = os.getenv("API_URL")
else:
    API_URL = "http://localhost:8000/recommend"

st.set_page_config(page_title="Hybrid RecSys Admin", layout="wide")

# Sidebar: Simulation Controls
st.sidebar.header("User Simulation")
st.sidebar.caption(f"Backend: {API_URL}")  # Debug info

user_id = st.sidebar.number_input("Select User ID", min_value=1, max_value=1000, value=10)
use_llm = st.sidebar.checkbox("Enable LLM Re-Ranking", value=True)

if st.sidebar.button("Get Recommendations"):
    with st.spinner("Fetching recommendations from API..."):
        try:
            payload = {"user_id": user_id, "n_candidates": 10, "use_llm": use_llm}
            response = requests.post(API_URL, json=payload)
            
            # Error Handling: If non-200 response, show text
            if response.status_code != 200:
                st.error(f"API Error {response.status_code}: {response.text}")
                st.stop()
                
            data = response.json()

            # --- Main Content ---
            st.title(f"Shopping Assistant for User #{user_id}")

            # 1. User Profile Card
            if "profile" in data:
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Persona:** {data['profile'].get('persona', 'Unknown')}")
                with col2:
                    st.warning(f"**Recent History:** {data['profile'].get('recent_views', 'None')}")

            # 2. Recommendations Display
            st.subheader(f"Recommended Items ({data.get('strategy', 'Unknown Strategy')})")
            
            recs = data.get('recommendations', [])

            if use_llm and recs:
                # Display as cards
                for item in recs:
                    label = item.get('name', f"Product #{item.get('product_id')}")
                    with st.expander(f"🛒 {label}", expanded=True):
                        st.markdown(f"_{item.get('explanation', 'No explanation provided')}_")
                        st.caption(f"Product ID: {item.get('product_id')}")
            else:
                # Table fallback
                if recs:
                    st.table(pd.DataFrame(recs))
                else:
                    st.warning("No recommendations returned.")

            # 3. Analytics (Fake/Simulated for demo)
            st.markdown("---")
            st.subheader("Real-Time System Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("API Latency", "340ms", "-12ms")
            m2.metric("Conversion Prob", "24%", "+5%")
            m3.metric("Active Users", "1,240", "+12")

        except requests.exceptions.ConnectionError:
            st.error(f"Failed to connect to API at: {API_URL}")
            st.warning("Check if the Render service is awake (it may take 50s to start).")
        except Exception as e:
            st.error(f"Unexpected Error: {e}")
else:
    st.info("👈 Select a user and click 'Get Recommendations' to start.")

    # Landing page stats
    st.subheader("System Overview")
    chart_data = pd.DataFrame({
        'Model': ['Collaborative Filtering', 'Hybrid (LLM)', 'Random'],
        'CTR': [0.12, 0.23, 0.05]
    })
    fig = px.bar(chart_data, x='Model', y='CTR', title="A/B Test Performance (Click-Through Rate)", color='Model')
    st.plotly_chart(fig)

import streamlit as st
import requests
import pandas as pd
import plotly.express as px

# Config
API_URL = "http://localhost:8000/recommend"

st.set_page_config(page_title="Hybrid RecSys Admin", layout="wide")

# Sidebar: Simulation Controls
st.sidebar.header("User Simulation")
user_id = st.sidebar.number_input("Select User ID", min_value=1, max_value=1000, value=10)
use_llm = st.sidebar.checkbox("Enable LLM Re-Ranking", value=True)

if st.sidebar.button("Get Recommendations"):
    with st.spinner("Fetching recommendations from API..."):
        try:
            payload = {"user_id": user_id, "n_candidates": 10, "use_llm": use_llm}
            response = requests.post(API_URL, json=payload)
            data = response.json()
            
            # --- Main Content ---
            st.title(f"Shopping Assistant for User #{user_id}")
            
            # 1. User Profile Card
            if "profile" in data:
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"**Persona:** {data['profile']['persona']}")
                with col2:
                    st.warning(f"**Recent History:** {data['profile']['recent_views']}")
            
            # 2. Recommendations Display
            st.subheader(f"Recommended Items ({data['strategy']})")
            
            recs = data['recommendations']
            
            if use_llm:
                # Display as nice cards with explanations
                for item in recs:
                    with st.expander(f"🛒 {item.get('name', 'Product #' + str(item.get('product_id')))}", expanded=True):
                        st.markdown(f"_{item.get('explanation', 'No explanation provided')}_")
                        st.caption(f"Product ID: {item.get('product_id')}")
            else:
                # Display as simple table for ALS only
                df = pd.DataFrame(recs)
                st.table(df)

            # 3. Analytics (Fake/Simulated for demo)
            st.markdown("---")
            st.subheader("Real-Time System Metrics")
            m1, m2, m3 = st.columns(3)
            m1.metric("API Latency", "340ms", "-12ms")
            m2.metric("Conversion Prob", "24%", "+5%")
            m3.metric("Active Users", "1,240", "+12")

        except Exception as e:
            st.error(f"Error connecting to API: {e}")
            st.warning("Make sure the FastAPI server is running on port 8000!")

else:
    st.info("👈 Select a user and click 'Get Recommendations' to start.")
    
    # Landing page stats
    st.subheader("System Overview")
    
    # Just some dummy chart to look professional on landing
    chart_data = pd.DataFrame({
        'Model': ['Collaborative Filtering', 'Hybrid (LLM)', 'Random'],
        'CTR': [0.12, 0.23, 0.05]
    })
    fig = px.bar(chart_data, x='Model', y='CTR', title="A/B Test Performance (Click-Through Rate)", color='Model')
    st.plotly_chart(fig)

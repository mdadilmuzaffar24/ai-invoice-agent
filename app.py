import streamlit as st
import pandas as pd
import gspread
import os
import subprocess
from dotenv import load_dotenv

# ==========================================
# PAGE CONFIGURATION & STYLING
# ==========================================
load_dotenv()
st.set_page_config(page_title="AI-Ledger-Agent", page_icon="🧾", layout="wide")

# Custom CSS to make the button pop and smooth out the interface
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        border-radius: 8px;
        height: 55px;
        font-size: 20px;
        font-weight: 600;
        background-color: #2e66ff;
        color: white;
        transition: all 0.3s ease-in-out;
        border: none;
    }
    .stButton>button:hover {
        background-color: #1b4bcf;
        box-shadow: 0 6px 15px rgba(46, 102, 255, 0.3);
        transform: translateY(-2px);
    }
    .metric-container {
        display: flex;
        justify-content: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# CLOUD DATABASE CONNECTION
# ==========================================
@st.cache_data(ttl=10) # Refreshes data every 10 seconds
def load_ledger_data():
    try:
        credentials_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
        if not credentials_file:
            st.error("Missing Google Sheets credentials in .env file.")
            return pd.DataFrame()
            
        gc = gspread.service_account(filename=credentials_file)
        sheet = gc.open("AI_Ledger_Database").sheet1
        
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to connect to cloud database: {str(e)}")
        return pd.DataFrame()

# ==========================================
# STREAMLIT UI - DASHBOARD
# ==========================================
# Hero Section
st.markdown("<h1 style='text-align: center;'>🤖 AI-Ledger-Agent Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666; font-size: 18px; margin-bottom: 30px;'>Automated Deep Learning Financial Extraction Pipeline</p>", unsafe_allow_html=True)

# Sidebar Controls
with st.sidebar:
    st.header("⚙️ System Engine")
    st.write("Trigger the deterministic graph workflow to process staged invoices.")
    
    if st.button("🚀 Synchronize Database"):
        with st.spinner("Initializing AI-Ledger-Agent... routing through local inbox..."):
            try:
                # Executes the highly secure agent.py graph in the background
                subprocess.run(["uv", "run", "python", "agent.py"], check=True)
                st.success("✨ Synchronization Completed Successfully!")
                st.cache_data.clear() # Force dashboard to refresh and show new data
            except subprocess.CalledProcessError:
                st.error("Agent execution failed. Check terminal logs for rate-limit details.")

# Main Display Area
df = load_ledger_data()

if not df.empty:
    # Clean the data types for math operations
    df['total_amount'] = pd.to_numeric(df['total_amount'], errors='coerce').fillna(0)
    df['confidence_score'] = pd.to_numeric(df['confidence_score'], errors='coerce').fillna(0)
    
    # Generate Top-Level Analytics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Invoices Processed", len(df))
    with col2:
        st.metric("Total Value Extracted", f"₹ {df['total_amount'].sum():,.2f}")
    with col3:
        st.metric("Average AI Confidence", f"{df['confidence_score'].mean() * 100:.1f}%")

    st.write("")
    st.subheader("Live Ledger Database")
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("No data found in the ledger yet. Click 'Synchronize Database' to run the agent!")

# Footer
st.markdown("<br><hr><center><small>Powered by Gemini GenAI & Streamlit • Built by MD Adil Muzaffar</small></center>", unsafe_allow_html=True)
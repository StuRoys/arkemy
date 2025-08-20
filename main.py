# main.py - Application Entry Point (No Authentication)
import streamlit as st
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Arkemy: Turn Your Project Data Into Gold 🥇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# APPLICATION SETUP
# ==========================================

# Initialize global session state variables
if 'csv_loaded' not in st.session_state:
    st.session_state.csv_loaded = False
if 'transformed_df' not in st.session_state:
    st.session_state.transformed_df = None
if 'currency' not in st.session_state:
    st.session_state.currency = 'nok'  # Default to Norwegian krone
if 'currency_selected' not in st.session_state:
    st.session_state.currency_selected = False
if 'planned_csv_loaded' not in st.session_state:
    st.session_state.planned_csv_loaded = False
if 'transformed_planned_df' not in st.session_state:
    st.session_state.transformed_planned_df = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'data_loading_attempted' not in st.session_state:
    st.session_state.data_loading_attempted = False

# Initialize capacity-related session state variables
if 'schedule_loaded' not in st.session_state:
    st.session_state.schedule_loaded = False
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'absence_loaded' not in st.session_state:
    st.session_state.absence_loaded = False
if 'absence_df' not in st.session_state:
    st.session_state.absence_df = None
if 'capacity_config' not in st.session_state:
    st.session_state.capacity_config = None
if 'capacity_summary_loaded' not in st.session_state:
    st.session_state.capacity_summary_loaded = False
if 'capacity_summary_df' not in st.session_state:
    st.session_state.capacity_summary_df = None

# Set up app pages
pages = [
    st.Page("pages/1_Analytics_Dashboard.py", title="Analytics Dashboard", icon="📊"),
    st.Page("pages/2_Coworker_Report.py", title="Coworker Report", icon="👥"),
    st.Page("pages/3_Project_Report.py", title="Project Report", icon="📁"),
    st.Page("pages/4_Hrs_SQM_Phase.py", title="Hours / m2 (beta)", icon="🏗️"),
    st.Page("pages/5_Admin.py", title="Admin", icon="🛠️")
]

# Set up navigation - this creates the sidebar automatically
pg = st.navigation(pages)

# Run the application
pg.run()
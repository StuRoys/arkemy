# main.py - Application Entry Point and Orchestration
import streamlit as st

# Set global app configuration
st.set_page_config(
    page_title="Arkemy: Turn Your Project Data Into Gold 🥇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
if 'show_uploader' not in st.session_state:
    st.session_state.show_uploader = False

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

# Hide main page from sidebar navigation (replicates your manual DOM edit)
st.markdown("""
<style>
    /* Target first navigation item (main is typically first) */
    section[data-testid="stSidebar"] ul li:first-child span {
        font-size: 0 !important;
        visibility: hidden !important;
    }
    
    /* Also target by partial class match since emotion classes can change */
    section[data-testid="stSidebar"] span[class*="st-emotion-cache-a8ha1g"] {
        font-size: 0 !important;
        visibility: hidden !important;
    }
</style>
""", unsafe_allow_html=True)

# Auto-redirect to Analytics Dashboard (default landing page)
st.switch_page("pages/1_Analytics_Dashboard.py")
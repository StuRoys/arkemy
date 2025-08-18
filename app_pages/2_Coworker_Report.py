import streamlit as st

# ==========================================
# AUTHENTICATION CHECK - MUST COME FIRST
# ==========================================

# Check if user is authenticated
authentication_status = st.session_state.get('authentication_status')
if authentication_status != True:
    # User is not authenticated - redirect to main page
    st.error("🔒 Access denied. Please log in through the main page.")
    st.markdown("[👉 Go to Login Page](/?page=main)")
    st.stop()

# Set page configuration for consistent layout
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

from period_translations.translations import initialize_translations, t, load_translations
from period_processors.coworker_report import handle_coworker_upload

# Initialize English translations as default
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'translations' not in st.session_state:
    st.session_state.translations = load_translations('en')

# Session state for coworker data (namespaced to avoid conflicts)
if 'period_report_coworker_data' not in st.session_state:
    st.session_state.period_report_coworker_data = None

# Temporary mapping for backward compatibility with period_report code
st.session_state.coworker_data = st.session_state.period_report_coworker_data

# Create sidebar with data controls only
with st.sidebar:
    # Clear data button for coworker data
    if st.session_state.coworker_data is not None:
        if st.button("Clear uploaded coworker data", use_container_width=True):
            st.session_state.coworker_data = None
            st.rerun()

# Main content
st.header(t("title_coworker_report"))

# Handle coworker upload and rendering (sidebar will be populated by the processor)
filtered_period_info, selected_person = handle_coworker_upload()
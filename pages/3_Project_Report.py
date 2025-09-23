import streamlit as st

# Set page configuration for consistent layout
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

from period_translations.translations import initialize_translations, t, load_translations
from period_processors.project_report import handle_project_upload

# Initialize English translations as default
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'translations' not in st.session_state:
    st.session_state.translations = load_translations('en')

# Session state for project data (namespaced to avoid conflicts)
if 'period_report_project_data' not in st.session_state:
    st.session_state.period_report_project_data = None

# Temporary mapping for backward compatibility with period_report code
st.session_state.project_data = st.session_state.period_report_project_data

# Main content
# Header removed for cleaner UI - page title is already visible in navigation

# Handle project upload and rendering (sidebar will be populated by the processor)
handle_project_upload()
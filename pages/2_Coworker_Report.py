import streamlit as st

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

# Bidirectional sync - preserve data from either source
if st.session_state.period_report_coworker_data is not None:
    st.session_state.coworker_data = st.session_state.period_report_coworker_data
elif st.session_state.get('coworker_data') is not None:
    st.session_state.period_report_coworker_data = st.session_state.coworker_data
else:
    st.session_state.coworker_data = None

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
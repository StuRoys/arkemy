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

# Check if coworker data is available
if not st.session_state.get('coworker_available', False):
    st.error("📂 Coworker Report data not available")
    st.info("Please select a dataset that includes a coworker CSV file.")
    st.stop()

# Session state for coworker data (namespaced to avoid conflicts)
if 'period_report_coworker_data' not in st.session_state:
    st.session_state.period_report_coworker_data = None

# Load data from global CSV path if not already loaded
if st.session_state.period_report_coworker_data is None:
    csv_path = st.session_state.get('coworker_csv_path')
    if csv_path:
        try:
            import pandas as pd
            st.session_state.period_report_coworker_data = pd.read_csv(csv_path)
            st.session_state.coworker_data = st.session_state.period_report_coworker_data
        except Exception as e:
            st.error(f"Failed to load coworker data: {str(e)}")
            st.stop()
    else:
        st.error("Coworker CSV path not found in session state")
        st.stop()

# Bidirectional sync - preserve data from either source
if st.session_state.period_report_coworker_data is not None:
    st.session_state.coworker_data = st.session_state.period_report_coworker_data
elif st.session_state.get('coworker_data') is not None:
    st.session_state.period_report_coworker_data = st.session_state.coworker_data
else:
    st.session_state.coworker_data = None

# Sidebar will be populated by the processor

# Main content
st.subheader(t("title_coworker_report"))

# Handle coworker upload and rendering (sidebar will be populated by the processor)
filtered_period_info, selected_person = handle_coworker_upload()
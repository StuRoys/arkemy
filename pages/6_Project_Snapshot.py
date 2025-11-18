import streamlit as st

# Set page configuration for consistent layout
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

from period_translations.translations import initialize_translations, t, load_translations
from period_processors.project_report import (
    render_project_sidebar_filters,
    transform_parquet_to_project_report
)
from period_charts.project_snapshot import render_project_snapshot
from utils.localhost_selector import is_localhost, render_localhost_file_selector
import pandas as pd

# Initialize English translations as default
if 'language' not in st.session_state:
    st.session_state.language = 'en'
if 'translations' not in st.session_state:
    st.session_state.translations = load_translations('en')

# Session state for project data (shared with Project Report)
if 'period_report_project_data' not in st.session_state:
    st.session_state.period_report_project_data = None

# Temporary mapping for backward compatibility with period_report code
st.session_state.project_data = st.session_state.period_report_project_data

# Main content
st.subheader("🔍 " + t("snapshot_project").title())

# Check if we're on localhost and offer file selector
if is_localhost():
    with st.sidebar.expander("📂 Data Source (Localhost Only)", expanded=False):
        data_path = render_localhost_file_selector()

        if data_path and st.button("Load Selected File"):
            try:
                # Transform and load the data
                project_df = transform_parquet_to_project_report(data_path)
                st.session_state.period_report_project_data = project_df
                st.success(f"Loaded data from {data_path}")
                st.rerun()
            except Exception as e:
                st.error(f"Error loading data: {str(e)}")

# Check if data is loaded
if st.session_state.period_report_project_data is None:
    st.info("👆 Please load project data using the sidebar to view the snapshot.")
    st.stop()

# Get the project data
project_df = st.session_state.period_report_project_data

# Ensure Period column is datetime
if "Period" in project_df.columns:
    try:
        project_df["Period"] = pd.to_datetime(project_df["Period"])
    except Exception as e:
        st.warning(f"Could not convert Period to datetime: {str(e)}")

# Apply sidebar filters
filtered_df, filtered_period_info, selected_project = render_project_sidebar_filters(project_df)

# Get the translated "All Projects" option
all_projects_option = t('filter_all_projects')

# Render the snapshot view
render_project_snapshot(filtered_df, selected_project, all_projects_option)

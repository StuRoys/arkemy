import streamlit as st

# Set page configuration for consistent layout
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

from period_translations.translations import t, load_translations
from period_processors.project_report import try_autoload_project_data
from period_charts.project_snapshot import render_project_snapshot
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

# Check if data already exists in session state
if st.session_state.project_data is None:
    # First, check if global transformed_df is available (from dataset selection)
    if st.session_state.get('csv_loaded', False) and st.session_state.transformed_df is not None:
        # Import transformation function
        from period_processors.project_report import transform_dataframes_to_project_report

        # Transform global data to project report format
        time_records = st.session_state.transformed_df
        planned_records = st.session_state.get('transformed_planned_df')

        transformed_data = transform_dataframes_to_project_report(time_records, planned_records)

        if transformed_data is not None:
            # Store transformed data in session state
            st.session_state.project_data = transformed_data
            st.session_state.period_report_project_data = transformed_data
            project_df = transformed_data
        else:
            st.error("Failed to transform global data to project report format")
            st.stop()
    else:
        # Fallback: Try to autoload data (for production or if global data not available)
        autoloaded_data = try_autoload_project_data()

        if autoloaded_data is not None:
            # Store autoloaded data in session state
            st.session_state.project_data = autoloaded_data
            st.session_state.period_report_project_data = autoloaded_data
            project_df = autoloaded_data
        else:
            # No data found - show error message
            st.error("📂 No project data available")
            st.info("Please load a dataset using the 'Change Dataset' button in the sidebar.")
            st.stop()
else:
    # Use existing data from session state
    project_df = st.session_state.project_data

# Check required columns
project_columns = [
    "Project ID", "Project Name", "Period", "Period Hours", "Billable Hours",
    "Planned Hours", "Period Fees Adjusted", "Planned Income"
]

missing_columns = [col for col in project_columns if col not in project_df.columns]

if missing_columns:
    st.warning(f"{t('filter_missing_columns')} {', '.join(missing_columns)}")
    st.stop()

# Ensure Period column is datetime
if "Period" in project_df.columns:
    try:
        project_df["Period"] = pd.to_datetime(project_df["Period"], errors='coerce')
        # Check if conversion was successful
        if project_df["Period"].isna().all():
            st.warning("Could not convert any Period values to datetime format")
            project_df["Period"] = pd.Timestamp.now()
    except Exception as e:
        st.warning(f"Could not convert Period to datetime: {str(e)}")
        project_df["Period"] = pd.Timestamp.now()

# Get the translated "All Projects" option
all_projects_option = t('filter_all_projects')

# Render the snapshot view (no sidebar filters - period selection is in the UI)
render_project_snapshot(project_df, all_projects_option, all_projects_option)

"""
Dataset Reset Utility

Provides functionality to display current dataset and reset button for localhost mode.
"""

import streamlit as st
import os
from utils.localhost_selector import is_localhost


def render_dataset_indicator():
    """
    Render dataset reset button in sidebar (localhost only).

    Provides a button to change datasets by clearing session state
    and returning to selection screen.

    Only renders when in localhost mode. Does nothing in production.
    Should be called at the END of sidebar rendering to appear below filters.
    """
    # Only show in localhost mode
    if not is_localhost():
        return

    # Only show if data is loaded
    if not st.session_state.get('csv_loaded', False):
        return

    # Reset button (appears wherever this function is called in sidebar flow)
    if st.sidebar.button("🔄 Change Dataset", use_container_width=True, key="dataset_reset_btn"):
        clear_dataset_session_state()
        st.rerun()


def clear_dataset_session_state():
    """
    Clear all dataset-related session state variables.

    This includes:
    - Time records data (actual)
    - Planned records data (forecasting)
    - Loaded file path
    - Currency settings
    - Tag mappings
    - Reference data
    """
    # Clear time records (actual data)
    st.session_state.csv_loaded = False
    st.session_state.transformed_df = None

    # Clear planned records (forecasting data)
    st.session_state.planned_csv_loaded = False
    st.session_state.transformed_planned_df = None

    # Clear file tracking
    if 'loaded_file_path' in st.session_state:
        del st.session_state.loaded_file_path

    # Reset currency to default
    st.session_state.currency = 'nok'
    st.session_state.currency_selected = False

    # Clear tag mappings
    if 'tag_mappings' in st.session_state:
        del st.session_state.tag_mappings

    # Clear reference data
    if 'person_reference_df' in st.session_state:
        st.session_state.person_reference_df = None
    if 'project_reference_df' in st.session_state:
        st.session_state.project_reference_df = None

    # Clear period report data (if any)
    if 'period_report_project_data' in st.session_state:
        st.session_state.period_report_project_data = None
    if 'period_report_coworker_data' in st.session_state:
        st.session_state.period_report_coworker_data = None
    if 'project_data' in st.session_state:
        st.session_state.project_data = None
    if 'coworker_data' in st.session_state:
        st.session_state.coworker_data = None

    # Clear CSV availability flags and paths
    if 'coworker_available' in st.session_state:
        st.session_state.coworker_available = False
    if 'coworker_csv_path' in st.session_state:
        st.session_state.coworker_csv_path = None
    if 'sqm_available' in st.session_state:
        st.session_state.sqm_available = False
    if 'sqm_csv_path' in st.session_state:
        st.session_state.sqm_csv_path = None
    if 'sqm_data' in st.session_state:
        st.session_state.sqm_data = None

    # Reset data loading flag
    st.session_state.data_loading_attempted = False


def get_current_dataset_name():
    """
    Get the name of the currently loaded dataset.

    Returns:
        str: Filename of current dataset, or None if no dataset loaded
    """
    if not is_localhost():
        return None

    loaded_file_path = st.session_state.get('loaded_file_path', None)
    if loaded_file_path:
        return os.path.basename(loaded_file_path)

    return None

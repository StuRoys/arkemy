import streamlit as st
import pandas as pd
from period_translations.translations import t
from period_utils.chart_utils import prepare_project_dataframe


def render_project_snapshot(df, selected_project, all_projects_option="All Projects"):
    """Render a snapshot overview of project performance."""
    # Check required columns
    required_columns = ["Period", "Project Name", "Period Hours", "Planned Hours"]
    missing_columns = [col for col in required_columns if col not in df.columns]

    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return

    if selected_project != all_projects_option:
        render_single_project_snapshot(df, selected_project)
    else:
        render_all_projects_snapshot(df)


def render_single_project_snapshot(df, project_name):
    """Render snapshot for a single project."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)

    # Filter data for selected project
    filtered_df = df_copy[df_copy["Project Name"] == project_name].sort_values("Period")

    # Return if no data
    if filtered_df.empty:
        st.warning(f"No data found for project: {project_name}")
        return

    st.info("Project snapshot view - coming soon")


def render_all_projects_snapshot(df):
    """Render snapshot overview for all projects."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)

    # Return if no data
    if df_copy.empty:
        st.warning("No data available for the selected period")
        return

    st.info("Project snapshot view - coming soon")

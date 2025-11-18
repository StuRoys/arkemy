import streamlit as st
import pandas as pd
import altair as alt
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

    st.info("💡 Switch to 'All Projects' in the sidebar to use the snapshot comparison view")


def render_all_projects_snapshot(df):
    """Render snapshot overview for all projects."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)

    # Return if no data
    if df_copy.empty:
        st.warning("No data available for the selected period")
        return

    # Get unique projects sorted by total hours (descending)
    project_totals = df_copy.groupby("Project Name")["Period Hours"].sum().sort_values(ascending=False)
    available_projects = project_totals.index.tolist()

    # Create Stockpeer-style layout: left cell (selector) + right cell (chart)
    cols = st.columns([1, 3])

    # LEFT CELL: Project and period selectors
    left_cell = cols[0].container(
        border=True,
        height=500,
        vertical_alignment="top"
    )

    with left_cell:
        st.markdown("### Period")

        # Period selection buttons (Stockpeer-style)
        period_options = {
            "3M": 3,
            "6M": 6,
            "YTD": "ytd",
            "1Y": 12,
            "All": "all"
        }

        # Create radio buttons for period selection
        selected_period_key = st.radio(
            "Select time period",
            options=list(period_options.keys()),
            index=3,  # Default to 1Y
            horizontal=True,
            label_visibility="collapsed"
        )

        selected_period_value = period_options[selected_period_key]

        st.markdown("---")
        st.markdown("### Projects")

        # Add "All projects" option
        all_projects_label = "All projects (aggregated)"

        # Default to top 5 projects
        default_projects = available_projects[:5] if len(available_projects) >= 5 else available_projects

        # Multiselect with all available projects
        selected_projects = st.multiselect(
            "Compare projects",
            options=[all_projects_label] + available_projects,
            default=default_projects,
            placeholder="Choose projects to compare",
            label_visibility="collapsed"
        )

    # RIGHT CELL: Chart
    right_cell = cols[1].container(
        border=True,
        height=500,
        vertical_alignment="center"
    )

    with right_cell:
        # Handle selection
        if not selected_projects:
            st.info("👆 Select at least one project to view the chart")
            return

        # Apply period filter
        if selected_period_value != "all":
            max_period = df_copy["Period"].max()

            if selected_period_value == "ytd":
                # Year to date - from January 1st to max_period
                start_of_year = pd.Timestamp(max_period.year, 1, 1)
                df_copy = df_copy[df_copy["Period"] >= start_of_year]
            else:
                # Months back (3M, 6M, 1Y)
                months_back = selected_period_value
                start_period = max_period - pd.DateOffset(months=months_back)
                df_copy = df_copy[df_copy["Period"] >= start_period]

        # Check if "All projects" is selected
        if all_projects_label in selected_projects:
            # Aggregate all projects
            plot_data = df_copy.groupby("Period", as_index=False)["Period Hours"].sum()
            plot_data["Project Name"] = "All projects"
        else:
            # Filter for selected projects
            plot_data = df_copy[df_copy["Project Name"].isin(selected_projects)].copy()

        # Sort by period for chronological display
        plot_data = plot_data.sort_values("Period")

        # Create Altair line chart
        chart = (
            alt.Chart(plot_data)
            .mark_line(point=True)
            .encode(
                alt.X("Period:T", title="Period", axis=alt.Axis(format="%b %Y")),
                alt.Y("Period Hours:Q", title="Hours Worked", scale=alt.Scale(zero=False)),
                alt.Color("Project Name:N", title="Project"),
                tooltip=["Period:T", "Project Name:N", "Period Hours:Q"]
            )
            .properties(
                height=400,
                title="Period Hours by Project"
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)

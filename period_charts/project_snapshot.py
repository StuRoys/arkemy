import streamlit as st
import pandas as pd
import numpy as np
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

    # Get unique projects sorted alphabetically
    available_projects = sorted(df_copy["Project Name"].unique())

    # Create Stockpeer-style layout: left cell (selector) + right cell (chart)
    cols = st.columns([1, 3])

    # LEFT CELL: Project and period selectors
    left_cell = cols[0].container(
        border=True,
        height=600,
        vertical_alignment="top"
    )

    with left_cell:
        st.markdown("### Projects")

        # Add "All projects" option
        all_projects_label = "All projects (aggregated)"

        # Empty default selection
        selected_projects = st.multiselect(
            "Compare projects",
            options=[all_projects_label] + available_projects,
            default=[],
            placeholder="Choose projects to compare",
            label_visibility="collapsed"
        )

        st.markdown("### Metric")

        # Metric configuration: display label → (column/calculation, y-axis title, format)
        metric_options = {
            "Hrs used": ("Period Hours", "Hours", "hours"),
            "Hrs bill.": ("Billable Hours", "Hours", "hours"),
            "Hrs %": ("billability", "Billability %", "percent"),
            "Fees": ("Period Fees Adjusted", "Fees", "currency"),
            "$/hr eff.": ("effective_rate", "Effective Rate", "rate"),
            "$/hr avg.": ("billable_rate", "Billable Rate", "rate")
        }

        selected_metric_key = st.pills(
            "Metric",
            options=list(metric_options.keys()),
            default="Hrs used",
            label_visibility="collapsed"
        )

        metric_col, y_title, metric_format = metric_options[selected_metric_key]

        st.markdown("### Period")

        # Period selection buttons (Stockpeer-style)
        period_options = {
            "1M": 1,
            "3M": 3,
            "6M": 6,
            "YTD": "ytd",
            "1Y": 12,
            "All": "all"
        }

        # Create pill buttons for period selection (Stockpeer-style)
        selected_period_key = st.pills(
            "Period",
            options=list(period_options.keys()),
            default="1Y",
            label_visibility="collapsed"
        )

        selected_period_value = period_options[selected_period_key]

    # RIGHT CELL: Chart
    right_cell = cols[1].container(
        border=True,
        height=600,
        vertical_alignment="center"
    )

    with right_cell:
        # Handle selection
        if not selected_projects:
            st.info("Select one or more projects to view chart")
            return

        # Apply period filter
        if selected_period_value != "all":
            max_period = df_copy["Period"].max()

            if selected_period_value == "ytd":
                # Year to date - from January 1st to max_period
                start_of_year = pd.Timestamp(max_period.year, 1, 1)
                df_copy = df_copy[df_copy["Period"] >= start_of_year]
            else:
                # Months back (1M, 3M, 6M, 1Y)
                months_back = selected_period_value
                start_period = max_period - pd.DateOffset(months=months_back)
                df_copy = df_copy[df_copy["Period"] >= start_period]

        # Calculate derived metrics if needed
        if metric_col in ["billability", "effective_rate", "billable_rate"]:
            if metric_col == "billability":
                # Billability % = (Billable Hours / Period Hours) * 100
                df_copy["billability"] = (df_copy["Billable Hours"] / df_copy["Period Hours"]) * 100
                df_copy["billability"] = df_copy["billability"].fillna(0).replace([np.inf, -np.inf], 0)
            elif metric_col == "effective_rate":
                # Effective rate = Fees / Period Hours
                df_copy["effective_rate"] = df_copy["Period Fees Adjusted"] / df_copy["Period Hours"]
                df_copy["effective_rate"] = df_copy["effective_rate"].fillna(0).replace([np.inf, -np.inf], 0)
            elif metric_col == "billable_rate":
                # Billable rate = Fees / Billable Hours
                df_copy["billable_rate"] = df_copy["Period Fees Adjusted"] / df_copy["Billable Hours"]
                df_copy["billable_rate"] = df_copy["billable_rate"].fillna(0).replace([np.inf, -np.inf], 0)

        # Check if "All projects" is selected
        if all_projects_label in selected_projects:
            # Aggregate all projects
            agg_dict = {"Period Hours": "sum", "Billable Hours": "sum", "Period Fees Adjusted": "sum"}

            plot_data = df_copy.groupby("Period", as_index=False).agg(agg_dict)
            plot_data["Project Name"] = "All projects"

            # Recalculate derived metrics after aggregation
            if metric_col == "billability":
                plot_data["billability"] = (plot_data["Billable Hours"] / plot_data["Period Hours"]) * 100
                plot_data["billability"] = plot_data["billability"].fillna(0).replace([np.inf, -np.inf], 0)
            elif metric_col == "effective_rate":
                plot_data["effective_rate"] = plot_data["Period Fees Adjusted"] / plot_data["Period Hours"]
                plot_data["effective_rate"] = plot_data["effective_rate"].fillna(0).replace([np.inf, -np.inf], 0)
            elif metric_col == "billable_rate":
                plot_data["billable_rate"] = plot_data["Period Fees Adjusted"] / plot_data["Billable Hours"]
                plot_data["billable_rate"] = plot_data["billable_rate"].fillna(0).replace([np.inf, -np.inf], 0)
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
                alt.Y(f"{metric_col}:Q", title=y_title, scale=alt.Scale(zero=False)),
                alt.Color("Project Name:N", title="Project"),
                tooltip=["Period:T", "Project Name:N", f"{metric_col}:Q"]
            )
            .properties(
                height=500,
                title=f"{selected_metric_key} by Project"
            )
            .interactive()
        )

        st.altair_chart(chart, use_container_width=True)

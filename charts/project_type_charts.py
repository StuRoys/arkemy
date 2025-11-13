# project_type_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options
from utils.processors import get_project_tag_columns, aggregate_by_project_tag, get_project_tag_columns_with_labels
from utils.tag_manager import get_tag_display_name

def get_widget_key(base_key: str, nav_context: str = "project_types") -> str:
    """Generate stable widget keys for project type charts"""
    # Use static keys to preserve widget state across reruns
    return f"{nav_context}_{base_key}"

def render_project_type_tab(filtered_df, aggregate_by_project_type, render_chart, get_category_colors):
    """
    Renders the project type analysis tab with visualizations and metrics.

    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project_type: Function to aggregate data by project type (deprecated, kept for compatibility)
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Get available project tag columns
    available_tags = get_project_tag_columns(filtered_df)

    if not available_tags:
        st.warning("Project tag information is not available in the data.")
        return

    # Get tag mappings from session state (populated by unified_data_loader)
    tag_mappings = st.session_state.get('tag_mappings', {})

    # Get available project tags with labels
    tag_columns_with_labels = get_project_tag_columns_with_labels(filtered_df, tag_mappings)

    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)

    # Create columns for horizontal alignment (3 columns)
    col1, col2, col3 = st.columns(3)

    with col1:
        # Tag dimension selector - only show if multiple tags exist
        if len(available_tags) > 1:
            # Use column names as values, but display labels to user via format_func
            selected_tag_column = st.selectbox(
                label="",
                options=available_tags,
                format_func=lambda col: tag_columns_with_labels.get(col, col),
                index=0,
                key=get_widget_key("tag_selector")
            )
        else:
            # Only one tag available, use it automatically
            selected_tag_column = available_tags[0]

    with col2:
        selected_metric = st.selectbox(
            label="",
            options=metric_options,
            index=0,  # Default to Hours worked
            key=get_widget_key("metric_selector")
        )

    with col3:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]

        visualization_type = st.selectbox(
            label="",
            options=visualization_options,
            index=0,  # Default to Treemap
            key=get_widget_key("visualization_selector")
        )

    # Get display label for selected tag column
    selected_tag_display_name = get_tag_display_name(selected_tag_column, tag_mappings)

    # Aggregate by selected project tag - this will be used for all visualizations
    project_type_agg = aggregate_by_project_tag(filtered_df, tag_column=selected_tag_column)

    # Check if we have any data after aggregation
    if project_type_agg.empty:
        st.error("No project type data available after filtering.")
        return

    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"
    
    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_project_type_agg = project_type_agg[project_type_agg[metric_column] != 0]
    else:
        filtered_project_type_agg = project_type_agg[project_type_agg[metric_column] > 0]
    
    # Show warning if some project types were filtered out
    if len(filtered_project_type_agg) < len(project_type_agg):
        excluded_count = len(project_type_agg) - len(filtered_project_type_agg)
        if "profit" in selected_metric.lower():
            st.warning(f"{excluded_count} project types with zero {selected_metric} were excluded from visualization.")
        else:
            st.warning(f"{excluded_count} project types with zero {selected_metric} were excluded from visualization.")
    
    # Render visualization based on type
    if not filtered_project_type_agg.empty:
        if visualization_type == "Treemap":
            # Project type treemap with standardized custom data
            fig = px.treemap(
                filtered_project_type_agg,
                path=[selected_tag_column],
                values=metric_column,
                color=metric_column,
                color_continuous_scale="Greens",
                custom_data=create_standardized_customdata(filtered_project_type_agg),
                title=f"{selected_tag_display_name} {selected_metric} Distribution"
            )
            render_chart(fig, "project_type")

        elif visualization_type == "Bar chart":
            # Sort project types by selected metric in descending order
            sorted_project_types = project_type_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of project types to display (only if 10+ items)
            if len(project_type_agg) >= 10:
                num_project_types = st.slider(
                    label="",
                    min_value=1,
                    max_value=min(1000, len(project_type_agg)),
                    value=min(10, len(project_type_agg)),
                    step=1,
                    key=get_widget_key("count_slider")
                )
                # Limit the number of project types based on slider
                limited_project_types = sorted_project_types.head(num_project_types)
            else:
                # If fewer than 10 items, show all
                limited_project_types = sorted_project_types

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_project_types,
                x=selected_tag_column,
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Greens",
                title=f"{selected_metric} by {selected_tag_display_name}",
                custom_data=create_standardized_customdata(limited_project_types)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart
            render_chart(fig_bar, "project_type")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No project types have non-zero values for {selected_metric}.")
        else:
            st.error(f"No project types have values greater than zero for {selected_metric}.")

    # Display project type data table with all metrics
    st.subheader(f"Data for {selected_tag_display_name}")

    # Sort by hours worked in descending order
    sorted_project_type_agg = project_type_agg.sort_values("hours_used", ascending=False)

    # Use the column configuration from chart_styles
    from utils.chart_styles import create_column_config

    # Display the table with column configurations
    st.dataframe(
        sorted_project_type_agg,
        use_container_width=True,
        hide_index=True,
        column_config=create_column_config(sorted_project_type_agg)
    )
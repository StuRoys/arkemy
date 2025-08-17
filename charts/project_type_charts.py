# project_type_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def get_widget_key(base_key: str, nav_context: str = "project_types") -> str:
    """Generate navigation-specific widget keys for project type charts"""
    # Include navigation counter to force widget recreation on tab switch
    counter = st.session_state.get('project_nav_counter', 0)
    return f"{nav_context}_{base_key}_{counter}"

def render_project_type_tab(filtered_df, aggregate_by_project_type, render_chart, get_category_colors):
    """
    Renders the project type analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project_type: Function to aggregate data by project type
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Check if Project type column exists
    if "project_tag" not in filtered_df.columns:
        st.warning("Project type information is not available in the data.")
        return
    
    # Aggregate by project type first - this will be used for all visualizations
    project_type_agg = aggregate_by_project_type(filtered_df)
    
    # Check if we have any data after aggregation
    if project_type_agg.empty:
        st.error("No project type data available after filtering.")
        return
    
    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)
    
    # Create columns for horizontal alignment
    col1, col2 = st.columns(2)
    
    with col1:
        selected_metric = st.selectbox(
            "Select metric to visualize:",
            options=metric_options,
            index=0,  # Default to Hours worked
            key=get_widget_key("metric_selector")
        )
    
    with col2:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]
        
        visualization_type = st.radio(
            "Visualization type:",
            options=visualization_options,
            index=0,  # Default to Treemap
            key=get_widget_key("visualization_selector"),
            horizontal=True
        )
    
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
                path=["project_tag"],
                values=metric_column,
                color=metric_column,
                color_continuous_scale="Greens",
                custom_data=create_standardized_customdata(filtered_project_type_agg),
                title=f"Project Type {selected_metric} Distribution"
            )
            render_chart(fig, "project_type")
        
        elif visualization_type == "Bar chart":
            # Sort project types by selected metric in descending order
            sorted_project_types = project_type_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of project types to display
            if len(project_type_agg) > 1:
                num_project_types = st.slider(
                    "Number of project types to display:",
                    min_value=1,
                    max_value=min(1000, len(project_type_agg)),
                    value=min(10, len(project_type_agg)),
                    step=1,
                    key=get_widget_key("count_slider")
                )
                # Limit the number of project types based on slider
                limited_project_types = sorted_project_types.head(num_project_types)
            else:
                # If only one project type, no need for slider
                limited_project_types = sorted_project_types

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_project_types,
                x="project_tag",
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Greens",
                title=f"{selected_metric} by Project Type",
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
    st.subheader("Project Type Data Table")
    
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
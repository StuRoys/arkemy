# activity_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata, create_single_metric_chart
from utils.chart_styles import get_metric_options, initialize_analytics_metric_state

def render_activity_tab(filtered_df, aggregate_by_activity, render_chart, get_category_colors):
    """
    Renders the activity analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_activity: Function to aggregate data by activity
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Check if Activity column exists
    if "activity_tag" in filtered_df.columns:
        # Initialize shared metric state (persists across tabs)
        initialize_analytics_metric_state()

        # Get metric options from centralized function
        metric_options = get_metric_options(has_planned_data=False)

        # Get current index from session state (with fallback if metric not in options)
        try:
            current_metric_index = metric_options.index(st.session_state.analytics_selected_metric)
        except ValueError:
            current_metric_index = 0  # Fallback to first option if current selection not available

        # Create columns for horizontal alignment
        col1, col2 = st.columns(2)

        with col1:
            selected_metric = st.selectbox(
                label="Metric",
                label_visibility="collapsed",
                options=metric_options,
                index=current_metric_index,
                key="activity_metric_selector"
            )
            st.session_state.analytics_selected_metric = selected_metric

        with col2:
            # Add visualization type selection
            visualization_options = ["Treemap", "Bar chart"]

            visualization_type = st.selectbox(
                label="Chart type",
                label_visibility="collapsed",
                options=visualization_options,
                index=0,  # Default to Treemap
                key="activity_visualization_selector"
            )
        
        # Translate display names to column names if needed
        metric_column = selected_metric
        if selected_metric == "Hours worked":
            metric_column = "hours_used"
        elif selected_metric == "Billable hours":
            metric_column = "hours_billable"
        
        # Aggregate by activity
        activity_agg = aggregate_by_activity(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_activity_agg = activity_agg[activity_agg[metric_column] != 0]
        else:
            filtered_activity_agg = activity_agg[activity_agg[metric_column] > 0]

        # Render visualization based on type
        if not filtered_activity_agg.empty:
            if visualization_type == "Treemap":
                # Use centralized helper function for consistent treemap rendering
                fig = create_single_metric_chart(
                    filtered_activity_agg,
                    metric_column,
                    title="",
                    chart_type="treemap",
                    x_field="activity_tag"
                )
                render_chart(fig, "activity")
            
            elif visualization_type == "Bar chart":
                # Sort activities by selected metric in descending order
                sorted_activities = activity_agg.sort_values(metric_column, ascending=False)

                # Add a slider to control number of activities to display
                if len(activity_agg) > 1:
                    num_activities = st.slider(
                        "Number of activities to display:",
                        min_value=1,
                        max_value=min(1000, len(activity_agg)),
                        value=min(10, len(activity_agg)),
                        step=1,
                        key="activity_count_slider"
                    )
                    # Limit the number of activities based on slider
                    limited_activities = sorted_activities.head(num_activities)
                else:
                    # If only one activity, no need for slider
                    limited_activities = sorted_activities

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_activities,
                    x="activity_tag",
                    y=metric_column,
                    color=metric_column,
                    color_continuous_scale="Reds",
                    title=f"{selected_metric} by Activity",
                    custom_data=create_standardized_customdata(limited_activities)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "activity")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No activities have non-zero values for {selected_metric}.")
            else:
                st.error(f"No activities have values greater than zero for {selected_metric}.")

        # Display activity data table with all metrics in an expander
        with st.expander("Details"):
            # Sort by hours worked in descending order
            sorted_activity_agg = activity_agg.sort_values("hours_used", ascending=False)

            # Use the column configuration from chart_styles
            from utils.chart_styles import create_column_config

            # Display the table with column configurations
            st.dataframe(
                sorted_activity_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_activity_agg)
            )
    else:
        st.warning("Activity information is not available in the data.")
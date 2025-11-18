# phase_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata, create_single_metric_chart
from utils.chart_styles import get_metric_options, initialize_analytics_metric_state

def render_phase_tab(filtered_df, aggregate_by_phase, render_chart, get_category_colors):
    """
    Renders the phase analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_phase: Function to aggregate data by phase
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Check if Phase column exists
    if "phase_tag" in filtered_df.columns:
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
                key="phase_metric_selector"
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
                key="phase_visualization_selector"
            )
        
        # Translate display names to column names if needed
        metric_column = selected_metric
        if selected_metric == "Hours worked":
            metric_column = "hours_used"
        elif selected_metric == "Billable hours":
            metric_column = "hours_billable"
        
        # Aggregate by phase
        phase_agg = aggregate_by_phase(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_phase_agg = phase_agg[phase_agg[metric_column] != 0]
        else:
            filtered_phase_agg = phase_agg[phase_agg[metric_column] > 0]

        # Render visualization based on type
        if not filtered_phase_agg.empty:
            if visualization_type == "Treemap":
                # Use centralized helper function for consistent treemap rendering
                fig = create_single_metric_chart(
                    filtered_phase_agg,
                    metric_column,
                    title="",
                    chart_type="treemap",
                    x_field="phase_tag"
                )
                render_chart(fig, "phase")
            
            elif visualization_type == "Bar chart":
                # Sort phases by selected metric in descending order
                sorted_phases = phase_agg.sort_values(metric_column, ascending=False)

                # Add a slider to control number of phases to display
                if len(phase_agg) > 1:
                    num_phases = st.slider(
                        "Number of phases to display:",
                        min_value=1,
                        max_value=min(1000, len(phase_agg)),
                        value=min(10, len(phase_agg)),
                        step=1,
                        key="phase_count_slider"
                    )
                    # Limit the number of phases based on slider
                    limited_phases = sorted_phases.head(num_phases)
                else:
                    # If only one phase, no need for slider
                    limited_phases = sorted_phases

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_phases,
                    x="phase_tag",
                    y=metric_column,
                    color=metric_column,
                    color_continuous_scale="Purples",
                    title=f"{selected_metric} by Phase",
                    custom_data=create_standardized_customdata(limited_phases)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "phase")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No phases have non-zero values for {selected_metric}.")
            else:
                st.error(f"No phases have values greater than zero for {selected_metric}.")


        # Display phase data table with all metrics in an expander
        with st.expander("Details"):
            # Sort by hours worked in descending order
            sorted_phase_agg = phase_agg.sort_values("hours_used", ascending=False)

            # Use the column configuration from chart_styles
            from utils.chart_styles import create_column_config

            # Display the table with column configurations
            st.dataframe(
                sorted_phase_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_phase_agg)
            )
    else:
        st.warning("Phase information is not available in the data.")
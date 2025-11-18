# charts/project_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import re
import numpy as np
from datetime import datetime

from utils.chart_styles import (
    create_column_config,
    render_chart,
    get_category_colors,
    get_metric_options,
    get_visualization_options,
    format_variance_columns,
    format_time_period_columns,
    standardize_column_order,
    initialize_analytics_metric_state
)

from utils.chart_helpers import (
    create_standardized_customdata,
    create_comparison_chart,
    create_single_metric_chart,
    filter_projects_by_metric,
    create_forecast_chart,
    create_monthly_metrics_chart,
    create_summary_metrics_table,
    create_yearly_metrics_table,
    create_monthly_metrics_table
)

def get_widget_key(base_key: str, nav_context: str = "project_details") -> str:
    """Generate stable widget keys for project charts"""
    # Use static keys to preserve widget state across reruns
    return f"{nav_context}_{base_key}"

def render_project_tab(filtered_df, aggregate_by_project, render_chart, get_category_colors, planned_df=None, filter_settings=None):
    """
    Renders the project analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project: Function to aggregate data by project
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
        planned_df: Optional DataFrame with planned hours data
        filter_settings: Filter settings from sidebar
    """
    # Check if planned data is available - either as separate df or in main df columns
    has_planned_data_separate = planned_df is not None and len(planned_df) > 0
    has_planned_data_integrated = 'planned_hours' in filtered_df.columns and filtered_df['planned_hours'].sum() > 0
    has_planned_data = has_planned_data_separate or has_planned_data_integrated
    
    # Note: No need to show messages about planned data availability
    
    # If planned data is integrated in main df and no separate planned_df provided, create planned_df from those columns
    if has_planned_data_integrated and not has_planned_data_separate:
        # Create planned_df from main df planned columns
        planned_cols = ['project_number', 'project_name', 'planned_hours']
        if 'planned_hourly_rate' in filtered_df.columns:
            planned_cols.append('planned_hourly_rate')
        if 'person_name' in filtered_df.columns:
            planned_cols.append('person_name')
        if 'record_date' in filtered_df.columns:
            planned_cols.append('record_date')
            
        # Filter to only records with planned hours > 0
        planned_mask = filtered_df['planned_hours'] > 0
        if planned_mask.any():
            planned_df = filtered_df[planned_mask][planned_cols].copy()
    
    # Note: If has_planned_data_separate is True, we use the already filtered planned_df parameter
    # This preserves all the comprehensive filtering (customer, person, date, etc.) applied at dashboard level
    
    # Ensure Project number is string type in both dataframes for consistent joining
    filtered_df = filtered_df.copy()
    filtered_df["project_number"] = filtered_df["project_number"].astype(str)
    
    if has_planned_data:
        planned_df = planned_df.copy()
        planned_df["project_number"] = planned_df["project_number"].astype(str)
    
    # Initialize shared metric state (persists across tabs)
    initialize_analytics_metric_state()

    # Get metric options using the new helper function
    metric_options = get_metric_options(has_planned_data)

    # Get current index from session state (with fallback if metric not in options)
    try:
        current_metric_index = metric_options.index(st.session_state.analytics_selected_metric)
    except ValueError:
        current_metric_index = 0  # Fallback to first option if current selection not available

    col1, col2 = st.columns(2)

    with col1:
        selected_metric = st.selectbox(
            label="Metric",
            label_visibility="collapsed",
            options=metric_options,
            index=current_metric_index,
            key=get_widget_key("metric_selectbox")
        )
        st.session_state.analytics_selected_metric = selected_metric
        
    
    # Set comparison view flags based on metric selection
    is_hours_comparison_view = selected_metric == "Worked vs Planned: Hours"
    is_rate_comparison_view = selected_metric == "Worked vs Planned: Hourly rate"
    is_fee_comparison_view = selected_metric == "Worked vs Planned: Fees"
    is_forecast_hours_view = selected_metric == "Hours" and has_planned_data
    is_comparison_view = is_hours_comparison_view or is_rate_comparison_view or is_fee_comparison_view

    # Check if we have data for the selected view
    if filtered_df.empty and not is_comparison_view:
        st.info("📊 No worked hours in selected date range.")
        st.markdown("Try adjusting your date filter or select a comparison view to see planned hours.")
        return

    # Handle aggregation for actual data
    if filtered_df.empty:
        # Create empty project aggregation with expected columns for comparison views
        project_agg = pd.DataFrame(columns=[
            "project_number", "project_name", "project_tag", "hours_used", 
            "hours_billable", "Number of people", "Non-billable hours", 
            "Billability %", "Fee", "Billable rate", "Effective rate"
        ])
    else:
        project_agg = aggregate_by_project(filtered_df)
        
        # Check if aggregation produced any results
        if project_agg.empty:
            st.info("📊 No worked hours in selected date range.")
            st.markdown("Try adjusting your filters or select a comparison view to see planned hours.")
            return
    
    # Merge with planned data if available
    if has_planned_data:
        # Import the function to merge actual and planned data
        from utils.planned_processors import aggregate_by_project_planned, merge_actual_planned_projects
        
        # Aggregate planned data by project
        planned_agg = aggregate_by_project_planned(planned_df)
        
        # Merge actual and planned data
        project_agg = merge_actual_planned_projects(project_agg, planned_agg)

    with col2:
        # Get visualization options using the new helper function
        viz_options = get_visualization_options(is_comparison_view, is_forecast_hours_view)
        default_index = 0  # Default to first option

        # Visualization type selection
        selected_viz_type = st.selectbox(
            label="Chart type",
            label_visibility="collapsed",
            options=viz_options,
            index=default_index,
            key=get_widget_key("viz_type_selectbox")
        )
        visualization_type = selected_viz_type
    
    # For monthly view, use the filtered dataframe directly
    is_monthly_view = visualization_type == "Monthly: Bar chart"
    
    # Import the new function for monthly aggregation if needed
    from utils.processors import aggregate_project_by_month_year
    
    # For monthly view, process differently based on whether it's a comparison or single metric
    if is_monthly_view:
        # Extract project numbers from filtered data to ensure planned data is filtered to same projects
        project_numbers = None
        if not filtered_df.empty:
            project_numbers = filtered_df["project_number"].unique().tolist()
        
        # Get monthly data using the already filtered dataframe and pass planned data if available
        monthly_data = aggregate_project_by_month_year(filtered_df, project_numbers=project_numbers, planned_df=planned_df, filter_settings=filter_settings)
        
        # Check if we have data
        if monthly_data.empty:
            st.error("No monthly data available for the selected projects.")
        else:
            # Create the monthly chart
            month_labels = monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
            
            # If it's a forecast hours view, create the accumulated forecast chart
            if is_forecast_hours_view and has_planned_data:
                # Use the new helper function to create the forecast chart
                fig, forecast_df = create_forecast_chart(monthly_data)
                
            # If it's a hours comparison view, create a grouped bar chart
            elif is_hours_comparison_view and has_planned_data:
                fig = create_comparison_chart(
                    monthly_data,
                    "hours_used",
                    "planned_hours",
                    title="",
                    y_axis_label="Hours",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            # If it's a rate comparison view, create a grouped bar chart
            elif is_rate_comparison_view and has_planned_data and "planned_hourly_rate" in monthly_data.columns:
                fig = create_comparison_chart(
                    monthly_data,
                    "Effective rate",
                    "planned_hourly_rate",
                    title="",
                    y_axis_label="Rate",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            # If it's a fee comparison view, create a grouped bar chart
            elif is_fee_comparison_view and has_planned_data and "planned_fee" in monthly_data.columns:
                fig = create_comparison_chart(
                    monthly_data,
                    "Fee",
                    "planned_fee",
                    title="",
                    y_axis_label="Fee_Amount",
                    x_field=monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
                )
                
                # Ensure x-axis is in chronological order
                fig.update_layout(
                    xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
                )
                
            else:
                # For single metric view, use the new helper function
                # Check if the selected metric is a comparison that we need to handle specially
                if selected_metric in ["Worked vs Planned: Hours", "Worked vs Planned: Hourly rate", "Worked vs Planned: Fees"]:
                    # Default to Hours worked if it's a comparison view but we got here
                    plot_metric = "hours_used"
                else:
                    # Translate display names to column names if needed
                    plot_metric = selected_metric
                    if selected_metric == "Hours worked":
                        plot_metric = "hours_used"
                    elif selected_metric == "Billable hours":
                        plot_metric = "hours_billable"
                    
                fig = create_monthly_metrics_chart(monthly_data, plot_metric, month_labels)
            
            # Render the chart immediately
            render_chart(fig, "project_monthly")
            
            # Create total summary table - expanded first
            with st.expander("Metrics: Total", expanded=False):
                # Use the new helper function to create the summary metrics table
                summary_df = create_summary_metrics_table(monthly_data, has_planned_data)
                
                # Add unique project count from original filtered_df
                summary_df["Unique projects"] = filtered_df["project_number"].nunique()
                
                # Display summary metrics - use original dataframe instead of formatted
                st.dataframe(
                    summary_df,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(summary_df)
                )
            
            # Yearly metrics
            with st.expander("Metrics: Year", expanded=False):
                # Use the new helper function to create the yearly metrics table
                yearly_data = create_yearly_metrics_table(monthly_data, filtered_df, has_planned_data)
                
                # Display the yearly aggregation - use original dataframe
                st.dataframe(
                    yearly_data,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(yearly_data)
                )
            
            # Monthly metrics    
            with st.expander("Metrics: Month", expanded=False):
                # Use the new helper function to create the monthly metrics table
                forecast_df_param = forecast_df if is_forecast_hours_view and has_planned_data and 'forecast_df' in locals() else None
                display_df, visible_cols = create_monthly_metrics_table(monthly_data, filtered_df, is_forecast_hours_view, forecast_df_param, has_planned_data)
                
                # Use original dataframe
                st.dataframe(
                    display_df[visible_cols],  # Only show visible columns
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(display_df)
                )
            
            # Project metrics
            with st.expander("Metrics: Project", expanded=False):
                # Use the complete project_agg dataframe from earlier
                sorted_project_agg = standardize_column_order(project_agg.sort_values("hours_used", ascending=False))
                
                # Display the table with column configurations - use original dataframe
                st.dataframe(
                    sorted_project_agg,
                    use_container_width=True,
                    hide_index=True,
                    column_config=create_column_config(sorted_project_agg)
                )
    else:
        # Filter projects based on selected metric or for comparison view
        if is_hours_comparison_view:
            # For hours comparison view, include projects with either hours worked or planned hours > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "hours_used", 
                "planned_hours", 
                is_comparison_view=True
            )
        elif is_rate_comparison_view:
            # For rate comparison view, include projects with either effective rate or planned rate > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "Effective rate", 
                "planned_hourly_rate", 
                is_comparison_view=True
            )
        elif is_fee_comparison_view:
            # For fee comparison view, include projects with either fee or planned fee > 0
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                "Fee", 
                "planned_fee", 
                is_comparison_view=True
            )
        else:
            # For single metric view, filter projects with metric > 0
            # Translate display names to column names if needed
            metric_column = selected_metric
            if selected_metric == "Hours worked":
                metric_column = "hours_used"
            elif selected_metric == "Billable hours":
                metric_column = "hours_billable"
            
            filtered_project_agg = filter_projects_by_metric(
                project_agg, 
                metric_column
            )
        
        # Render visualization based on type and metric
        if not filtered_project_agg.empty:
            # Hours comparison view
            if is_hours_comparison_view and has_planned_data:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "hours_used",
                    "planned_hours",
                    title="",
                    y_axis_label="Hours"
                )
                
                # Render the chart immediately
                render_chart(fig, "project")
            
            # Rate comparison view
            elif is_rate_comparison_view and has_planned_data and "planned_hourly_rate" in filtered_project_agg.columns:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "Effective rate",
                    "planned_hourly_rate",
                    title="",
                    y_axis_label="Rate"
                )
                
                # Render the chart immediately
                render_chart(fig, "project")
                
            # Fee comparison view
            elif is_fee_comparison_view and has_planned_data and "planned_fee" in filtered_project_agg.columns:
                fig = create_comparison_chart(
                    filtered_project_agg,
                    "Fee",
                    "planned_fee",
                    title="",
                    y_axis_label="Fee_Amount"
                )
                
                # Render the chart immediately
                render_chart(fig, "project")
            
            # Project: Treemap visualization
            elif visualization_type == "Project: Treemap":
                fig = create_single_metric_chart(
                    filtered_project_agg,
                    metric_column,
                    title="",
                    chart_type="treemap"
                )
                
                # Render the chart immediately
                render_chart(fig, "project")
            
            # Project: Bar chart visualization
            elif visualization_type == "Project: Bar chart":
                fig = create_single_metric_chart(
                    filtered_project_agg,
                    metric_column,
                    title="",
                    chart_type="bar",
                    sort_by=metric_column
                )
                
                # Render the chart immediately
                render_chart(fig, "project")
        else:
            st.error(f"No projects have values greater than zero for {selected_metric}.")
        
        # Project metrics table only for non-monthly views
        with st.expander("Metrics: Project", expanded=False):
            # Sort by hours worked in descending order
            sorted_project_agg = standardize_column_order(project_agg.sort_values("hours_used", ascending=False))
            
            # Display the table with column configurations - use original dataframe
            st.dataframe(
                sorted_project_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_project_agg)
            )
import streamlit as st
import pandas as pd
from period_translations.translations import t
from period_utils.chart_utils import (
    prepare_project_dataframe,
    create_bar_chart,
    create_treemap,
    create_color_map,
    create_hover_template,
    calculate_metric_forecast,
    get_project_total_metric,
    display_metrics_summary,
    display_monthly_breakdown,
    display_project_breakdown,
    display_project_per_month_breakdown
)

def render_project_hours_chart(df, selected_project, all_projects_option="All Projects"):
    """Render a chart showing project hours over time."""
    # Check required columns
    required_columns = ["Period", "Project Name", "Period Hours", "Planned Hours"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return
    
    if selected_project != all_projects_option:
        render_single_project_hours(df, selected_project)
    else:
        render_all_projects_hours(df)

def render_single_project_hours(df, project_name):
    """Render hours chart for a single project."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Filter data for selected project
    filtered_df = df_copy[df_copy["Project Name"] == project_name].sort_values("Period")
    
    # Return if no data
    if filtered_df.empty:
        st.warning(f"No data found for project: {project_name}")
        return
    
    # Value columns to visualize
    value_cols = ["Planned Hours", "Period Hours"]
    
    # Get total project hours metadata if available
    total_project_hours = get_project_total_metric(filtered_df, "Total Hours")
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Hours"] = t("project_hours_summary_planned_hours")
    translations_map["Period Hours"] = t("project_hours_summary_period_hours")
    
    # Melt the DataFrame for plotting
    melted_df = pd.melt(
        filtered_df,
        id_vars=["Period_display", "Project Name"],
        value_vars=value_cols,
        var_name="Metric Type",
        value_name="Hours"
    )
    
    # Add translated metric type for hover and legend
    melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
    
    # Create color map and hover template
    color_map = create_color_map(value_cols, scheme="blue")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items() if k in value_cols}
    hover_template = create_hover_template(include_units=True, unit_text=t('hrs'), decimal_places=0)
    
    # Create and display the chart
    fig = create_bar_chart(
        melted_df, 
        "Period_display", 
        "Hours", 
        "Metric Type Translated", 
        translated_color_map, 
        hover_template,
        y_label=t("hours") if "hours" in st.session_state.translations else "Hours",
        period_display_col="Period_display"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate forecast
    forecast_hours = calculate_metric_forecast(filtered_df, "Period Hours", "Planned Hours")
    
    # Display summary metrics
    # Summary section (no title needed)
    display_metrics_summary(
        filtered_df, 
        value_cols, 
        translations_map, 
        unit_suffix=t('hrs'),
        forecast_value=forecast_hours,
        total_value=total_project_hours,
        decimal_places=0,
        forecast_label_key='project_hours_summary_forecast',
        total_label_key='project_hours_summary_total_hours'
    )
    
    # Display monthly breakdown
    display_monthly_breakdown(
        filtered_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('hrs'), 
        decimal_places=1,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast',
        total_metric_col="Total Hours",
        total_label_key='project_hours_summary_total_hours'
    )
    
    # Display project breakdown
    display_project_breakdown(
        filtered_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('hrs'), 
        decimal_places=1,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast',
        total_metric_col="Total Hours",
        total_label_key='project_hours_summary_total_hours'
    )
    
    # Display project per month breakdown
    display_project_per_month_breakdown(
        filtered_df,
        value_cols,
        translations_map,
        format_suffix=t('hrs'),
        decimal_places=1,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast',
        total_metric_col="Total Hours",
        total_label_key='project_hours_summary_total_hours'
    )

def render_all_projects_hours(df):
    """Render hours chart for all projects aggregated."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Sort by period for better visualization
    viz_df = df_copy.sort_values("Period")
    
    # Aggregate data by period
    agg_df = viz_df.groupby("Period_display").agg({
        "Period Hours": "sum",
        "Planned Hours": "sum"
    }).reset_index()
    
    # Value columns to visualize
    value_cols = ["Planned Hours", "Period Hours"]
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Hours"] = t("project_hours_summary_planned_hours")
    translations_map["Period Hours"] = t("project_hours_summary_period_hours")
    
    # Create color map
    color_map = create_color_map(value_cols, scheme="blue")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items()}
    
    chart_type = st.radio(
        label="",  # Empty string removes the visible label
        options=[t('bar_chart'), t('tree_map')],
        horizontal=True,
        key='project_hours_charts'
    )
    
    if chart_type == t('bar_chart'):
        # Prepare data for bar chart
        melted_df = pd.melt(
            agg_df,
            id_vars=["Period_display"],
            value_vars=value_cols,
            var_name="Metric Type",
            value_name="Hours"
        )
        
        # Add translated metric type for hover and legend
        melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
        melted_df["custom_label"] = melted_df["Metric Type Translated"]
        
        # Create hover template
        hover_template = create_hover_template(include_units=True, unit_text=t('hrs'), decimal_places=0)
        
        # Create and display the bar chart
        fig = create_bar_chart(
            melted_df, 
            "Period_display", 
            "Hours", 
            "Metric Type Translated", 
            translated_color_map, 
            hover_template,
            y_label=t("hours") if "hours" in st.session_state.translations else "Hours",
            period_display_col="Period_display"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:  # Treemap
        # Prepare data for treemap
        treemap_df = viz_df.groupby("Project Name", as_index=False)["Period Hours"].sum()
        
        # Create treemap visualization
        fig_treemap = create_treemap(
            treemap_df,
            "Project Name",
            "Period Hours",
            color_scheme="Blues",
            unit_text=t('hrs')
        )
        
        if fig_treemap:
            # Add Streamlit styling
            st.markdown(
                """
                <style>
                .stPlotlyChart {
                    width: 100%;
                    margin: 0 auto;
                }
                </style>
                """, 
                unsafe_allow_html=True
            )
            
            # Display the treemap
            st.plotly_chart(fig_treemap, use_container_width=True)
        else:
            st.warning(t("no_data_for_treemap") if "no_data_for_treemap" in st.session_state.translations 
                      else "No registered hours in selected period")
    
    # Calculate forecast for all projects by aggregating project forecasts
    all_projects_forecast = sum(calculate_metric_forecast(project_data, "Period Hours", "Planned Hours") 
                               for _, project_data in viz_df.groupby("Project Name"))
    
    # Check if Total Hours column exists across all projects
    total_hours_all_projects = None
    if "Total Hours" in viz_df.columns:
        # Calculate the sum of Total Hours across projects (take first non-null per project)
        project_total_hours = {}
        for project_name, project_data in viz_df.groupby("Project Name"):
            total_hours_value = get_project_total_metric(project_data, "Total Hours")
            if total_hours_value is not None:
                project_total_hours[project_name] = total_hours_value
        
        # Sum up all project total hours if any exist
        if project_total_hours:
            total_hours_all_projects = sum(project_total_hours.values())
    
    # Display summary metrics
    # Summary section (no title needed)
    display_metrics_summary(
        agg_df, 
        value_cols, 
        translations_map, 
        unit_suffix=t('hrs'),
        forecast_value=all_projects_forecast,
        decimal_places=0,
        forecast_label_key='project_hours_summary_forecast'
    )
    
    # Display monthly breakdown
    display_monthly_breakdown(
        viz_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('hrs'), 
        decimal_places=0,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast'
    )
    
    # Display project breakdown
    display_project_breakdown(
        viz_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('hrs'), 
        decimal_places=0,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast',
        total_metric_col="Total Hours",
        total_label_key='project_hours_summary_total_hours',
        agg_type="sum"
    )
    
    # Display project per month breakdown
    display_project_per_month_breakdown(
        viz_df,
        value_cols,
        translations_map,
        format_suffix=t('hrs'),
        decimal_places=0,
        diff_prefix="hours_",
        forecast_label_key='project_hours_summary_forecast',
        total_metric_col="Total Hours",
        total_label_key='project_hours_summary_total_hours'
    )
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

def render_project_fees_chart(df, selected_project, all_projects_option="All Projects"):
    """Render a chart showing project fees over time."""
    # Check required columns
    required_columns = ["Period", "Project Name", "Period Fees Adjusted", "Planned Income"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return
    
    if selected_project != all_projects_option:
        render_single_project_fees(df, selected_project)
    else:
        render_all_projects_fees(df)

def render_single_project_fees(df, project_name):
    """Render fees chart for a single project."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Filter data for selected project
    filtered_df = df_copy[df_copy["Project Name"] == project_name].sort_values("Period")
    
    # Return if no data
    if filtered_df.empty:
        st.warning(f"No data found for project: {project_name}")
        return
    
    # Value columns to visualize
    value_cols = ["Planned Income", "Period Fees Adjusted"]
    
    # Get total project fees metadata if available
    total_project_fees = get_project_total_metric(filtered_df, "Total Fees")
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Income"] = t("project_fees_summary_planned_income")
    translations_map["Period Fees Adjusted"] = t("project_fees_summary_period_fees")
    
    # Melt the DataFrame for plotting
    melted_df = pd.melt(
        filtered_df,
        id_vars=["Period_display", "Project Name"],
        value_vars=value_cols,
        var_name="Metric Type",
        value_name="Fees"
    )
    
    # Add translated metric type for hover and legend
    melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
    
    # Create color map and hover template
    color_map = create_color_map(value_cols, scheme="green")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items() if k in value_cols}
    
    # Create hover template with thousand separators
    hover_template = (
        f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
        f"%{{x}}<br>"
        f"%{{y:,.0f}} {t('kr')}</span><br>"
        "<extra></extra>"
    )
    
    # Create and display the chart
    fig = create_bar_chart(
        melted_df, 
        "Period_display", 
        "Fees", 
        "Metric Type Translated", 
        translated_color_map, 
        hover_template,
        y_label=t("fees") if "fees" in st.session_state.translations else "Fees",
        period_display_col="Period_display"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate forecast
    forecast_fees = calculate_metric_forecast(filtered_df, "Period Fees Adjusted", "Planned Income")
    
    # Display summary metrics
    # Summary section (no title needed)
    display_metrics_summary(
        filtered_df, 
        value_cols, 
        translations_map, 
        unit_suffix=t('kr'),
        forecast_value=forecast_fees,
        total_value=total_project_fees,
        decimal_places=2,
        convert_to_millions=True,
        forecast_label_key='project_fees_summary_forecast',
        total_label_key='project_fees_summary_total_fees'
    )
    
    # Display monthly breakdown
    display_monthly_breakdown(
        filtered_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('kr'), 
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast',
        total_metric_col="Total Fees",
        total_label_key='project_fees_summary_total_fees'
    )
    
    # Display project breakdown
    display_project_breakdown(
        filtered_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('kr'), 
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast',
        total_metric_col="Total Fees",
        total_label_key='project_fees_summary_total_fees'
    )
    
    # Display project per month breakdown
    display_project_per_month_breakdown(
        filtered_df,
        value_cols,
        translations_map,
        format_suffix=t('kr'),
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast',
        total_metric_col="Total Fees",
        total_label_key='project_fees_summary_total_fees'
    )

def render_all_projects_fees(df):
    """Render fees chart for all projects aggregated."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Sort by period for better visualization
    viz_df = df_copy.sort_values("Period")
    
    # Aggregate data by period
    agg_df = viz_df.groupby("Period_display").agg({
        "Period Fees Adjusted": "sum",
        "Planned Income": "sum"
    }).reset_index()
    
    # Value columns to visualize
    value_cols = ["Planned Income", "Period Fees Adjusted"]
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Income"] = t("project_fees_summary_planned_income")
    translations_map["Period Fees Adjusted"] = t("project_fees_summary_period_fees")
    
    # Create color map
    color_map = create_color_map(value_cols, scheme="green")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items()}
    
    chart_type = st.radio(
        label="",  # Empty string removes the visible label
        options=[t('bar_chart'), t('tree_map')],
        horizontal=True,
        key='project_fees_charts'
    )
    #ddd
    if chart_type == t('bar_chart'):
        # Prepare data for bar chart
        melted_df = pd.melt(
            agg_df,
            id_vars=["Period_display"],
            value_vars=value_cols,
            var_name="Metric Type",
            value_name="Fees"
        )
        
        # Add translated metric type for hover and legend
        melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
        melted_df["custom_label"] = melted_df["Metric Type Translated"]
        
        # Create hover template with thousand separators
        hover_template = (
            f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
            f"%{{x}}<br>"
            f"%{{y:,.0f}} {t('kr')}</span><br>"
            "<extra></extra>"
        )
        
        # Create and display the bar chart
        fig = create_bar_chart(
            melted_df, 
            "Period_display", 
            "Fees", 
            "Metric Type Translated", 
            translated_color_map, 
            hover_template,
            y_label=t("fees") if "fees" in st.session_state.translations else "Fees",
            period_display_col="Period_display"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:  # Treemap
        # Prepare data for treemap
        treemap_df = viz_df.groupby("Project Name", as_index=False)["Period Fees Adjusted"].sum()
        
        # Create treemap visualization
        fig_treemap = create_treemap(
            treemap_df,
            "Project Name",
            "Period Fees Adjusted",
            color_scheme="Greens",
            unit_text=t('kr')
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
                      else "No registered fees in selected period")
    
    # Calculate forecast for all projects by aggregating project forecasts
    all_projects_forecast = sum(calculate_metric_forecast(project_data, "Period Fees Adjusted", "Planned Income") 
                               for _, project_data in viz_df.groupby("Project Name"))
    
    # Check if Total Fees column exists across all projects
    total_fees_all_projects = None
    if "Total Fees" in viz_df.columns:
        # Calculate the sum of Total Fees across projects (take first non-null per project)
        project_total_fees = {}
        for project_name, project_data in viz_df.groupby("Project Name"):
            total_fees_value = get_project_total_metric(project_data, "Total Fees")
            if total_fees_value is not None:
                project_total_fees[project_name] = total_fees_value
        
        # Sum up all project total fees if any exist
        if project_total_fees:
            total_fees_all_projects = sum(project_total_fees.values())
    
    # Display summary metrics
    # Summary section (no title needed)
    display_metrics_summary(
        agg_df, 
        value_cols, 
        translations_map, 
        unit_suffix=t('kr'),
        forecast_value=all_projects_forecast,
        decimal_places=2,
        convert_to_millions=True,
        forecast_label_key='project_fees_summary_forecast'
    )
    
    # Display monthly breakdown
    display_monthly_breakdown(
        viz_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('kr'), 
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast'
    )
    
    # Display project breakdown
    display_project_breakdown(
        viz_df, 
        value_cols, 
        translations_map, 
        format_suffix=t('kr'), 
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast',
        total_metric_col="Total Fees",
        total_label_key='project_fees_summary_total_fees',
        agg_type="sum"
    )
    
    # Display project per month breakdown
    display_project_per_month_breakdown(
        viz_df,
        value_cols,
        translations_map,
        format_suffix=t('kr'),
        decimal_places=0,
        diff_prefix="fees_",
        forecast_label_key='project_fees_summary_forecast',
        total_metric_col="Total Fees",
        total_label_key='project_fees_summary_total_fees'
    )
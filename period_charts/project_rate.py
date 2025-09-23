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

def render_project_rate_chart(df, selected_project, all_projects_option="All Projects"):
    """Render a chart showing project hourly rates over time."""
    # Check required columns
    required_columns = ["Period", "Project Name", "Period Hours", "Planned Hours", "Period Fees Adjusted", "Planned Income"]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return
    
    # Create rate columns on the fly
    df_with_rates = df.copy()
    
    # Calculate rates - add 1 to hours before division to avoid division by zero
    df_with_rates["Planned Hourly Rate"] = df_with_rates["Planned Income"] / (df_with_rates["Planned Hours"] + 1)
    df_with_rates["Period Hourly Rate"] = df_with_rates["Period Fees Adjusted"] / (df_with_rates["Period Hours"] + 1)
    
    # Reset to 0 where hours were 0
    df_with_rates.loc[df_with_rates["Planned Hours"] <= 0, "Planned Hourly Rate"] = 0
    df_with_rates.loc[df_with_rates["Period Hours"] <= 0, "Period Hourly Rate"] = 0
    
    if selected_project != all_projects_option:
        render_single_project_rate(df_with_rates, selected_project)
    else:
        render_all_projects_rate(df_with_rates)

def render_single_project_rate(df, project_name):
    """Render rate chart for a single project."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Filter data for selected project
    filtered_df = df_copy[df_copy["Project Name"] == project_name].sort_values("Period")
    
    # Return if no data
    if filtered_df.empty:
        st.warning(f"No data found for project: {project_name}")
        return
    
    # Value columns to visualize
    value_cols = ["Planned Hourly Rate", "Period Hourly Rate"]
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Hourly Rate"] = t("project_rate_summary_planned_rate") if "project_rate_summary_planned_rate" in st.session_state.translations else "Planned Hourly Rate"
    translations_map["Period Hourly Rate"] = t("project_rate_summary_period_rate") if "project_rate_summary_period_rate" in st.session_state.translations else "Period Hourly Rate"
    
    # Melt the DataFrame for plotting
    melted_df = pd.melt(
        filtered_df,
        id_vars=["Period_display", "Project Name"],
        value_vars=value_cols,
        var_name="Metric Type",
        value_name="Rate"
    )
    
    # Add translated metric type for hover and legend
    melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
    
    # Create color map and hover template
    color_map = create_color_map(value_cols, scheme="purple")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items() if k in value_cols}
    hover_template = create_hover_template(include_units=True, unit_text=t('kr') + "/" + t('hrs'), decimal_places=0)
    
    # Create and display the chart
    fig = create_bar_chart(
        melted_df, 
        "Period_display", 
        "Rate", 
        "Metric Type Translated", 
        translated_color_map, 
        hover_template,
        y_label=t("hourly_rate") if "hourly_rate" in st.session_state.translations else "Hourly Rate",
        period_display_col="Period_display"
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Calculate forecast - for rates, we need a weighted approach
    # First calculate forecast for hours and fees separately
    forecast_hours = calculate_metric_forecast(filtered_df, "Period Hours", "Planned Hours")
    forecast_fees = calculate_metric_forecast(filtered_df, "Period Fees Adjusted", "Planned Income")
    
    # Then calculate rate as weighted average
    forecast_rate = forecast_fees / (forecast_hours + 1) if forecast_hours > 0 else 0
    
    # Display summary metrics
    # Summary section (no title needed)
    
    # Calculate weighted average rates
    total_planned_fees = filtered_df["Planned Income"].sum()
    total_planned_hours = filtered_df["Planned Hours"].sum()
    avg_planned_rate = total_planned_fees / (total_planned_hours + 1) if total_planned_hours > 0 else 0
    
    total_actual_fees = filtered_df["Period Fees Adjusted"].sum()
    total_actual_hours = filtered_df["Period Hours"].sum()
    avg_actual_rate = total_actual_fees / (total_actual_hours + 1) if total_actual_hours > 0 else 0
    
    # Create a temporary dataframe with just one row containing the weighted averages
    weighted_df = pd.DataFrame({
        "Period_display": ["Total"],
        "Planned Hourly Rate": [avg_planned_rate],
        "Period Hourly Rate": [avg_actual_rate]
    })
    
    display_metrics_summary(
        weighted_df, 
        value_cols, 
        translations_map, 
        unit_suffix=f"{t('kr')}/{t('hrs')}",
        forecast_value=forecast_rate,
        total_value=None,  # No total rate concept
        decimal_places=0,
        forecast_label_key='project_rate_summary_forecast'
    )
    
    # Display monthly breakdown
    display_monthly_breakdown(
        filtered_df, 
        value_cols, 
        translations_map, 
        format_suffix=f"{t('kr')}/{t('hrs')}", 
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast'
    )
    
    # Display project breakdown with properly calculated rates
    # For a single project view, we need to create a DataFrame with pre-calculated weighted average rates
    # First, create a copy to avoid modifying the original DataFrame
    project_df = filtered_df.copy()
    
    # Calculate the weighted average rates
    total_planned_fees = project_df["Planned Income"].sum()
    total_planned_hours = project_df["Planned Hours"].sum()
    total_actual_fees = project_df["Period Fees Adjusted"].sum()
    total_actual_hours = project_df["Period Hours"].sum()
    
    # Replace all rate values with the weighted average
    if total_planned_hours > 0:
        project_df["Planned Hourly Rate"] = total_planned_fees / (total_planned_hours + 1)
    if total_actual_hours > 0:
        project_df["Period Hourly Rate"] = total_actual_fees / (total_actual_hours + 1)
    
    # Use this modified DataFrame for the project breakdown
    display_project_breakdown(
        project_df, 
        value_cols, 
        translations_map, 
        format_suffix=f"{t('kr')}/{t('hrs')}", 
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast',
        agg_type="mean"  # Since we've already calculated the weighted average
    )
    
    # Display project per month breakdown - use original filtered_df with rate calculations
    display_project_per_month_breakdown(
        filtered_df,
        value_cols,
        translations_map,
        format_suffix=f"{t('kr')}/{t('hrs')}",
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast'
    )

def render_all_projects_rate(df):
    """Render rate chart for all projects aggregated."""
    # Prepare dataframe
    df_copy = prepare_project_dataframe(df)
    
    # Sort by period for better visualization
    viz_df = df_copy.sort_values("Period")
    
    # Calculate weighted average rates by period
    agg_df = pd.DataFrame()
    agg_df["Period_display"] = viz_df["Period_display"].unique()
    
    # Aggregate data by period with weighted rates
    period_data = []
    for period in agg_df["Period_display"]:
        period_rows = viz_df[viz_df["Period_display"] == period]
        
        # Calculate weighted average for planned rate
        total_planned_fees = period_rows["Planned Income"].sum()
        total_planned_hours = period_rows["Planned Hours"].sum()
        planned_rate = total_planned_fees / (total_planned_hours + 1) if total_planned_hours > 0 else 0
        
        # Calculate weighted average for actual rate
        total_actual_fees = period_rows["Period Fees Adjusted"].sum()
        total_actual_hours = period_rows["Period Hours"].sum()
        actual_rate = total_actual_fees / (total_actual_hours + 1) if total_actual_hours > 0 else 0
        
        period_data.append({
            "Period_display": period,
            "Planned Hourly Rate": planned_rate,
            "Period Hourly Rate": actual_rate
        })
    
    # Create aggregated dataframe with weighted rates
    agg_df = pd.DataFrame(period_data)
    
    # Sort periods chronologically
    try:
        agg_df = agg_df.sort_values(
            "Period_display",
            key=lambda x: pd.to_datetime(x, format="%b %Y")
        )
    except (ValueError, TypeError, pd.errors.ParserError):
        # Fallback to simple sorting if datetime conversion fails
        agg_df = agg_df.sort_values("Period_display")
    
    # Value columns to visualize
    value_cols = ["Planned Hourly Rate", "Period Hourly Rate"]
    
    # Create translation mapping
    translations_map = {}
    translations_map["Planned Hourly Rate"] = t("project_rate_summary_planned_rate") if "project_rate_summary_planned_rate" in st.session_state.translations else "Planned Hourly Rate"
    translations_map["Period Hourly Rate"] = t("project_rate_summary_period_rate") if "project_rate_summary_period_rate" in st.session_state.translations else "Period Hourly Rate"
    
    # Create color map
    color_map = create_color_map(value_cols, scheme="purple")
    translated_color_map = {translations_map.get(k, k): v for k, v in color_map.items()}
    
    chart_type = st.radio(
        label="",  # Empty string removes the visible label
        options=[t('bar_chart'), t('tree_map')],
        horizontal=True,
        key='project_rate_charts'
    )
    
    if chart_type == t('bar_chart'):
        # Prepare data for bar chart
        melted_df = pd.melt(
            agg_df,
            id_vars=["Period_display"],
            value_vars=value_cols,
            var_name="Metric Type",
            value_name="Rate"
        )
        
        # Add translated metric type for hover and legend
        melted_df["Metric Type Translated"] = melted_df["Metric Type"].map(translations_map)
        melted_df["custom_label"] = melted_df["Metric Type Translated"]
        
        # Create hover template
        hover_template = create_hover_template(include_units=True, unit_text=f"{t('kr')}/{t('hrs')}", decimal_places=0)
        
        # Create and display the bar chart
        fig = create_bar_chart(
            melted_df, 
            "Period_display", 
            "Rate", 
            "Metric Type Translated", 
            translated_color_map, 
            hover_template,
            y_label=t("hourly_rate") if "hourly_rate" in st.session_state.translations else "Hourly Rate",
            period_display_col="Period_display"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:  # Treemap
        # Calculate weighted average rate per project for treemap
        project_data = []
        for project_name in viz_df["Project Name"].unique():
            project_rows = viz_df[viz_df["Project Name"] == project_name]
            
            # Calculate weighted average rate
            total_fees = project_rows["Period Fees Adjusted"].sum()
            total_hours = project_rows["Period Hours"].sum()
            avg_rate = total_fees / (total_hours + 1) if total_hours > 0 else 0
            
            project_data.append({
                "Project Name": project_name,
                "Period Hourly Rate": avg_rate
            })
        
        treemap_df = pd.DataFrame(project_data)
        
        # Create treemap visualization
        fig_treemap = create_treemap(
            treemap_df,
            "Project Name",
            "Period Hourly Rate",
            color_scheme="Purples",
            unit_text=f"{t('kr')}/{t('hrs')}"
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
                      else "No registered rates in selected period")
    
    # Calculate forecast for all projects
    # First, calculate forecast hours and fees for all projects
    all_projects_forecast_hours = sum(calculate_metric_forecast(project_data, "Period Hours", "Planned Hours") 
                                    for _, project_data in viz_df.groupby("Project Name"))
    all_projects_forecast_fees = sum(calculate_metric_forecast(project_data, "Period Fees Adjusted", "Planned Income") 
                                   for _, project_data in viz_df.groupby("Project Name"))
    
    # Then calculate forecast rate as weighted average
    all_projects_forecast_rate = all_projects_forecast_fees / (all_projects_forecast_hours + 1) if all_projects_forecast_hours > 0 else 0
    
    # Display summary metrics
    # Summary section (no title needed)
    
    # Calculate weighted average rates
    total_planned_fees = viz_df["Planned Income"].sum()
    total_planned_hours = viz_df["Planned Hours"].sum()
    avg_planned_rate = total_planned_fees / (total_planned_hours + 1) if total_planned_hours > 0 else 0
    
    total_actual_fees = viz_df["Period Fees Adjusted"].sum()
    total_actual_hours = viz_df["Period Hours"].sum()
    avg_actual_rate = total_actual_fees / (total_actual_hours + 1) if total_actual_hours > 0 else 0
    
    # Create a temporary dataframe with just one row containing the weighted averages
    weighted_df = pd.DataFrame({
        "Period_display": ["Total"],
        "Planned Hourly Rate": [avg_planned_rate],
        "Period Hourly Rate": [avg_actual_rate]
    })
    
    # Use this dataframe for the summary display
    display_metrics_summary(
        weighted_df, 
        value_cols, 
        translations_map, 
        unit_suffix=f"{t('kr')}/{t('hrs')}",
        forecast_value=all_projects_forecast_rate,
        total_value=None,  # No total rate concept
        decimal_places=0,
        forecast_label_key='project_rate_summary_forecast'
    )
    
    # Create a DataFrame with pre-calculated weighted average rates per month
    monthly_data = []
    for period in viz_df["Period_display"].unique():
        period_rows = viz_df[viz_df["Period_display"] == period]
        
        # Calculate weighted average rates
        m_total_planned_fees = period_rows["Planned Income"].sum()
        m_total_planned_hours = period_rows["Planned Hours"].sum()
        m_avg_planned_rate = m_total_planned_fees / (m_total_planned_hours + 1) if m_total_planned_hours > 0 else 0
        
        m_total_actual_fees = period_rows["Period Fees Adjusted"].sum()
        m_total_actual_hours = period_rows["Period Hours"].sum()
        m_avg_actual_rate = m_total_actual_fees / (m_total_actual_hours + 1) if m_total_actual_hours > 0 else 0
        
        # Create a dictionary with the information we need
        month_dict = {
            "Period_display": period,
            "Period": period_rows["Period"].iloc[0],  # Take the first period value
            "Planned Hourly Rate": m_avg_planned_rate,
            "Period Hourly Rate": m_avg_actual_rate,
            # Add the raw data needed for calculations
            "Period Hours": m_total_actual_hours,
            "Planned Hours": m_total_planned_hours,
            "Period Fees Adjusted": m_total_actual_fees,
            "Planned Income": m_total_planned_fees
        }
        
        monthly_data.append(month_dict)
    
    # Create a DataFrame with pre-calculated monthly rates
    monthly_df = pd.DataFrame(monthly_data)
    
    # Sort by period
    try:
        monthly_df = monthly_df.sort_values(
            "Period_display",
            key=lambda x: pd.to_datetime(x, format="%b %Y")
        )
    except (ValueError, TypeError, pd.errors.ParserError):
        # Fallback to simple sorting if datetime conversion fails
        monthly_df = monthly_df.sort_values("Period_display")
    
    # Display monthly breakdown with pre-calculated rates
    display_monthly_breakdown(
        monthly_df, 
        value_cols, 
        translations_map, 
        format_suffix=f"{t('kr')}/{t('hrs')}", 
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast'
    )
    
    # Create a DataFrame with pre-calculated weighted average rates per project
    project_data = []
    for project_name in viz_df["Project Name"].unique():
        project_rows = viz_df[viz_df["Project Name"] == project_name]
        
        # Calculate weighted average rates
        p_total_planned_fees = project_rows["Planned Income"].sum()
        p_total_planned_hours = project_rows["Planned Hours"].sum()
        p_avg_planned_rate = p_total_planned_fees / (p_total_planned_hours + 1) if p_total_planned_hours > 0 else 0
        
        p_total_actual_fees = project_rows["Period Fees Adjusted"].sum()
        p_total_actual_hours = project_rows["Period Hours"].sum()
        p_avg_actual_rate = p_total_actual_fees / (p_total_actual_hours + 1) if p_total_actual_hours > 0 else 0
        
        # Create a dictionary with the information we need
        project_dict = {
            "Project Name": project_name,
            "Planned Hourly Rate": p_avg_planned_rate,
            "Period Hourly Rate": p_avg_actual_rate,
            # Add the missing columns
            "Period Hours": p_total_actual_hours,
            "Planned Hours": p_total_planned_hours,
            "Period Fees Adjusted": p_total_actual_fees,
            "Planned Income": p_total_planned_fees
        }
        
        project_data.append(project_dict)
    
    # Create a DataFrame with our pre-calculated rates
    project_df = pd.DataFrame(project_data)
    
    # Use this project_df for the breakdown
    display_project_breakdown(
        project_df, 
        value_cols, 
        translations_map, 
        format_suffix=f"{t('kr')}/{t('hrs')}", 
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast',
        agg_type="first"  # Just use the pre-calculated values directly
    )
    
    # Display project per month breakdown - use original viz_df with rate calculations
    display_project_per_month_breakdown(
        viz_df,
        value_cols,
        translations_map,
        format_suffix=f"{t('kr')}/{t('hrs')}",
        decimal_places=0,
        diff_prefix="rate_",
        forecast_label_key='project_rate_summary_forecast'
    )
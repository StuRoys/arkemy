import streamlit as st
import plotly.express as px
import pandas as pd
from period_translations.translations import t

def render_comparison_chart(df, selected_person, target_value=80):
    """
    Render a bar chart showing billable rate (Project hours / Capacity/Period) filtered by person.
    
    Parameters:
    df (DataFrame): The DataFrame containing the data
    selected_person (str): The person to filter by
    target_value (int): Target billable rate percentage
    
    Returns:
    DataFrame: The filtered dataframe
    """
    # Check required columns
    required_columns = ["Period", "Person", "Capacity/Period", "Project hours"]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"Missing required columns: {', '.join(missing_columns)}")
        return df[df["Person"] == selected_person] if "Person" in df.columns else df
    
    # Create a copy of the dataframe
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper sorting
    if not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Filter data by selected person
    filtered_df = df_copy[df_copy["Person"] == selected_person].sort_values("Period")
    
    # Calculate billable rate
    filtered_df["Billable Rate"] = (filtered_df["Project hours"] / filtered_df["Capacity/Period"] * 100).round(2)
    
    # Calculate additional metrics
    if "Hours/Period" in filtered_df.columns:
        filtered_df["Registered vs Schedule"] = (filtered_df["Hours/Registered"] / filtered_df["Hours/Period"] * 100).round(2) if "Hours/Registered" in filtered_df.columns else pd.Series([0] * len(filtered_df))
        filtered_df["Billable vs Schedule"] = (filtered_df["Project hours"] / filtered_df["Hours/Period"] * 100).round(2)
        filtered_df["Non-billable vs Schedule"] = (filtered_df["Unpaid work"] / filtered_df["Hours/Period"] * 100).round(2) if "Unpaid work" in filtered_df.columns else pd.Series([0] * len(filtered_df))
    
    filtered_df["Registered vs Capacity"] = (filtered_df["Hours/Registered"] / filtered_df["Capacity/Period"] * 100).round(2) if "Hours/Registered" in filtered_df.columns else pd.Series([0] * len(filtered_df))
    filtered_df["Non-billable vs Capacity"] = (filtered_df["Unpaid work"] / filtered_df["Capacity/Period"] * 100).round(2) if "Unpaid work" in filtered_df.columns else pd.Series([0] * len(filtered_df))
    
    if "Hours/Registered" in filtered_df.columns:
        filtered_df["Billable vs Registered"] = (filtered_df["Project hours"] / filtered_df["Hours/Registered"] * 100).round(2)
        filtered_df["Non-billable vs Registered"] = (filtered_df["Unpaid work"] / filtered_df["Hours/Registered"] * 100).round(2) if "Unpaid work" in filtered_df.columns else pd.Series([0] * len(filtered_df))
    
    # Create formatted period string for display
    filtered_df["Period_display"] = filtered_df["Period"].dt.strftime("%b %Y")
    
    # Create a dropdown for selecting which metric to display
    metric_options = {
        "Billable Rate": "Billable vs Capacity",
        "Registered vs Schedule": "Registered vs Schedule",
        "Registered vs Capacity": "Registered vs Capacity",
        "Billable vs Schedule": "Billable vs Schedule",
        "Billable vs Capacity": "Billable vs Capacity",
        "Billable vs Registered": "Billable vs Registered",
        "Non-billable vs Schedule": "Non-billable vs Schedule",
        "Non-billable vs Capacity": "Non-billable vs Capacity",
        "Non-billable vs Registered": "Non-billable vs Registered"
    }
    
    # Create filtered options in the correct order
    available_metrics = []
    ordered_metrics = [
        "Registered vs Schedule",
        "Registered vs Capacity", 
        "Billable vs Schedule",
        "Billable Rate",  # This is Billable vs Capacity
        "Billable vs Registered",
        "Non-billable vs Schedule",
        "Non-billable vs Capacity",
        "Non-billable vs Registered"
    ]
    
    # Add metrics in the specified order if they're available
    for metric in ordered_metrics:
        if metric == "Registered vs Schedule" and "Hours/Period" in filtered_df.columns and "Hours/Registered" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Registered vs Capacity" and "Hours/Registered" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Billable vs Schedule" and "Hours/Period" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Billable Rate":  # Always available
            available_metrics.append(metric)
        elif metric == "Billable vs Registered" and "Hours/Registered" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Non-billable vs Schedule" and "Hours/Period" in filtered_df.columns and "Unpaid work" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Non-billable vs Capacity" and "Unpaid work" in filtered_df.columns:
            available_metrics.append(metric)
        elif metric == "Non-billable vs Registered" and "Hours/Registered" in filtered_df.columns and "Unpaid work" in filtered_df.columns:
            available_metrics.append(metric)
    
    # Only show dropdown if there are multiple metrics available
    if len(available_metrics) > 1:
        selected_metric = st.selectbox(
            t(""),
            options=available_metrics,
            format_func=lambda x: metric_options.get(x, x)
        )
    else:
        selected_metric = "Billable Rate"
    
    # Determine color based on metric type
    if "Registered vs" in selected_metric:
        bar_color = '#9d7dbc'  # Purple
    elif "Billable vs" in selected_metric or selected_metric == "Billable Rate":
        bar_color = '#2ca02c'  # Green
    elif "Non-billable vs" in selected_metric:
        bar_color = '#d62728'  # Red
    else:
        bar_color = '#4C78A8'  # Default blue
    
    # Create the bar chart with ordered periods and appropriate color
    fig = px.bar(
        filtered_df,
        x="Period_display",
        y=selected_metric,
        labels={"Period_display": t("period"), selected_metric: f"{selected_metric} (%)"},
        category_orders={"Period_display": filtered_df["Period_display"].tolist()},
        color_discrete_sequence=[bar_color],
        height=515
    )
    
    # Add text labels inside the bars
    fig.update_traces(
        texttemplate='%{y:.0f}%', 
        textposition='auto',
        textfont=dict(color='white', size=16, family='Arial, sans-serif')
    )

    fig.update_layout(
    xaxis=dict(tickfont=dict(size=16)),
    yaxis=dict(tickfont=dict(size=16))
    )
    
    # Create custom hovertemplate
    hovertemplate = (
        f"<b style='font-size:20px'>%{{y:.1f}}%</b><br><br>"
        f"<span style='font-size:14px'>{t('hours_period')}: %{{customdata[0]:.0f}}<br>"
        f"{t('absence_period')}: %{{customdata[1]:.0f}}<br>"
        f"{t('capacity_period')}: %{{customdata[2]:.0f}}<br>"
        f"{t('hours_registered')}: %{{customdata[3]:.0f}}<br>"
        f"{t('project_hours')}: %{{customdata[4]:.0f}}<br>"
        f"{t('unpaid_work')}: %{{customdata[5]:.0f}}</span><br>"
        "<extra></extra>"
    )
    
    # Ensure all required columns exist, use 0 as default if missing
    custom_data_cols = [
        "Hours/Period",
        "Absence/Period", 
        "Capacity/Period", 
        "Hours/Registered", 
        "Project hours", 
        "Unpaid work"
    ]
    
    # Create a list of arrays for customdata
    custom_data = []
    for col in custom_data_cols:
        if col in filtered_df.columns:
            custom_data.append(filtered_df[col])
        else:
            # Use zeros if column doesn't exist
            custom_data.append(pd.Series([0] * len(filtered_df)))
    
    # Update traces with custom hovertemplate and data
    fig.update_traces(
        customdata=list(zip(*custom_data)),
        hovertemplate=hovertemplate
    )
    
    # Set y-axis to always include 100%
    fig.update_layout(
        yaxis=dict(
            range=[0, 120],
            tickvals=[0, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 110, 120,],
            ticktext=["0%", "10%", "20%", "30%", "40%", "50%", "60%", "70%", "80%", "90%", "100%", "110%", "120%"],
        )
    )
    
    # Ensure all labels are shown
    fig.update_xaxes(tickangle=45)
    
    # Display the chart
    st.plotly_chart(fig, use_container_width=True)
    
    return filtered_df
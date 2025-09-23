import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from period_translations.translations import t

def create_bar_chart(data_df, x_col, y_col, color_col, color_map, hover_template, y_label=None, period_display_col=None):
    """Create a standardized bar chart.
    
    Parameters:
    -----------
    data_df : DataFrame
        The data to plot
    x_col : str
        The column to use for x-axis
    y_col : str
        The column to use for y-axis
    color_col : str
        The column to use for color grouping
    color_map : dict
        Mapping of color values to colors
    hover_template : str
        Template for hover text
    y_label : str, optional
        Custom label for y-axis
    period_display_col : str, optional
        Column to use for period ordering
    """
    category_orders = {}
    if period_display_col:
        category_orders[x_col] = sorted(data_df[period_display_col].unique(), 
                                       key=lambda x: pd.to_datetime(x, format="%b %Y"))
    
    # Use provided y_label or default to appropriate translation
    if y_label is None:
        if "hourly_rate" in y_col.lower():
            y_label = t("hourly_rate") if "hourly_rate" in st.session_state.translations else "Hourly Rate"
        elif "hours" in y_col.lower():
            y_label = t("hours") if "hours" in st.session_state.translations else "Hours"
        elif "fees" in y_col.lower():
            y_label = t("fees") if "fees" in st.session_state.translations else "Fees"
        else:
            y_label = y_col
    
    fig = px.bar(
        data_df,
        x=x_col,
        y=y_col,
        color=color_col,
        barmode="group",
        labels={
            x_col: t("period"),
            y_col: y_label,
            color_col: ""
        },
        category_orders=category_orders,
        color_discrete_map=color_map,
        custom_data=[color_col]
    )
    
    # Apply hover template
    for trace in fig.data:
        trace.hovertemplate = hover_template
    
    # Improve chart readability
    fig.update_layout(
        height=415,
        xaxis_tickangle=45,
        margin=dict(l=20, r=20, t=40, b=20),
        legend_title_text="",
        xaxis=dict(
            tickfont=dict(
                size=16  # Increase x-axis font size
            )
        ),
        yaxis=dict(
            tickfont=dict(
                size=16  # Increase y-axis font size
            )
        )
    )
    
    return fig

def create_treemap(data_df, path_col, values_col, color_scheme="Blues", unit_text=""):
    """Create a standardized treemap visualization.
    
    Parameters:
    -----------
    data_df : DataFrame
        The data to plot
    path_col : str
        The column to use for treemap hierarchy
    values_col : str
        The column to use for size values
    color_scheme : str, optional
        The color scheme to use (e.g., "Blues", "Greens", "Purples")
    unit_text : str, optional
        Unit text for display
    """
    # Filter out rows with zero or negative values
    filtered_df = data_df[data_df[values_col] > 0]
    
    if filtered_df.empty:
        return None
    
    # Calculate total for title
    total_value = filtered_df[values_col].sum()
    
    # Format total with thousand separators
    total_formatted = f"{total_value:_.0f}".replace("_", " ")
    
    fig = px.treemap(
        filtered_df,
        path=[path_col],
        values=values_col,
        color=values_col,
        color_continuous_scale=color_scheme,
        labels={
            path_col: t("project_name") if "project_name" in st.session_state.translations else path_col, 
            values_col: t(values_col.lower().replace(" ", "_")) if values_col.lower().replace(" ", "_") in st.session_state.translations else values_col
        }
    )
    
    # Determine if we need thousand separators (for monetary values)
    use_thousand_sep = color_scheme == "Greens"  # Typically fees
    
    # Update hover template and styling
    if use_thousand_sep:
        # With thousand separators - no decimals (use native Plotly comma formatting)
        hover_template = f"<b style='font-size:18px'>%{{label}}</b><br><span style='font-size:18px'>{values_col}: %{{value:,.0f}} {unit_text}</span>"
        text_template = '%{label}<br>%{value:,.0f} ' + unit_text
    else:
        # Without thousand separators - 1 decimal for hours, 0 for rates
        hover_template = f"<b style='font-size:18px'>%{{label}}</b><br><span style='font-size:18px'>{values_col}: %{{value:.0f}} {unit_text}</span>"
        text_template = '%{label}<br>%{value:.0f} ' + unit_text
    
    fig.update_traces(
        hovertemplate=hover_template,
        texttemplate=text_template,
        textposition='middle center',
        textfont=dict(size=16),
        marker=dict(
            cornerradius=5,
            pad=dict(t=5, l=5, r=5, b=5)
        )
    )
    
    # Apply styling
    fig.update_layout(
        height=400,
        coloraxis_showscale=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=20, r=20, t=40, b=20)
    )
    
    return fig

def create_color_map(value_cols, scheme="blue"):
    """Create a color map based on the selected scheme.
    
    Parameters:
    -----------
    value_cols : list
        List of column names to create colors for
    scheme : str, optional
        Color scheme to use ('blue', 'green', or 'purple')
    
    Returns:
    --------
    dict
        Mapping of column names to colors
    """
    if scheme == "blue":
        colors = ["#7fcdff", "#1f77b4"]  # Lighter blue, Darker blue (inverse so 'used' gets darker)
    elif scheme == "green":
        colors = ["#98df8a", "#2ca02c"]  # Lighter green, Darker green (inverse so 'used' gets darker)
    elif scheme == "purple":
        colors = ["#c5b0d5", "#9467bd"]  # Lighter purple, Darker purple (inverse so 'used' gets darker)
    else:
        colors = ["#1f77b4", "#ff7f0e"]  # Default blue and orange
    
    # Create mapping for the provided columns
    color_map = {}
    for i, col in enumerate(value_cols):
        if i < len(colors):
            color_map[col] = colors[i]
    
    return color_map

def create_hover_template(include_units=False, unit_text="", decimal_places=0):
    """Create a standardized hover template.
    
    Parameters:
    -----------
    include_units : bool
        Whether to include unit text in the hover
    unit_text : str
        The unit text to display
    decimal_places : int
        Number of decimal places to display
    
    Returns:
    --------
    str
        Hover template string
    """
    if decimal_places <= 0:
        # Use thousand separators for integers
        hovertemplate = (
            f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
            f"%{{x}}<br>"
            f"%{{y:,.0f}}"
        ).replace("_", " ")
    else:
        # Use decimal places for float values
        format_str = f"%.{decimal_places}f"
        hovertemplate = (
            f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
            f"%{{x}}<br>"
            f"%{{y:{format_str}}}"
        )
    
    # Add unit text if requested
    if include_units and unit_text:
        hovertemplate += f" {unit_text}"
    
    # Close the template
    hovertemplate += "</span><br><extra></extra>"
    
    return hovertemplate

def calculate_metric_forecast(df, actual_col, planned_col, condition_col=None):
    """Calculate forecast for a metric based on actual and planned values.
    
    Parameters:
    -----------
    df : DataFrame
        The data to analyze
    actual_col : str
        Column containing actual values
    planned_col : str
        Column containing planned values
    condition_col : str, optional
        Column to use for condition (defaults to actual_col)
    
    Returns:
    --------
    float
        Forecast value
    """
    if condition_col is None:
        condition_col = actual_col
    
    # Sum all existing actual values where > 0
    actual_values = df[df[condition_col] > 0][actual_col].sum()
    
    # Identify future periods where condition is zero or less
    future_periods = df[df[condition_col] <= 0]
    
    # Sum planned values for these future periods
    planned_future_values = future_periods[planned_col].sum()
    
    # Calculate forecast
    forecast = actual_values + planned_future_values
    
    return forecast

def get_project_total_metric(df, metric_col):
    """Get the total for a metric from metadata if available.
    
    Parameters:
    -----------
    df : DataFrame
        The data to analyze
    metric_col : str
        Column containing the total metric
    
    Returns:
    --------
    float or None
        Total metric value if available
    """
    if metric_col not in df.columns:
        return None
    
    # Get the first non-null value as this is metadata
    values = df[metric_col].dropna()
    if values.empty:
        return None
    
    return values.iloc[0]

def display_metrics_summary(df, value_cols, translations_map, unit_suffix, 
                            forecast_value=None, total_value=None, 
                            decimal_places=0, convert_to_millions=False,
                            forecast_label_key=None, total_label_key=None):
    """Display summary metrics with forecast and total if available.
    
    Parameters:
    -----------
    df : DataFrame
        The data to analyze
    value_cols : list
        List of columns to summarize
    translations_map : dict
        Translation mapping for column names
    unit_suffix : str
        Unit suffix for display
    forecast_value : float, optional
        Forecast value to display
    total_value : float, optional
        Total value to display
    decimal_places : int, optional
        Number of decimal places for display
    convert_to_millions : bool, optional
        Whether to convert values to millions
    forecast_label_key : str, optional
        Key for forecast label translation
    total_label_key : str, optional
        Key for total label translation
    """
    # Calculate number of columns needed
    num_cols = len(value_cols) + (1 if forecast_value is not None else 0) + (1 if total_value is not None else 0)
    
    # Create columns for metrics
    columns = st.columns(num_cols)
    
    # Display values for each value column
    for i, (col, col_display) in enumerate(zip(value_cols, columns)):
        value = df[col].sum() if col in df.columns else 0
        
        # Convert to millions if requested
        if convert_to_millions:
            value = value / 1000000
            formatted_value = f"{value:_.{decimal_places}f}".replace("_", " ") + f" {t('MNOK')}"
        else:
            formatted_value = f"{value:_.{decimal_places}f}".replace("_", " ") + f" {unit_suffix}"
        
        with col_display:
            st.metric(
                translations_map.get(col, col),
                formatted_value
            )
    
    # Add Forecast as the next column
    if forecast_value is not None:
        with columns[len(value_cols)]:
            forecast_label = t(forecast_label_key) if forecast_label_key and forecast_label_key in st.session_state.translations else "Forecast"
            
            # Format forecast value
            if convert_to_millions:
                forecast_in_millions = forecast_value / 1000000
                formatted_forecast = f"{forecast_in_millions:_.{decimal_places}f}".replace("_", " ") + f" {t('MNOK')}"
            else:
                formatted_forecast = f"{forecast_value:_.{decimal_places}f}".replace("_", " ") + f" {unit_suffix}"
                
            st.metric(
                forecast_label,
                formatted_forecast
            )

def display_monthly_breakdown(df, value_cols, translations_map, format_suffix, 
                             decimal_places=0, diff_prefix="", forecast_label_key=None, 
                             total_metric_col=None, total_label_key=None):
    """Display monthly breakdown of metrics using a dataframe.
    
    Parameters:
    -----------
    df : DataFrame
        The data to analyze
    value_cols : list
        List of columns to display
    translations_map : dict
        Translation mapping for column names
    format_suffix : str
        Suffix for formatted values
    decimal_places : int, optional
        Number of decimal places to display
    diff_prefix : str, optional
        Prefix for difference columns (e.g., 'hours_', 'fees_', 'rate_')
    forecast_label_key : str, optional
        Key for forecast label translation
    total_metric_col : str, optional
        Column name for total metric
    total_label_key : str, optional
        Key for total label translation
    """
    # Create a copy of the dataframe
    monthly_df = df.copy()
    
    # Ensure Period is datetime for proper aggregation
    if "Period" in monthly_df.columns and not pd.api.types.is_datetime64_any_dtype(monthly_df["Period"]):
        monthly_df["Period"] = pd.to_datetime(monthly_df["Period"], errors='coerce')
    
    # Check if Period_display exists, otherwise generate it
    if "Period_display" not in monthly_df.columns and "Period" in monthly_df.columns:
        monthly_df["Period_display"] = monthly_df["Period"].dt.strftime("%b %Y")
    
    # For all metrics use sum aggregation
    monthly_summary = monthly_df.groupby("Period_display")[value_cols].sum().reset_index()
    
    # Sort periods chronologically
    try:
        monthly_summary = monthly_summary.sort_values(
            "Period_display",
            key=lambda x: pd.to_datetime(x, format="%b %Y")
        )
    except (ValueError, TypeError, pd.errors.ParserError):
        # Fallback to simple sorting if datetime conversion fails
        monthly_summary = monthly_summary.sort_values("Period_display")
    
    # Check if we can calculate difference based on value_cols
    can_calculate_diff = False
    actual_col = None
    planned_col = None
    
    # Determine actual and planned columns based on value_cols names
    if "Period Hours" in value_cols and "Planned Hours" in value_cols:
        can_calculate_diff = True
        actual_col = "Period Hours"
        planned_col = "Planned Hours"
    elif "Period Fees Adjusted" in value_cols and "Planned Income" in value_cols:
        can_calculate_diff = True
        actual_col = "Period Fees Adjusted"
        planned_col = "Planned Income"
    elif "Period Hourly Rate" in value_cols and "Planned Hourly Rate" in value_cols:
        can_calculate_diff = True
        actual_col = "Period Hourly Rate"
        planned_col = "Planned Hourly Rate"
    
    # Display monthly breakdown in expandable section
    with st.expander(f"{t('monthly_breakdown') if 'monthly_breakdown' in st.session_state.translations else 'Monthly Breakdown'}"):
        # Create a new dataframe for display
        display_df = pd.DataFrame()
        display_df["Period"] = monthly_summary["Period_display"]
        
        # Add numeric columns (original values)
        for col in value_cols:
            display_df[col] = monthly_summary[col]
        
        # Calculate differences if possible
        if can_calculate_diff:
            # Add difference columns
            diff_abs_label = t(f'{diff_prefix}difference_abs') if f'{diff_prefix}difference_abs' in st.session_state.translations else 'Difference'
            diff_pct_label = t(f'{diff_prefix}difference_pct') if f'{diff_prefix}difference_pct' in st.session_state.translations else 'Difference (%)'
            
            # Calculate absolute differences
            display_df[diff_abs_label] = monthly_summary[actual_col] - monthly_summary[planned_col]
            
            # Calculate percentage differences
            display_df[diff_pct_label] = 0.0  # Default value
            mask = monthly_summary[planned_col] > 0
            if mask.any():
                display_df.loc[mask, diff_pct_label] = ((monthly_summary.loc[mask, actual_col] - 
                                                         monthly_summary.loc[mask, planned_col]) / 
                                                        monthly_summary.loc[mask, planned_col]) * 100
            
            # Add forecast column
            forecast_values = []
            for _, row in monthly_summary.iterrows():
                if row[actual_col] <= 0:  # Future period
                    forecast_values.append(row[planned_col])
                else:  # Past/current period
                    forecast_values.append(row[actual_col])
            
            forecast_label = t(forecast_label_key) if forecast_label_key and forecast_label_key in st.session_state.translations else 'Forecast'
            display_df[forecast_label] = forecast_values
        
        # Add Total metric if available
        if total_metric_col and total_metric_col in df.columns:
            total_metric_label = t(total_label_key) if total_label_key and total_label_key in st.session_state.translations else 'Total'
            
            total_metric_values = df[total_metric_col].dropna()
            if not total_metric_values.empty:
                total_metric_value = total_metric_values.iloc[0]
                display_df[total_metric_label] = total_metric_value
        
        # Order columns
        ordered_columns = ["Period"] + value_cols
        
        # Add diff and forecast columns if they exist
        if can_calculate_diff:
            diff_abs_label = t(f'{diff_prefix}difference_abs') if f'{diff_prefix}difference_abs' in st.session_state.translations else 'Difference'
            diff_pct_label = t(f'{diff_prefix}difference_pct') if f'{diff_prefix}difference_pct' in st.session_state.translations else 'Difference (%)'
            ordered_columns.extend([diff_abs_label, diff_pct_label])
            
            forecast_label = t(forecast_label_key) if forecast_label_key and forecast_label_key in st.session_state.translations else 'Forecast'
            if forecast_label in display_df.columns:
                ordered_columns.append(forecast_label)
        
        # Add Total if available
        if total_metric_col and total_metric_col in df.columns:
            total_metric_label = t(total_label_key) if total_label_key and total_label_key in st.session_state.translations else 'Total'
            if total_metric_label in display_df.columns:
                ordered_columns.append(total_metric_label)
        
        # Only include columns that exist
        filtered_ordered_columns = [col for col in ordered_columns if col in display_df.columns]
        display_df = display_df[filtered_ordered_columns]
        
        # Configure columns with translations
        column_config = {
            "Period": t("period") if "period" in st.session_state.translations else "Period"
        }
        
        # Configure numeric columns
        for col in value_cols:
            if col in display_df.columns:
                column_config[col] = st.column_config.NumberColumn(
                    label=translations_map.get(col, col),
                    format=f"%.{decimal_places}f {format_suffix}"
                )
        
        # Configure diff columns
        if can_calculate_diff:
            diff_abs_label = t(f'{diff_prefix}difference_abs') if f'{diff_prefix}difference_abs' in st.session_state.translations else 'Difference'
            diff_pct_label = t(f'{diff_prefix}difference_pct') if f'{diff_prefix}difference_pct' in st.session_state.translations else 'Difference (%)'
            
            if diff_abs_label in display_df.columns:
                column_config[diff_abs_label] = st.column_config.NumberColumn(
                    label=diff_abs_label,
                    format=f"%+.{decimal_places}f {format_suffix}"
                )
            
            if diff_pct_label in display_df.columns:
                column_config[diff_pct_label] = st.column_config.NumberColumn(
                    label=diff_pct_label,
                    format="%+.0f %%"
                )
            
            # Configure forecast column
            forecast_label = t(forecast_label_key) if forecast_label_key and forecast_label_key in st.session_state.translations else 'Forecast'
            if forecast_label in display_df.columns:
                column_config[forecast_label] = st.column_config.NumberColumn(
                    label=forecast_label,
                    format=f"%.{decimal_places}f {format_suffix}"
                )
        
        # Configure Total column if it exists
        if total_metric_col and total_metric_col in df.columns:
            total_metric_label = t(total_label_key) if total_label_key and total_label_key in st.session_state.translations else 'Total'
            if total_metric_label in display_df.columns:
                column_config[total_metric_label] = st.column_config.NumberColumn(
                    label=total_metric_label,
                    format=f"%.{decimal_places}f {format_suffix}"
                )
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )

def display_project_breakdown(df, value_cols, translations_map, format_suffix="", decimal_places=1, diff_prefix="", forecast_label_key=None, total_metric_col=None, total_label_key=None, agg_type=None):
    """Display project breakdown with detailed metrics.
    
    Parameters:
    -----------
    df : DataFrame
        The data to analyze
    value_cols : list
        List of columns to display
    translations_map : dict
        Translation mapping for column names
    format_suffix : str
        Suffix for formatted values
    decimal_places : int
        Number of decimal places to display
    diff_prefix : str
        Prefix for difference columns
    forecast_label_key : str, optional
        Key for forecast label translation
    total_metric_col : str, optional
        Column name for total metric
    total_label_key : str, optional
        Key for total label translation
    agg_type : str or dict, optional
        Aggregation type ("sum", "mean") or dict mapping column names to aggregation types
    """
    if df.empty:
        return
    
    # Create summary
    with st.expander(t('project_breakdown')):
        # Get unique projects
        projects = df["Project Name"].unique()
        
        # Create a DataFrame to store project metrics
        metrics_df = pd.DataFrame(index=projects)
        
        # Determine the appropriate aggregation method for each column
        def get_agg_method(col_name):
            # If agg_type is provided as a dictionary, use it
            if isinstance(agg_type, dict) and col_name in agg_type:
                return agg_type[col_name]
            
            # If agg_type is provided as a string, use it for all columns
            if isinstance(agg_type, str):
                return agg_type
            
            # Auto-detect based on column name:
            # Use mean for rate columns, sum for others
            if "rate" in col_name.lower():
                return "mean"
            else:
                return "sum"
        
        # Calculate metrics for each project
        for project in projects:
            project_data = df[df["Project Name"] == project]
            
            # Calculate standard metrics using appropriate aggregation
            for col in value_cols:
                if col in project_data.columns:
                    agg_method = get_agg_method(col)
                    
                    if agg_method == "mean":
                        metrics_df.at[project, col] = project_data[col].mean()
                    else:  # default to sum
                        metrics_df.at[project, col] = project_data[col].sum()
            
            # Add Total metric if available
            if total_metric_col and total_metric_col in project_data.columns:
                total_metric_values = project_data[total_metric_col].dropna()
                if not total_metric_values.empty:
                    total_metric_value = total_metric_values.iloc[0]
                    metrics_df.at[project, "Total"] = total_metric_value
        
        # Calculate forecast correctly for each project
        if forecast_label_key:
            for project_name in projects:
                # Use a different variable name to avoid overriding the outer project_data
                project_specific_data = df[df["Project Name"] == project_name]
                
                # Check if we're dealing with rates
                is_rate_calculation = any("rate" in col.lower() for col in value_cols)
                
                if is_rate_calculation:
                    # For rates, calculate weighted average
                    # Use calculate_metric_forecast for both hours and fees
                    forecast_hours = calculate_metric_forecast(project_specific_data, "Period Hours", "Planned Hours")
                    forecast_fees = calculate_metric_forecast(project_specific_data, "Period Fees Adjusted", "Planned Income")
                    
                    # Calculate rate as weighted average
                    project_forecast = 0
                    if forecast_hours > 0:
                        project_forecast = forecast_fees / forecast_hours
                else:
                    # For hours and fees, use the standard forecast calculation
                    if len(value_cols) >= 2:
                        actual_col = value_cols[1]  # "Period Hours" or "Period Fees Adjusted"
                        planned_col = value_cols[0]  # "Planned Hours" or "Planned Income"
                        project_forecast = calculate_metric_forecast(project_specific_data, actual_col, planned_col)
                    else:
                        project_forecast = 0
                
                metrics_df.at[project_name, "Forecast"] = project_forecast
                
        # Calculate differences between actual and planned values
        can_calculate_diff = False
        actual_col = None
        planned_col = None
        
        # Determine actual and planned columns based on value_cols
        if len(value_cols) >= 2:
            # For hours and fees, assume second column is actual, first is planned
            if "Hours" in value_cols[0] and "Hours" in value_cols[1]:
                can_calculate_diff = True
                planned_col = value_cols[0]  # Usually "Planned Hours"
                actual_col = value_cols[1]   # Usually "Period Hours"
            elif "Income" in value_cols[0] and "Fees" in value_cols[1]:
                can_calculate_diff = True
                planned_col = value_cols[0]  # Usually "Planned Income"
                actual_col = value_cols[1]   # Usually "Period Fees Adjusted"
            elif "Rate" in value_cols[0] and "Rate" in value_cols[1]:
                can_calculate_diff = True
                planned_col = value_cols[0]  # Usually "Planned Hourly Rate"
                actual_col = value_cols[1]   # Usually "Period Hourly Rate"
        
        # Calculate absolute and percentage differences if possible
        if can_calculate_diff:
            # Calculate and store differences
            metrics_df["diff_abs"] = metrics_df[actual_col] - metrics_df[planned_col]
            
            # Calculate percentage differences (avoiding division by zero)
            metrics_df["diff_pct"] = 0.0
            for project in projects:
                planned = metrics_df.at[project, planned_col]
                if planned > 0:
                    actual = metrics_df.at[project, actual_col]
                    metrics_df.at[project, "diff_pct"] = ((actual - planned) / planned) * 100

        # Don't create formatted string columns, instead keep original numeric columns
        display_cols = []
        for col in value_cols:
            if col in metrics_df.columns:
                display_cols.append(col)

        # Add difference columns if available
        if can_calculate_diff:
            display_cols.extend(["diff_abs", "diff_pct"])

        # Add forecast column if available
        if "Forecast" in metrics_df.columns:
            display_cols.append("Forecast")

        # Add total column if available
        if "Total" in metrics_df.columns:
            display_cols.append("Total")

        # Use the numeric columns for the display DataFrame
        display_df = metrics_df[display_cols].copy()

        # Reset index to make Project Name a column
        display_df = display_df.reset_index().rename(columns={"index": "Project Name"})

        # Create column configuration for proper formatting in display
        column_config = {
            "Project Name": st.column_config.TextColumn(
                "Project Name"
            )
        }

        # Configure numeric columns with proper formatting
        for col in value_cols:
            if col in display_df.columns:
                column_config[col] = st.column_config.NumberColumn(
                    label=translations_map.get(col, col),
                    format=f"%.{decimal_places}f {format_suffix}"
                )

        # Configure difference columns if available
        if can_calculate_diff:
            diff_abs_label = t(f'{diff_prefix}difference_abs') if f'{diff_prefix}difference_abs' in st.session_state.translations else 'Difference'
            diff_pct_label = t(f'{diff_prefix}difference_pct') if f'{diff_prefix}difference_pct' in st.session_state.translations else 'Difference (%)'
            
            column_config["diff_abs"] = st.column_config.NumberColumn(
                label=diff_abs_label,
                format=f"%+.{decimal_places}f {format_suffix}"
            )
            
            column_config["diff_pct"] = st.column_config.NumberColumn(
                label=diff_pct_label,
                format="%+.1f %%"
            )

        # Configure forecast column if available
        if "Forecast" in display_df.columns:
            forecast_label = t(forecast_label_key) if forecast_label_key and forecast_label_key in st.session_state.translations else 'Forecast'
            column_config["Forecast"] = st.column_config.NumberColumn(
                label=forecast_label,
                format=f"%.{decimal_places}f {format_suffix}"
            )

        # Configure total column if available
        if "Total" in display_df.columns:
            total_label = t(total_label_key) if total_label_key and total_label_key in st.session_state.translations else 'Total'
            column_config["Total"] = st.column_config.NumberColumn(
                label=total_label,
                format=f"%.{decimal_places}f {format_suffix}"
            )

        # Display the table with proper numeric sorting and formatting
        st.dataframe(
            display_df,
            hide_index=True,
            use_container_width=True,
            column_config=column_config
        )

def prepare_project_dataframe(df):
    """Prepare dataframe for project visualizations.
    
    Parameters:
    -----------
    df : DataFrame
        The data to prepare
    
    Returns:
    --------
    DataFrame
        Prepared dataframe with additional columns
    """
    # Create a copy to avoid modifying the original
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper aggregation
    if "Period" in df_copy.columns and not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Add Period_display column if it doesn't exist
    if "Period" in df_copy.columns and "Period_display" not in df_copy.columns:
        df_copy["Period_display"] = df_copy["Period"].dt.strftime("%b %Y")
    
    return df_copy

def create_translation_map(value_cols, prefix):
    """Create translation mapping for value columns.
    
    Parameters:
    -----------
    value_cols : list
        List of column names to translate
    prefix : str
        Prefix for translation keys
    
    Returns:
    --------
    dict
        Mapping of column names to translated names
    """
    translations_map = {}
    for col in value_cols:
        key = f"{prefix}_{col.lower().replace(' ', '_')}"
        translations_map[col] = t(key) if key in st.session_state.translations else col
    
    return translations_map

def display_project_per_month_breakdown(df, value_cols, translations_map, format_suffix='', decimal_places=2, diff_prefix="", forecast_label_key=None, total_metric_col=None, total_label_key=None):
    """
    Display project per month breakdown showing individual project entries organized by month.
    
    Parameters:
    -----------
    df : pd.DataFrame
        DataFrame with project data
    value_cols : list
        List of column names to display
    translations_map : dict
        Mapping of column names to translated names
    format_suffix : str, optional
        Suffix to add to formatted values (e.g., 'hrs', 'NOK')
    decimal_places : int, optional
        Number of decimal places for formatting
    diff_prefix : str, optional
        Prefix for difference calculation translation keys
    forecast_label_key : str, optional
        Key for forecast label translation
    total_metric_col : str, optional
        Name of column containing total metric values
    total_label_key : str, optional
        Key for total label translation
    """
    if df.empty:
        return
    
    # Create project per month breakdown
    with st.expander(t('project_per_month_breakdown') if 'project_per_month_breakdown' in st.session_state.translations else "Project per Month"):
        # Ensure Period is datetime for proper sorting
        df_copy = df.copy()
        if "Period" in df_copy.columns and not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
            df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
        
        # Sort by Period and Project Name
        df_sorted = df_copy.sort_values(["Period", "Project Name"])
        
        # Create display dataframe
        display_df = pd.DataFrame()
        display_df["Period"] = df_sorted["Period_display"] if "Period_display" in df_sorted.columns else df_sorted["Period"].dt.strftime('%Y-%m')
        display_df["Project Name"] = df_sorted["Project Name"]
        
        # Add value columns
        for col in value_cols:
            if col in df_sorted.columns:
                display_df[col] = df_sorted[col]
        
        # Calculate variance if we have planned vs actual columns
        can_calculate_diff = False
        if len(value_cols) >= 2:
            # Check for hours: Planned Hours vs Period Hours
            if "Planned Hours" in value_cols and "Period Hours" in value_cols:
                can_calculate_diff = True
                planned_col = "Planned Hours"
                actual_col = "Period Hours"
            # Check for fees: Planned Income vs Period Fees Adjusted
            elif "Planned Income" in value_cols and "Period Fees Adjusted" in value_cols:
                can_calculate_diff = True
                planned_col = "Planned Income"
                actual_col = "Period Fees Adjusted"
            # Check for rates: Planned Rate vs Period Rate
            elif "Rate" in value_cols[0] and "Rate" in value_cols[1]:
                can_calculate_diff = True
                planned_col = value_cols[0]  # Usually "Planned Hourly Rate"
                actual_col = value_cols[1]   # Usually "Period Hourly Rate"
        
        # Calculate differences if possible
        if can_calculate_diff:
            display_df["Variance"] = display_df[actual_col] - display_df[planned_col]
            # Calculate percentage variance (avoiding division by zero)
            display_df["Variance %"] = 0.0
            mask = display_df[planned_col] != 0
            display_df.loc[mask, "Variance %"] = ((display_df.loc[mask, actual_col] - display_df.loc[mask, planned_col]) / display_df.loc[mask, planned_col]) * 100
        
        # Create column configuration for proper formatting
        column_config = {
            "Period": st.column_config.TextColumn("Period"),
            "Project Name": st.column_config.TextColumn("Project Name")
        }
        
        # Configure numeric columns with proper formatting
        for col in value_cols:
            if col in display_df.columns:
                translated_col = translations_map.get(col, col)
                if "rate" in col.lower():
                    column_config[col] = st.column_config.NumberColumn(
                        translated_col,
                        format=f"%.{decimal_places}f {format_suffix}".strip()
                    )
                else:
                    column_config[col] = st.column_config.NumberColumn(
                        translated_col,
                        format=f"%.{decimal_places}f {format_suffix}".strip()
                    )
        
        # Configure variance columns if they exist
        if "Variance" in display_df.columns:
            column_config["Variance"] = st.column_config.NumberColumn(
                "Variance",
                format=f"%.{decimal_places}f {format_suffix}".strip()
            )
        
        if "Variance %" in display_df.columns:
            column_config["Variance %"] = st.column_config.NumberColumn(
                "Variance %",
                format="%.1f%%"
            )
        
        # Display the dataframe
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=column_config
        )
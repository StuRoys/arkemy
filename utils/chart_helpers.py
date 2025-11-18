# chart_helpers.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from datetime import datetime
import numpy as np
from utils.chart_styles import SUM_METRICS


def build_treemap_texttemplate(metric, has_percentage_column):
    """
    Build the texttemplate for treemap tiles based on whether percentage data exists.

    Args:
        metric: Name of the metric being visualized
        has_percentage_column: Boolean indicating if percentage column exists for this metric

    Returns:
        Text template string for treemap tiles
    """
    if has_percentage_column:
        # Show label + percentage on separate line, 1 decimal place
        # customdata[19] is the percentage column index (added at the end)
        return '%{label}<br>%{customdata[19]:.1f}%'
    else:
        # Default: just show label
        return '%{label}'


def create_standardized_customdata(df):
    """
    Creates standardized custom data array for consistent hover templates.
    
    Args:
        df: DataFrame containing project or monthly metrics
        
    Returns:
        List of lists to be used as custom_data in Plotly charts
    """
    custom_data = []
    
    # [0] Hours worked
    custom_data.append(df["hours_used"])
    
    # [1] Billable hours
    if "hours_billable" in df.columns:
        custom_data.append(df["hours_billable"])
    else:
        custom_data.append([0] * len(df))
    
    # [2] Billability %
    if "Billability %" in df.columns:
        custom_data.append(df["Billability %"])
    else:
        custom_data.append([0] * len(df))
    
    # [3] Number of people/projects
    if "Number of people" in df.columns:
        custom_data.append(df["Number of people"])
    else:
        custom_data.append([0] * len(df))
    
    # [4] Billable rate
    if "Billable rate" in df.columns:
        custom_data.append(df["Billable rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [5] Effective rate
    if "Effective rate" in df.columns:
        custom_data.append(df["Effective rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [6] Fee
    if "Fee" in df.columns:
        custom_data.append(df["Fee"])
    else:
        custom_data.append([0] * len(df))
    
    # [7] Planned hours
    if "planned_hours" in df.columns:
        custom_data.append(df["planned_hours"])
    else:
        custom_data.append([0] * len(df))
    
    # [8] Planned rate
    if "planned_hourly_rate" in df.columns:
        custom_data.append(df["planned_hourly_rate"])
    else:
        custom_data.append([0] * len(df))
    
    # [9] planned_fee
    if "planned_fee" in df.columns:
        custom_data.append(df["planned_fee"])
    else:
        custom_data.append([0] * len(df))
    
    # [10] Hours variance (absolute)
    if "Hours variance" in df.columns:
        custom_data.append(df["Hours variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [11] Hours variance (%)
    if "Variance percentage" in df.columns:
        custom_data.append(df["Variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    # [12] Rate variance (absolute)
    if "Rate variance" in df.columns:
        custom_data.append(df["Rate variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [13] Rate variance (%)
    if "Rate variance percentage" in df.columns:
        custom_data.append(df["Rate variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    # [14] Fee variance (absolute)
    if "Fee variance" in df.columns:
        custom_data.append(df["Fee variance"])
    else:
        custom_data.append([0] * len(df))
    
    # [15] Fee variance (%)
    if "Fee variance percentage" in df.columns:
        custom_data.append(df["Fee variance percentage"])
    else:
        custom_data.append([0] * len(df))
    
    # [16] Total cost
    if "Total cost" in df.columns:
        custom_data.append(df["Total cost"])
    else:
        custom_data.append([0] * len(df))
    
    # [17] Total profit
    if "Total profit" in df.columns:
        custom_data.append(df["Total profit"])
    else:
        custom_data.append([0] * len(df))
    
    # [18] Profit margin %
    if "Profit margin %" in df.columns:
        custom_data.append(df["Profit margin %"])
    else:
        custom_data.append([0] * len(df))

    # [19] Percentage column (dynamically determined)
    # This will be populated by the caller if a percentage column exists
    # For now, add a placeholder that the treemap logic will replace
    custom_data.append([0] * len(df))

    return custom_data

# Replace the create_comparison_chart function in chart_helpers.py with this version

def create_comparison_chart(df, primary_metric, comparison_metric, title, y_axis_label, x_field="project_name"):
    """
    Creates a comparison bar chart between two metrics.
    
    Args:
        df: DataFrame with project/month data
        primary_metric: Name of the primary metric (e.g., "hours_used")
        comparison_metric: Name of the comparison metric (e.g., "planned_hours")
        title: Chart title
        y_axis_label: Label for Y axis
        x_field: Field to use for x-axis categories, defaults to "project_name"
        
    Returns:
        Plotly figure with grouped bar chart
    """
    # Check if x_field is a Series (not a string column name)
    # If it is, create a temporary column to use for indexing
    temp_df = df.copy()
    if not isinstance(x_field, str):
        # Create a temporary column for the x-axis labels
        temp_df["_temp_x_axis_"] = x_field
        x_field_name = "_temp_x_axis_"
    else:
        x_field_name = x_field
    
    # Prepare data for comparison chart
    comparison_df = temp_df[[x_field_name, primary_metric, comparison_metric]].copy()
    
    # Sort by primary metric in descending order
    comparison_df = comparison_df.sort_values(primary_metric, ascending=False)
    
    # Add a slider to control number of items to display if we have more than one
    if len(comparison_df) > 1 and x_field_name == "project_name":  # Only show slider for Project view
        num_items = st.slider(
            f"Number of {x_field_name.lower()}s to display:",
            min_value=1,
            max_value=min(1000, len(comparison_df)),
            value=min(10, len(comparison_df)),
            step=1,
            key="item_count_slider"
        )
        # Limit the number of items based on slider
        comparison_df = comparison_df.head(num_items)
    
    # Create standardized custom data for rich hover templates
    # Use the original temp_df (before melting) to preserve all metrics
    custom_data = create_standardized_customdata(temp_df)
    
    # Convert from wide to long format for grouped bar chart
    comparison_long_df = pd.melt(
        comparison_df,
        id_vars=[x_field_name],
        value_vars=[primary_metric, comparison_metric],
        var_name="Metric",
        value_name=y_axis_label
    )
    
    # Create color scheme based on metrics - use different colors for cost/profit
    if "cost" in primary_metric.lower() or "profit" in primary_metric.lower():
        if "profit" in primary_metric.lower():
            # Use red/green for profit comparisons
            color_scheme = ["#d62728", "#2ca02c"]  # Red for actual, Green for planned
        else:
            # Use orange/blue for cost comparisons
            color_scheme = ["#ff7f0e", "#1f77b4"]  # Orange for actual, Blue for planned
    else:
        # Default green/blue for other comparisons
        color_scheme = ["#2ca02c", "#1f77b4"]  # Green for primary, Blue for comparison
    
    # Create a grouped bar chart
    fig = px.bar(
        comparison_long_df,
        x=x_field_name,
        y=y_axis_label,
        color="Metric",
        barmode="group",
        title=title,
        color_discrete_sequence=color_scheme
    )
    
    # Add the rich custom data to each trace for detailed hover templates
    # Need to duplicate custom data for each unique x value since we have two bars per item
    unique_x_values = comparison_long_df[x_field_name].unique()
    
    # Create mapping from x_field_name back to original dataframe rows
    for i, trace in enumerate(fig.data):
        trace_custom_data = []
        for x_val in trace.x:
            # Find the row index in temp_df that matches this x value
            row_idx = temp_df[temp_df[x_field_name] == x_val].index[0] if len(temp_df[temp_df[x_field_name] == x_val]) > 0 else 0
            # Get the custom data for this row
            row_custom_data = [custom_data[j][row_idx] if row_idx < len(custom_data[j]) else 0 for j in range(len(custom_data))]
            trace_custom_data.append(row_custom_data)
        
        trace.customdata = trace_custom_data
    
    # Improve layout for better readability
    fig.update_layout(
        xaxis_title="",
        yaxis_title=y_axis_label,
        xaxis={'categoryorder':'total descending'},
        legend_title_text=""
    )
    
    return fig

def create_single_metric_chart(df, metric, title, chart_type="bar", x_field="project_name", sort_by=None):
    """
    Creates a single metric visualization (bar chart or treemap).
    
    Args:
        df: DataFrame with project/month data
        metric: Name of the metric to visualize
        title: Chart title
        chart_type: 'bar' or 'treemap'
        x_field: Field to use for x-axis or path (for treemap)
        sort_by: Optional column to sort by (for bar charts)
        
    Returns:
        Plotly figure
    """
    # Choose color scheme based on metric type
    if "cost" in metric.lower():
        color_scale = "Oranges"
    elif "profit" in metric.lower():
        # For profit, use a diverging color scale to handle negative values
        color_scale = "RdYlGn"  # Red-Yellow-Green scale
    elif "Planned" in metric:
        color_scale = "Blues"
    else:
        color_scale = "Greens"
    
    # For bar charts
    if chart_type == "bar":
        # Sort data if specified
        if sort_by:
            df = df.sort_values(sort_by, ascending=False)
        
        # Add a slider to control number of items if we have more than one
        if len(df) > 1 and x_field == "project_name":  # Only show slider for Project view
            num_items = st.slider(
                f"Number of {x_field.lower()}s to display:",
                min_value=1,
                max_value=min(1000, len(df)),
                value=min(10, len(df)),
                step=1,
                key="item_count_slider"
            )
            # Limit the number of items based on slider
            limited_df = df.head(num_items)
        else:
            limited_df = df
        
        # Get customdata for hover AFTER limiting the dataframe
        custom_data = create_standardized_customdata(limited_df)
        
        # Create the bar chart
        fig = px.bar(
            limited_df,
            x=x_field,
            y=metric,
            color=metric,
            color_continuous_scale=color_scale,
            title=title,
            custom_data=custom_data
        )
        
        # Improve layout for better readability
        fig.update_layout(
            xaxis_title="",
            yaxis_title=metric,
            xaxis={'categoryorder':'total descending'}
        )
    
    # For treemaps
    elif chart_type == "treemap":
        # Build hierarchical structure for go.Treemap
        ids = ["root"]
        labels = ["All Items"]
        parents = [""]
        values_list = [0]  # Will be summed from children
        customdata_list = [[0] * 20]  # Root customdata placeholder (19 + percentage)

        # Check if percentage column exists for this metric
        pct_column = f'{metric}_pct'
        has_percentage = pct_column in df.columns

        # Add all items as children of root
        root_total = 0
        for idx, row in df.iterrows():
            item_id = f"item_{row[x_field]}"
            ids.append(item_id)
            labels.append(str(row[x_field]))
            parents.append("root")
            val = row[metric]
            values_list.append(val)
            root_total += val

        # Set root value to sum of children
        values_list[0] = root_total if root_total > 0 else 1

        # Build customdata for all items
        customdata_for_root = [0] * 20
        customdata_list = [customdata_for_root]

        # Add customdata for each item
        custom_data_arrays = create_standardized_customdata(df)
        for i in range(len(df)):
            row_customdata = []
            for arr in custom_data_arrays:
                if i < len(arr):
                    # Handle both pandas Series and regular lists
                    val = arr.iloc[i] if isinstance(arr, pd.Series) else arr[i]
                    row_customdata.append(val)
                else:
                    row_customdata.append(0)
            customdata_list.append(row_customdata)

        # Add percentage values if they exist (index [19])
        if has_percentage:
            for i, pct_val in enumerate(df[pct_column], 1):  # Start from 1 to skip root
                if i < len(customdata_list):
                    customdata_list[i][19] = pct_val

        # Create color array using Plotly's color scale
        min_val = df[metric].min()
        max_val = df[metric].max()

        # Normalize values for color mapping (clamp to [0, 1])
        if max_val > min_val:
            normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
        else:
            normalized = [0.5] * len(values_list)

        # Sample the color scale
        colors_scale = pc.sample_colorscale(color_scale, normalized)

        # Build text template based on percentage availability
        texttemplate = build_treemap_texttemplate(metric, has_percentage)

        # Create treemap using graph_objects
        fig = go.Figure(data=[go.Treemap(
            ids=ids,
            labels=labels,
            parents=parents,
            values=values_list,
            customdata=customdata_list,
            texttemplate=texttemplate,
            marker=dict(
                colors=colors_scale,
                line=dict(width=2, color="white")
            ),
            textposition="middle center",
            branchvalues="total"
        )])

        fig.update_layout(
            title=title,
            height=420,
            margin=dict(l=20, r=20, t=40, b=20)
        )

    return fig

def filter_projects_by_metric(df, metric, planned_metric=None, is_comparison_view=False):
    """
    Filters projects based on selected metric or for comparison view.
    
    Args:
        df: DataFrame with project data
        metric: Name of the primary metric
        planned_metric: Name of the comparison metric (for comparison views)
        is_comparison_view: Whether this is a comparison view
        
    Returns:
        Filtered DataFrame
    """
    if is_comparison_view and planned_metric:
        # For comparison view, include projects with either metric > 0
        # Special handling for profit which can be negative
        if "profit" in metric.lower():
            return df[(df[metric] != 0) | (df[planned_metric] != 0)]
        else:
            return df[(df[metric] > 0) | (df[planned_metric] > 0)]
    else:
        # For single metric view, filter projects with metric > 0
        # Special handling for profit which can be negative
        if "profit" in metric.lower():
            return df[df[metric] != 0]  # Include negative profits
        else:
            return df[df[metric] > 0]

def create_forecast_chart(monthly_data):
    """
    Creates a forecast hours chart that shows accumulated hours over time.
    
    Args:
        monthly_data: DataFrame with monthly hours data
        
    Returns:
        Plotly figure with the forecast chart
    """
    # Get current month and year for comparison
    current_date = datetime.now().date()
    current_year = current_date.year
    current_month = current_date.month
    
    # Create a copy of the monthly data to calculate forecast
    forecast_df = monthly_data.copy()
    
    # Create a column to indicate if the month is in the past or future
    forecast_df["Time Period"] = forecast_df.apply(
        lambda row: "Actual" if (row["Year"] < current_year or 
                               (row["Year"] == current_year and row["Month"] < current_month)) 
                        else "Planned",
        axis=1
    )
    
    # Create the forecast column using hours worked for past months and planned hours for future
    forecast_df["Month Value"] = forecast_df.apply(
        lambda row: row["hours_used"] if row["Time Period"] == "Actual" else row["planned_hours"],
        axis=1
    )
    
    # Make sure the data is sorted chronologically
    forecast_df = forecast_df.sort_values(["Year", "Month"])
    
    # Calculate the cumulative sum of forecast values
    forecast_df["Accumulated Forecast"] = forecast_df["Month Value"].cumsum()
    
    # Create the bar chart
    fig = px.bar(
        forecast_df,
        x=forecast_df["Month name"] + " " + forecast_df["Year"].astype(str),
        y="Accumulated Forecast",
        color="Time Period",
        color_discrete_map={"Actual": "#2ca02c", "Planned": "#1f77b4"},  # Green for past, Blue for future
        title="Accumulated Hours Forecast by Month",
        text=forecast_df["Accumulated Forecast"].round(0).astype(int)
    )
    
    # Create custom hover data
    hover_template = "<b>%{x}</b><br><br>"
    hover_template += "Month's Value: %{text} hours<br>"
    hover_template += "Accumulated Forecast: %{y:,.1f} hours<br>"
    hover_template += "<extra></extra>"  # Hide secondary tooltip
    
    # Ensure x-axis is in chronological order and apply hover template
    month_labels = monthly_data["Month name"] + " " + monthly_data["Year"].astype(str)
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Accumulated Hours",
        xaxis={'categoryorder': 'array', 'categoryarray': month_labels}
    )
    
    fig.update_traces(hovertemplate=hover_template)
    
    # Adjust text position and format
    fig.update_traces(textposition='inside', textangle=0)
    
    return fig, forecast_df

def create_monthly_metrics_chart(monthly_data, selected_metric, month_labels):
    """
    Creates a single metric monthly bar chart.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        selected_metric: The metric to plot
        month_labels: Labels for the x-axis
        
    Returns:
        Plotly figure with the monthly metrics chart
    """
    # Choose color scheme based on metric type
    if "cost" in selected_metric.lower():
        color_scale = "Oranges"
    elif "profit" in selected_metric.lower():
        color_scale = "RdYlGn"  # Red-Yellow-Green for profit (handles negatives)
    elif "Planned" in selected_metric:
        color_scale = "Blues"
    else:
        color_scale = "Greens"
    
    # Get standardized customdata for hover templating
    custom_data = create_standardized_customdata(monthly_data)
    
    fig = px.bar(
        monthly_data,
        x=month_labels,
        y=selected_metric,
        color=selected_metric,
        color_continuous_scale=color_scale,
        title=f"{selected_metric} by Month for Selected Projects",
        custom_data=custom_data
    )
                
    # Improve layout
    fig.update_layout(
        xaxis_title="Month",
        yaxis_title=selected_metric,
        xaxis={'categoryorder': 'array', 'categoryarray': month_labels},
        hovermode="closest"
    )
    
    return fig

# Import the standardize_column_order function
from utils.chart_styles import standardize_column_order

def create_summary_metrics_table(monthly_data, has_planned_data=False):
    """
    Creates a summary metrics table with totals across all time periods.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with summary metrics
    """
    # Calculate summary metrics from monthly data
    summary_metrics = {
        "hours_used": monthly_data["hours_used"].sum(),
        "hours_billable": monthly_data["hours_billable"].sum(),
        "Billability %": (monthly_data["hours_billable"].sum() / monthly_data["hours_used"].sum() * 100) if monthly_data["hours_used"].sum() > 0 else 0,
    }
    
    # Add fee
    if "Fee" in monthly_data.columns:
        summary_metrics["Fee"] = monthly_data["Fee"].sum()
    
    # Add cost and profit metrics
    if "Total cost" in monthly_data.columns:
        summary_metrics["Total cost"] = monthly_data["Total cost"].sum()
    
    if "Total profit" in monthly_data.columns:
        summary_metrics["Total profit"] = monthly_data["Total profit"].sum()
        
        # Calculate profit margin
        if "Fee" in summary_metrics and summary_metrics["Fee"] > 0:
            summary_metrics["Profit margin %"] = (summary_metrics["Total profit"] / summary_metrics["Fee"]) * 100
        else:
            summary_metrics["Profit margin %"] = 0
    
    # Weighted average for billable rate (weighted by billable hours)
    if "Billable rate" in monthly_data.columns and "hours_billable" in monthly_data.columns:
        billable_sum = monthly_data["hours_billable"].sum()
        summary_metrics["Billable rate"] = (monthly_data["Billable rate"] * monthly_data["hours_billable"]).sum() / billable_sum if billable_sum > 0 else 0
    else:
        summary_metrics["Billable rate"] = 0
        
    # Weighted average for effective rate (weighted by hours worked)
    if "Effective rate" in monthly_data.columns:
        hours_sum = monthly_data["hours_used"].sum()
        summary_metrics["Effective rate"] = (monthly_data["Effective rate"] * monthly_data["hours_used"]).sum() / hours_sum if hours_sum > 0 else 0
    else:
        summary_metrics["Effective rate"] = 0
    
    # Add planned metrics if available
    if has_planned_data:
        if "planned_hours" in monthly_data.columns:
            summary_metrics["planned_hours"] = monthly_data["planned_hours"].sum()
            summary_metrics["Hours variance"] = summary_metrics["hours_used"] - summary_metrics["planned_hours"]
            if summary_metrics["planned_hours"] > 0:
                summary_metrics["Variance percentage"] = (summary_metrics["Hours variance"] / summary_metrics["planned_hours"]) * 100
            
        if "planned_hourly_rate" in monthly_data.columns:
            planned_hours_sum = monthly_data["planned_hours"].sum() if "planned_hours" in monthly_data.columns else 0
            if planned_hours_sum > 0:
                summary_metrics["planned_hourly_rate"] = (monthly_data["planned_hourly_rate"] * monthly_data["planned_hours"]).sum() / planned_hours_sum
                if "Effective rate" in summary_metrics:
                    summary_metrics["Rate variance"] = summary_metrics["Effective rate"] - summary_metrics["planned_hourly_rate"]
                    if summary_metrics["planned_hourly_rate"] > 0:
                        summary_metrics["Rate variance percentage"] = (summary_metrics["Rate variance"] / summary_metrics["planned_hourly_rate"]) * 100
            
        if "planned_fee" in monthly_data.columns:
            summary_metrics["planned_fee"] = monthly_data["planned_fee"].sum()
            if "Fee" in summary_metrics:
                summary_metrics["Fee variance"] = summary_metrics["Fee"] - summary_metrics["planned_fee"]
                if summary_metrics["planned_fee"] > 0:
                    summary_metrics["Fee variance percentage"] = (summary_metrics["Fee variance"] / summary_metrics["planned_fee"]) * 100
    
    # Convert to DataFrame for display
    summary_df = pd.DataFrame([summary_metrics])
    
    # Standardize column order before returning
    return standardize_column_order(summary_df)

def create_yearly_metrics_table(monthly_data, filtered_df, has_planned_data=False):
    """
    Creates a yearly metrics table aggregated by year.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        filtered_df: Original filtered DataFrame with time records
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with yearly metrics
    """
    # Group by Year and aggregate
    yearly_data = monthly_data.groupby('Year').agg({
        'hours_used': 'sum',
        'hours_billable': 'sum',
        'Month': 'count'  # Count of months with data
    })

    # Calculate Billability % for each year
    yearly_data['Billability %'] = (yearly_data['hours_billable'] / yearly_data['hours_used'] * 100)

    # Add fee, cost, and profit aggregations
    if 'Fee' in monthly_data.columns:
        yearly_data['Fee'] = monthly_data.groupby('Year')['Fee'].sum()
    
    if 'Total cost' in monthly_data.columns:
        yearly_data['Total cost'] = monthly_data.groupby('Year')['Total cost'].sum()
    
    if 'Total profit' in monthly_data.columns:
        yearly_data['Total profit'] = monthly_data.groupby('Year')['Total profit'].sum()
        
        # Calculate profit margin for each year
        if 'Fee' in yearly_data.columns:
            yearly_data['Profit margin %'] = 0.0
            mask = yearly_data['Fee'] > 0
            yearly_data.loc[mask, 'Profit margin %'] = (yearly_data.loc[mask, 'Total profit'] / yearly_data.loc[mask, 'Fee'] * 100)

    # Calculate weighted averages for rates if available
    if 'Effective rate' in monthly_data.columns:
        # Weighted average - effective rate weighted by hours worked
        yearly_rates = monthly_data.groupby('Year').apply(
            lambda x: (x['Effective rate'] * x['hours_used']).sum() / x['hours_used'].sum() 
            if x['hours_used'].sum() > 0 else 0
        )
        yearly_data['Effective rate'] = yearly_rates

    if 'Billable rate' in monthly_data.columns:
        # Weighted average - billable rate weighted by billable hours
        yearly_billable_rates = monthly_data.groupby('Year').apply(
            lambda x: (x['Billable rate'] * x['hours_billable']).sum() / x['hours_billable'].sum() 
            if x['hours_billable'].sum() > 0 else 0
        )
        yearly_data['Billable rate'] = yearly_billable_rates

    # Add unique projects count per year
    # Create a temporary dataframe with year and unique project counts
    yearly_projects = filtered_df.groupby(pd.Grouper(key='record_date', freq='Y')).agg({
        'project_number': 'nunique'
    }).reset_index()
    yearly_projects['Year'] = yearly_projects['record_date'].dt.year
    
    # Create a mapping dictionary and apply it to yearly_data
    yearly_projects_dict = dict(zip(yearly_projects['Year'], yearly_projects['project_number']))
    
    # Make sure yearly_data has Year as a column for mapping
    if isinstance(yearly_data.index, pd.Index) and yearly_data.index.name == 'Year':
        yearly_data = yearly_data.reset_index()
    
    # Map the unique project counts
    yearly_data['Unique projects'] = yearly_data['Year'].map(yearly_projects_dict)

    # Add planned data metrics if available
    if has_planned_data:
        if 'Planned hours' in monthly_data.columns:
            yearly_data['Planned hours'] = monthly_data.groupby('Year')['Planned hours'].sum()
            yearly_data['Hours variance'] = yearly_data['hours_used'] - yearly_data['Planned hours']
            yearly_data['Variance percentage'] = (yearly_data['Hours variance'] / yearly_data['Planned hours'] * 100) \
                .where(yearly_data['Planned hours'] > 0, 0)
                
        if 'Planned rate' in monthly_data.columns:
            # Weighted average for planned rate
            yearly_planned_rates = monthly_data.groupby('Year').apply(
                lambda x: (x['Planned rate'] * x['Planned hours']).sum() / x['Planned hours'].sum() 
                if x['Planned hours'].sum() > 0 else 0
            )
            yearly_data['Planned rate'] = yearly_planned_rates
            
            if 'Effective rate' in yearly_data.columns:
                yearly_data['Rate variance'] = yearly_data['Effective rate'] - yearly_data['Planned rate']
                yearly_data['Rate variance percentage'] = (yearly_data['Rate variance'] / yearly_data['Planned rate'] * 100) \
                    .where(yearly_data['Planned rate'] > 0, 0)
                
        if 'planned_fee' in monthly_data.columns:
            yearly_data['planned_fee'] = monthly_data.groupby('Year')['planned_fee'].sum()
            
            if 'Fee' in yearly_data.columns:
                yearly_data['Fee variance'] = yearly_data['Fee'] - yearly_data['planned_fee']
                yearly_data['Fee variance percentage'] = (yearly_data['Fee variance'] / yearly_data['planned_fee'] * 100) \
                    .where(yearly_data['planned_fee'] > 0, 0)

    # Rename the 'Month' column to something more descriptive
    yearly_data = yearly_data.rename(columns={'Month': 'Months'})
    
    # Convert Year to string (if it's not a string already)
    if 'Year' in yearly_data.columns and not pd.api.types.is_string_dtype(yearly_data['Year']):
        yearly_data['Year'] = yearly_data['Year'].astype(str)
    
    # Drop any columns that are all NaN
    yearly_data = yearly_data.dropna(axis=1, how='all')
    
    # Ensure index is dropped
    yearly_data = yearly_data.reset_index(drop=True)
    
    # Standardize column order before returning
    return standardize_column_order(yearly_data)

def create_monthly_metrics_table(monthly_data, filtered_df, is_forecast_hours_view=False, forecast_df=None, has_planned_data=False):
    """
    Creates a monthly metrics table with all metrics by month.
    
    Args:
        monthly_data: DataFrame with monthly metrics
        filtered_df: Original filtered DataFrame with time records
        is_forecast_hours_view: Whether this is a forecast hours view
        forecast_df: Optional forecast DataFrame if in forecast view
        has_planned_data: Whether planned data is available
        
    Returns:
        DataFrame with monthly metrics
    """
    # Define base columns that should always be included if they exist
    base_cols = ["Year", "Month name", "hours_used", "hours_billable", "Date string"]

    # Define additional metrics we want to display if available
    additional_metrics = [
        "Billability %", 
        "Fee",
        "Total cost",
        "Total profit", 
        "Profit margin %",
        "Billable rate",
        "Effective rate"
    ]
    
    # Calculate unique projects per month and add to monthly_data
    # Only do this calculation once
    if "Unique projects" not in monthly_data.columns:
        # Create monthly grouping with unique project counts
        monthly_projects = filtered_df.groupby([
            pd.Grouper(key='record_date', freq='M')
        ]).agg({
            'project_number': 'nunique'
        }).reset_index()
        
        # Extract year and month for joining
        monthly_projects['Year'] = monthly_projects['record_date'].dt.year
        monthly_projects['Month'] = monthly_projects['record_date'].dt.month
        
        # Create join keys
        monthly_projects['join_key'] = monthly_projects['Year'].astype(str) + "-" + monthly_projects['Month'].astype(str)
        monthly_data['join_key'] = monthly_data['Year'].astype(str) + "-" + monthly_data['Month'].astype(str)
        
        # Merge
        monthly_data = pd.merge(
            monthly_data,
            monthly_projects[['join_key', 'project_number']],
            on='join_key',
            how='left'
        )
        
        # Rename and clean up
        monthly_data = monthly_data.rename(columns={'project_number': 'Unique projects'})
        monthly_data = monthly_data.drop(columns=['join_key'])
    
    # Add Unique projects to additional metrics
    additional_metrics.append("Unique projects")

    # Define planned metrics to include if available
    planned_metrics = [
        "planned_hours",
        "planned_hourly_rate", 
        "planned_fee",
        "Hours variance",
        "Variance percentage",
        "Rate variance",
        "Rate variance percentage",
        "Fee variance",
        "Fee variance percentage"
    ]

    # Start with base columns
    display_cols = base_cols.copy()

    # Add any additional metrics that exist in the DataFrame
    for metric in additional_metrics:
        if metric in monthly_data.columns:
            display_cols.append(metric)

    # Add any planned metrics that exist
    for metric in planned_metrics:
        if metric in monthly_data.columns:
            display_cols.append(metric)

    # Add accumulated forecast to table if we're in forecast view
    if is_forecast_hours_view and has_planned_data and forecast_df is not None:
        # Create copy of the display dataframe including forecast data
        # Make sure to include 'Month' for merging, even if it's not in display_cols
        merge_cols = list(display_cols) + (['Month'] if 'Month' not in display_cols else [])
        forecast_display_df = pd.merge(
            monthly_data[merge_cols],
            forecast_df[['Year', 'Month', 'Month Value', 'Accumulated Forecast', 'Time Period']],
            on=['Year', 'Month'],
            how='left'
        )
        display_df = forecast_display_df
        # Add forecast columns to display list
        visible_cols = [col for col in display_df.columns if col != "Date string" and col != "Month"]
    else:
        # Sort by Year and Month name instead of Month
        display_df = monthly_data[display_cols].copy()
        # Add forecast columns to display list
        visible_cols = [col for col in display_df.columns if col != "Date string"]

    # Sort the DataFrame
    if "Year" in display_df.columns:
        if "Month" in display_df.columns:
            display_df = display_df.sort_values(["Year", "Month"])
        else:
            # If Month column doesn't exist, try sorting by Date string
            if "Date string" in monthly_data.columns:
                display_df = display_df.sort_values("Date string")
            else:
                display_df = display_df.sort_values("Year")
    
    # Standardize column order
    display_df = standardize_column_order(display_df)
    
    # For the visible columns, we need to ensure "Date string" and "Month" are excluded
    visible_cols = [col for col in display_df.columns if col not in ["Date string", "Month"]]
    
    return display_df, visible_cols

def add_unique_projects_count(df, filtered_df, frequency='M'):
    """
    Adds unique projects count to a dataframe.
    
    Args:
        df: DataFrame to add the counts to
        filtered_df: Source DataFrame with project data
        frequency: Time frequency for grouping ('M' for month, 'Y' for year)
        
    Returns:
        DataFrame with unique projects count added
    """
    # Create grouping with unique project counts
    projects_count = filtered_df.groupby([
        pd.Grouper(key='record_date', freq=frequency)
    ]).agg({
        'project_number': 'nunique'
    }).reset_index()
    
    # Extract year and month/year for joining
    projects_count['Year'] = projects_count['record_date'].dt.year
    
    if frequency == 'M':
        projects_count['Month'] = projects_count['record_date'].dt.month
        # Create join keys
        projects_count['join_key'] = projects_count['Year'].astype(str) + "-" + projects_count['Month'].astype(str)
        df['join_key'] = df['Year'].astype(str) + "-" + df['Month'].astype(str)
    else:
        # For yearly, use only Year as join key
        projects_count['join_key'] = projects_count['Year'].astype(str)
        df['join_key'] = df['Year'].astype(str)
    
    # Merge
    join_cols = ['join_key']
    result_df = pd.merge(
        df,
        projects_count[join_cols + ['project_number']],
        on=join_cols,
        how='left'
    )
    
    # Rename and clean up
    result_df = result_df.rename(columns={'project_number': 'Unique projects'})
    result_df = result_df.drop(columns=['join_key'])
    
    return result_df

def calculate_weighted_averages(df, weight_column, value_columns, group_by=None):
    """
    Calculates weighted averages for specified columns.
    
    Args:
        df: DataFrame with the data
        weight_column: Column to use as weights
        value_columns: List of columns to calculate weighted averages for
        group_by: Optional column to group by before calculating
        
    Returns:
        Series or DataFrame with weighted averages
    """
    if group_by is None:
        # Calculate weighted averages across the entire DataFrame
        result = {}
        for col in value_columns:
            if col in df.columns and weight_column in df.columns:
                weights_sum = df[weight_column].sum()
                if weights_sum > 0:
                    result[col] = (df[col] * df[weight_column]).sum() / weights_sum
                else:
                    result[col] = 0
        return pd.Series(result)
    else:
        # Calculate weighted averages by group
        result = {}
        for col in value_columns:
            if col in df.columns and weight_column in df.columns:
                result[col] = df.groupby(group_by).apply(
                    lambda x: (x[col] * x[weight_column]).sum() / x[weight_column].sum() 
                    if x[weight_column].sum() > 0 else 0
                )
        return pd.DataFrame(result)
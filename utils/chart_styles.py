# utils/chart_styles.py
import streamlit as st
import plotly.graph_objects as go
from typing import Dict, Any, List, Optional
import pandas as pd

# Import directly from currency_formatter instead of number_formatter
from utils.currency_formatter import get_currency_code, get_currency_display_name, CURRENCY_SYMBOLS, SYMBOL_POSITIONS

# Distinct colors for treemap categories
CATEGORY_COLORS = {
    "customer": ["#1f77b4", "#aec7e8", "#3366cc", "#0099c6", "#6699cc", "#004488"],
    "project": ["#ff7f0e", "#ff9933", "#ffad5c", "#ffc285", "#ffd6ad", "#ffe9d6"],
    "project_type": ["#2ca02c", "#98df8a", "#00cc66", "#009933", "#006622", "#33cc33"],
    "phase": ["#9467bd", "#c5b0d5", "#8855aa", "#7744aa", "#663399", "#9966cc"],
    "price_model": ["#d62728", "#ff9896", "#e34234", "#c63631", "#a52a2a", "#d16767"],  # Add this line
    "activity": ["#ff9896", "#ff7f0e", "#ff6347", "#e34234", "#dc143c", "#b22222"],
    "person": ["#17becf", "#9edae5", "#00b3b3", "#008080", "#006666", "#66cccc"]
}

# Default chart dimensions
CHART_HEIGHT = 420
CHART_MARGINS = dict(l=20, r=20, t=40, b=20)

# Treemap specific settings
TREEMAP_MARKER = dict(
    cornerradius=5,
    pad=dict(t=5, l=5, r=5, b=5)
)

# Bar chart specific settings
#BAR_MARKER = dict(
#    cornerradius=3
#)

# Default font settings
FONT_FAMILY = "Arial, sans-serif"
TITLE_FONT_SIZE = 18
AXIS_FONT_SIZE = 20
TICK_FONT_SIZE = 24

def get_currency_formatting():
    """
    Get the current currency symbol and position based on session state.
    
    Returns:
        tuple: (currency_symbol, symbol_position, currency_code) 
               e.g., ('$', 'before', 'usd') or ('kr', 'after', 'nok')
    """
    currency_code = get_currency_code()
    if currency_code is None:
        # Default fallback
        return ('', 'after', None)
    
    symbol = CURRENCY_SYMBOLS.get(currency_code, '')
    position = SYMBOL_POSITIONS.get(currency_code, 'after')
    
    return (symbol, position, currency_code)

def format_currency_value(value, with_symbol=True):
    """
    Format a currency value with the appropriate symbol and position.
    
    Args:
        value: Value to format
        with_symbol: Whether to include the currency symbol
        
    Returns:
        Formatted string
    """
    symbol, position, _ = get_currency_formatting()
    
    formatted = f"{value:,.0f}"
    
    if not with_symbol or not symbol:
        return formatted
        
    if position == 'before':
        return f"{symbol}{formatted}"
    else:
        return f"{formatted} {symbol}"

def create_treemap_hovertemplate(chart_type):
    """
    Create a standardized hover template for treemaps using consistent indices
    
    Args:
        chart_type: Type of chart (customer, project, etc.)
        
    Returns:
        Hover template string
    """
    symbol, position, _ = get_currency_formatting()
    
    hover_template = "<b>%{label}</b><br><br>"
    hover_template += "Hours worked: %{customdata[0]:,.1f} hours<br>"
    hover_template += "Billability: %{customdata[2]:,.1f}%<br>"
    
    # Add currency-formatted fields with appropriate symbol position
    if position == 'before':
        hover_template += f"Effective rate: {symbol}%{{customdata[5]:,.0f}}/hr<br>"
        hover_template += f"Fee: {symbol}%{{customdata[6]:,.0f}}<br>"
        hover_template += f"Total cost: {symbol}%{{customdata[16]:,.0f}}<br>"
        hover_template += f"Total profit: {symbol}%{{customdata[17]:,.0f}}<br>"
    else:
        hover_template += f"Effective rate: %{{customdata[5]:,.0f}} {symbol}/hr<br>"
        hover_template += f"Fee: %{{customdata[6]:,.0f}} {symbol}<br>"
        hover_template += f"Total cost: %{{customdata[16]:,.0f}} {symbol}<br>"
        hover_template += f"Total profit: %{{customdata[17]:,.0f}} {symbol}<br>"
    
    hover_template += "Profit margin: %{customdata[18]:,.1f}%<br>"
    hover_template += "<extra></extra>"  # Hide secondary tooltip
    
    return hover_template

def create_barchart_hovertemplate(chart_type):
    """
    Create a standardized hover template for bar charts using consistent indices
    
    Args:
        chart_type: Type of chart (customer, project, etc.)
        
    Returns:
        Hover template string
    """
    symbol, position, _ = get_currency_formatting()
    
    # For project or customer type charts
    hover_template = "<b>%{x}</b><br><br>"
    hover_template += "Hours worked: %{customdata[0]:,.1f} hours<br>"
    hover_template += "Billability: %{customdata[2]:,.1f}%<br>"
    
    # Add currency-formatted fields with appropriate symbol position
    if position == 'before':
        hover_template += f"Effective rate: {symbol}%{{customdata[5]:,.0f}}/hr<br>"
        hover_template += f"Fee: {symbol}%{{customdata[6]:,.0f}}<br>"
        hover_template += f"Total cost: {symbol}%{{customdata[16]:,.0f}}<br>"
        hover_template += f"Total profit: {symbol}%{{customdata[17]:,.0f}}<br>"
    else:
        hover_template += f"Effective rate: %{{customdata[5]:,.0f}} {symbol}/hr<br>"
        hover_template += f"Fee: %{{customdata[6]:,.0f}} {symbol}<br>"
        hover_template += f"Total cost: %{{customdata[16]:,.0f}} {symbol}<br>"
        hover_template += f"Total profit: %{{customdata[17]:,.0f}} {symbol}<br>"
    
    hover_template += "Profit margin: %{customdata[18]:,.1f}%<br>"
    
    # Add planned metrics for monthly charts
    if chart_type == "project_monthly":
        hover_template += "Planned hours: %{customdata[7]:,.1f} hours<br>"
        if position == 'before':
            hover_template += f"Planned rate: {symbol}%{{customdata[8]:,.0f}}/hr<br>"
            hover_template += f"planned_fee: {symbol}%{{customdata[9]:,.0f}}<br>"
        else:
            hover_template += f"Planned rate: %{{customdata[8]:,.0f}} {symbol}/hr<br>"
            hover_template += f"planned_fee: %{{customdata[9]:,.0f}} {symbol}<br>"
    
    hover_template += "<extra></extra>"  # Hide secondary tooltip
    
    return hover_template

def create_comparison_hovertemplate(comparison_type):
    """
    Create a simplified hover template for comparison bar charts showing only core metrics
    
    Args:
        comparison_type: Type of comparison ('hours', 'rate', 'fee', 'cost', 'profit')
        
    Returns:
        Hover template string with only essential comparison information
    """
    symbol, position, _ = get_currency_formatting()
    
    # Start with item name only
    hover_template = "<b>%{x}</b><br><br>"
    
    # Simplified templates showing only core comparison metrics
    if comparison_type == 'hours':
        # Hours comparison: Hours worked / Hours planned / Difference
        hover_template += "Hours worked: %{customdata[0]:,.1f} hours<br>"
        hover_template += "Hours planned: %{customdata[7]:,.1f} hours<br>"
        hover_template += "Difference: %{customdata[10]:,.1f} hours<br>"
        
    elif comparison_type == 'rate':
        # Rate comparison: Hourly rate / Planned rate / Difference
        if position == 'before':
            hover_template += f"Hourly rate: {symbol}%{{customdata[5]:,.0f}}/hr<br>"
            hover_template += f"Planned rate: {symbol}%{{customdata[8]:,.0f}}/hr<br>"
            hover_template += f"Difference: {symbol}%{{customdata[12]:,.0f}}/hr<br>"
        else:
            hover_template += f"Hourly rate: %{{customdata[5]:,.0f}} {symbol}/hr<br>"
            hover_template += f"Planned rate: %{{customdata[8]:,.0f}} {symbol}/hr<br>"
            hover_template += f"Difference: %{{customdata[12]:,.0f}} {symbol}/hr<br>"
        
    elif comparison_type == 'fee':
        # Fee comparison: Fee / Planned fee / Difference
        if position == 'before':
            hover_template += f"Fee: {symbol}%{{customdata[6]:,.0f}}<br>"
            hover_template += f"Planned fee: {symbol}%{{customdata[9]:,.0f}}<br>"
            hover_template += f"Difference: {symbol}%{{customdata[14]:,.0f}}<br>"
        else:
            hover_template += f"Fee: %{{customdata[6]:,.0f}} {symbol}<br>"
            hover_template += f"Planned fee: %{{customdata[9]:,.0f}} {symbol}<br>"
            hover_template += f"Difference: %{{customdata[14]:,.0f}} {symbol}<br>"
        
    elif comparison_type in ['cost', 'profit']:
        # Cost/Profit comparison: Value / Planned value / Difference  
        if position == 'before':
            hover_template += f"Total cost: {symbol}%{{customdata[16]:,.0f}}<br>"
            hover_template += f"Total profit: {symbol}%{{customdata[17]:,.0f}}<br>"
        else:
            hover_template += f"Total cost: %{{customdata[16]:,.0f}} {symbol}<br>"
            hover_template += f"Total profit: %{{customdata[17]:,.0f}} {symbol}<br>"
        
    else:
        # Generic fallback - minimal info
        hover_template += "Value: %{y:,.1f}<br>"
    
    hover_template += "<extra></extra>"  # Hide secondary tooltip
    
    return hover_template

def create_column_config(df):
    """
    Create a standardized column configuration for Streamlit dataframes
    
    Args:
        df: DataFrame to create configuration for
        
    Returns:
        Dictionary with column configurations
    """
    symbol, position, _ = get_currency_formatting()
    column_config = {}
    
    # Monthly view column handling
    if "Month name" in df.columns:
        column_config["Month name"] = st.column_config.TextColumn(
            "Month",
            width="medium"
        )
    
    if "Date string" in df.columns:
        column_config["Date string"] = st.column_config.Column(
            "Date string",
            disabled=True,
            width=0,  # Set width to 0
            help="Hidden sorting column"
        )
    
    # Variance metrics renaming
    if "Hours variance" in df.columns:
        column_config["Hours variance"] = st.column_config.NumberColumn(
            "Worked vs Planned",
            format="%.0f"  # Simple format with no thousand separator
        )
    
    if "Variance percentage" in df.columns:
        column_config["Variance percentage"] = st.column_config.NumberColumn(
            "Worked vs Planned %",
            format="%.1f%%"  # Keep this format for percentage with 1 decimal
        )
        
    if "Rate variance" in df.columns:
        # For currency, use simple format with symbol
        if position == 'before':
            format_str = f"{symbol}%.0f"
        else:
            format_str = f"%.0f {symbol}"
                
        column_config["Rate variance"] = st.column_config.NumberColumn(
            "Effective vs Planned rate",
            format=format_str,
            help=f"Currency in {get_currency_display_name()}"
        )
    
    if "Rate variance percentage" in df.columns:
        column_config["Rate variance percentage"] = st.column_config.NumberColumn(
            "Effective vs Planned rate %",
            format="%.1f%%"  # Keep this format for percentage with 1 decimal
        )
        
    if "Fee variance" in df.columns:
        # For currency, use simple format with symbol
        if position == 'before':
            format_str = f"{symbol}%.0f"
        else:
            format_str = f"%.0f {symbol}"
            
        column_config["Fee variance"] = st.column_config.NumberColumn(
            "Fee vs planned_fee",
            format=format_str,
            help=f"Currency in {get_currency_display_name()}"
        )
    
    if "Fee variance percentage" in df.columns:
        column_config["Fee variance percentage"] = st.column_config.NumberColumn(
            "Fee vs planned_fee %",
            format="%.1f%%"  # Keep this format for percentage with 1 decimal
        )
    
    if "planned_fee" in df.columns:
        # For currency, use simple format with symbol
        if position == 'before':
            format_str = f"{symbol}%.0f"
        else:
            format_str = f"%.0f {symbol}"
            
        column_config["planned_fee"] = st.column_config.NumberColumn(
            "planned_fee",
            format=format_str,
            help=f"Currency in {get_currency_display_name()}"
        )
    
    # Cost and Profit column configurations
    if "Total cost" in df.columns:
        if position == 'before':
            format_str = f"{symbol}%.0f"
        else:
            format_str = f"%.0f {symbol}"
            
        column_config["Total cost"] = st.column_config.NumberColumn(
            "Total cost",
            format=format_str,
            help=f"Currency in {get_currency_display_name()}"
        )
    
    if "Total profit" in df.columns:
        if position == 'before':
            format_str = f"{symbol}%.0f"
        else:
            format_str = f"%.0f {symbol}"
            
        column_config["Total profit"] = st.column_config.NumberColumn(
            "Total profit",
            format=format_str,
            help=f"Currency in {get_currency_display_name()}. Can be negative."
        )
    
    if "Profit margin %" in df.columns:
        column_config["Profit margin %"] = st.column_config.NumberColumn(
            "Profit margin %",
            format="%.1f%%",
            help="Profit as percentage of fee. Can be negative."
        )
    
    # Add comprehensive display name mappings for all field names
    display_name_mappings = {
        # Core time fields
        "hours_used": "Hours worked",
        "hours_billable": "Billable hours",
        
        # Planned data fields  
        "planned_hours": "Planned hours", 
        "planned_hourly_rate": "Planned rate",
        "planned_fee": "Planned fee",
        
        # Entity identifier fields
        "customer_name": "Customer name",
        "customer_number": "Customer number", 
        "project_name": "Project name",
        "project_number": "Project number",
        "project_tag": "Project tag",
        "person_name": "Person name",
        "person_type": "Person type",
        "activity_tag": "Activity",
        "phase_tag": "Phase",
        
        # Record fields
        "record_date": "Date",
        "billable_rate_record": "Hourly rate",
        "fee_record": "Fee per time record",
        "cost_per_hour": "Cost per hour",
        "cost_per_record": "Cost per time record",
        "profit_per_record": "Profit per time record",
        "profit_per_hour": "Profit per hour",
        
        # Other common fields that might appear
        "data_source": "Data source",
        "planned_billable": "Planned billable"
    }
    
    for col in df.columns:
        # Skip already configured columns
        if col in column_config:
            continue
            
        # Skip text columns that don't need display name changes
        if col in ["Month name"]:
            continue
            
        # Handle text identifier columns with display names
        if col in ["customer_name", "customer_number", "project_name", "project_number", 
                  "project_tag", "phase_tag", "activity_tag", "person_name", "person_type"]:
            display_name = display_name_mappings.get(col, col)
            column_config[col] = st.column_config.TextColumn(display_name)
            continue
            
        # Get display name for column
        display_name = display_name_mappings.get(col, col)
        
        # Make Year a string with no thousand separator
        if col == "Year":
            column_config[col] = st.column_config.TextColumn(
                display_name
            )
            
        # Percentage formatting
        elif "Billability" in col or "margin" in col.lower():
            column_config[col] = st.column_config.NumberColumn(
                display_name,
                format="%.1f%%"  # Keep percentage with 1 decimal
            )
            
        # Currency formatting (rates, fee, cost, profit)
        elif ("rate" in col.lower() or col in ["Fee", "Rate variance", "Fee variance", 
              "planned_fee", "Total cost", "Total profit"]):
            # For currency, use simple format with symbol
            if position == 'before':
                base_format = f"{symbol}%.0f"
            else:
                base_format = f"%.0f {symbol}"
                
            # Special handling for hourly rates
            if "rate" in col.lower():
                if position == 'before':
                    format_str = f"{symbol}%.0f/hr"
                else:
                    format_str = f"%.0f {symbol}/hr"
            else:
                format_str = base_format
            
            column_config[col] = st.column_config.NumberColumn(
                display_name,
                format=format_str,
                help=f"Currency in {get_currency_display_name()}"
            )
            
        # Regular number formatting
        elif pd.api.types.is_numeric_dtype(df[col]):
            column_config[col] = st.column_config.NumberColumn(
                display_name,
                format="%.0f"  # Simple format with no thousand separator for numeric values
            )
    
    return column_config

def is_comparison_chart(fig):
    """
    Determine if a figure is a comparison chart.
    
    Args:
        fig: Plotly figure object
        
    Returns:
        bool: True if it's a comparison chart, False otherwise
    """
    # Check if it's a bar chart with multiple traces (grouped bars)
    if fig.data and len(fig.data) > 1 and all(trace.type == 'bar' for trace in fig.data):
        # Check if the traces have names that match our comparison metrics
        trace_names = [trace.name for trace in fig.data if hasattr(trace, 'name')]
        comparison_pairs = [
            ('hours_used', 'planned_hours'),
            ('Effective rate', 'planned_hourly_rate'),
            ('Fee', 'planned_fee'),
            ('Total cost', 'Planned cost'),
            ('Total profit', 'Planned profit')
        ]
        
        for pair in comparison_pairs:
            if all(name in trace_names for name in pair):
                return True, get_comparison_type(pair)
    
    return False, None

def get_comparison_type(comparison_pair):
    """
    Determine the type of comparison based on the metric pair.
    
    Args:
        comparison_pair: Tuple of metric names
        
    Returns:
        str: Comparison type ('hours', 'rate', 'fee', 'cost', 'profit')
    """
    # Check both metrics in the comparison pair for more accurate detection
    pair_str = ' '.join(comparison_pair).lower()
    
    # Match specific comparison patterns
    if 'worked vs planned: hours' in pair_str or 'hours' in pair_str:
        return 'hours'
    elif 'worked vs planned: hourly rate' in pair_str or 'worked vs planned: fees' in pair_str:
        if 'rate' in pair_str:
            return 'rate'
        elif 'fee' in pair_str:
            return 'fee'
    elif 'worked vs planned: fees' in pair_str or 'fee' in pair_str:
        return 'fee'
    elif 'cost' in pair_str:
        return 'cost'
    elif 'profit' in pair_str:
        return 'profit'
    
    # Fallback to original logic for backwards compatibility
    if 'Hours' in comparison_pair[0]:
        return 'hours'
    elif 'rate' in comparison_pair[0].lower():
        return 'rate'
    elif 'Fee' in comparison_pair[0]:
        return 'fee'
    elif 'cost' in comparison_pair[0].lower():
        return 'cost'
    elif 'profit' in comparison_pair[0].lower():
        return 'profit'
    else:
        return 'generic'

def apply_chart_style(fig, chart_type="default"):
    """
    Apply consistent styling to Plotly figures
    
    Args:
        fig: Plotly figure object
        chart_type: Type of chart for specific styling (default, customer, project, etc.)
    
    Returns:
        Styled Plotly figure
    """
    # Check the chart type of the figure
    if fig.data and hasattr(fig.data[0], 'type'):
        chart_vis_type = fig.data[0].type
    else:
        chart_vis_type = "unknown"
    
    # Apply specific styling based on the chart visualization type
    if chart_vis_type == "treemap":
        fig.update_traces(
            textposition='middle center',
            marker=TREEMAP_MARKER
        )
        # Set translucent background for treemap
        fig.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',  # Transparent paper background
            plot_bgcolor='rgba(0,0,0,0)'    # Transparent plot background
        )
    elif chart_vis_type == "bar":
        fig.update_traces(
            #marker=BAR_MARKER
        )
    
    # Apply consistent layout
    fig.update_layout(
        height=CHART_HEIGHT,
        margin=CHART_MARGINS,
        font=dict(
            family=FONT_FAMILY,
            size=TICK_FONT_SIZE
        ),
        title=dict(
            font=dict(
                family=FONT_FAMILY,
                size=TITLE_FONT_SIZE
            )
        ),
        hoverlabel=dict(
            font_size=20,
            font_family=FONT_FAMILY
        ),
        # No colorbar needed
    )

    # Add currency information to title if relevant
    if chart_type != "default" and hasattr(fig, 'layout') and hasattr(fig.layout, 'title'):
        current_title = fig.layout.title.text
        if current_title and ("Fee" in current_title or "rate" in current_title.lower() or 
                             "cost" in current_title.lower() or "profit" in current_title.lower()):
            currency_info = get_currency_display_name()
            if currency_info:
                # Extract currency code or symbol
                currency_code = get_currency_code()
                if currency_code:
                    currency_symbol = CURRENCY_SYMBOLS.get(currency_code, currency_code.upper())
                    # Don't modify title if it already includes currency info
                    if currency_symbol not in current_title and currency_code.upper() not in current_title.upper():
                        fig.update_layout(title=f"{current_title} ({currency_symbol})")

    return fig

def render_chart(fig, chart_type="default"):
    """
    Apply styling and render a Plotly chart in Streamlit

    Args:
        fig: Plotly figure object
        chart_type: Type of chart for specific styling

    Returns:
        None (renders in Streamlit)
    """
    # Apply styling
    fig = apply_chart_style(fig, chart_type)

    # Check if it's a comparison chart
    is_comparison, comparison_type = is_comparison_chart(fig)

    # Apply custom hovertemplate based on chart type
    if fig.data and hasattr(fig.data[0], 'type'):
        # For comparison charts
        if is_comparison and comparison_type:
            hovertemplate = create_comparison_hovertemplate(comparison_type)
            for trace in fig.data:
                trace.hovertemplate = hovertemplate
        # For treemaps
        elif fig.data[0].type == 'treemap':
            hovertemplate = create_treemap_hovertemplate(chart_type)
            fig.update_traces(hovertemplate=hovertemplate)
        # For regular bar charts
        elif fig.data[0].type == 'bar' and not is_comparison:
            hovertemplate = create_barchart_hovertemplate(chart_type)
            fig.update_traces(hovertemplate=hovertemplate)

    # Add CSS to improve chart display in Streamlit
    st.markdown(
        """
        <style>
        .stPlotlyChart {
            width: 100%;
            margin: 0 auto;
        }
        /* Hide treemap background element - target by gray fill color */
        .treemaplayer .trace.treemap .slice .surface[style*="fill: rgb(68, 68, 68)"] {
            pointer-events: none !important;
            fill: transparent !important;
            stroke: transparent !important;
        }
        /* Hide treemap background for go.Treemap (light gray) */
        .treemaplayer .trace.treemap .slice .surface[style*="fill: rgb(211, 211, 211)"] {
            pointer-events: none !important;
            fill: transparent !important;
            stroke: transparent !important;
        }
        /* Hide "undefined" text in treemap pathbar title */
        text.gtitle[data-unformatted*="undefined"] {
            display: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Render the chart
    st.plotly_chart(fig, use_container_width=True)

def get_category_colors(chart_type):
    """
    Get the appropriate colors for a chart type
    
    Args:
        chart_type: Type of chart
    
    Returns:
        List of colors for the chart
    """
    return CATEGORY_COLORS.get(chart_type, ["#17becf", "#9edae5", "#00b3b3", "#008080", "#006666"])

# Helper functions

def get_metric_options(has_planned_data=False):
    """
    Generate metric options based on available data.
    
    Args:
        has_planned_data: Whether planned data is available
        
    Returns:
        List of metrics options for dropdown
    """
    # Clean dropdown without dividers
    metric_options = [
        "Hours worked",
        "Billable hours", 
        "Billability %",
        "Fee",
        "Total cost",
        "Total profit",
        "Profit margin %",
        "Billable rate",
        "Effective rate"
    ]
    
    # Add comparison metrics if we have planned data
    if has_planned_data:
        metric_options.extend([
            "Worked vs Planned: Hours",
            "Worked vs Planned: Hourly rate",
            "Worked vs Planned: Fees",
            "Hours"  # Forecast option
        ])
        
    return metric_options

def get_visualization_options(is_comparison_view=False, is_forecast_hours_view=False):
    """
    Generate visualization options based on view type.
    
    Args:
        is_comparison_view: Whether this is a comparison view
        is_forecast_hours_view: Whether this is a forecast hours view
        
    Returns:
        List of visualization options
    """
    if is_comparison_view:
        # For comparison views, only show bar chart options (no treemap)
        return ["Monthly: Bar chart", "Project: Bar chart"]
    elif is_forecast_hours_view:
        # For forecast view, only allow monthly bar chart
        return ["Monthly: Bar chart"]
    else:
        # For regular metrics, show all visualization options with Treemap first
        return ["Project: Treemap", "Monthly: Bar chart", "Project: Bar chart"]

def format_variance_columns(df):
    """
    Format variance columns with appropriate styling.
    
    Args:
        df: DataFrame with variance columns
        
    Returns:
        DataFrame with formatted variance columns
    """
    # Format variance percentage columns
    for col in ["Variance percentage", "Rate variance percentage", "Fee variance percentage"]:
        if col in df.columns:
            df[col] = df[col].round(1)
    
    # Round variance columns to integers
    for col in ["Hours variance", "Rate variance", "Fee variance"]:
        if col in df.columns:
            df[col] = df[col].round(0).astype(int)
    
    return df

def format_time_period_columns(df):
    """
    Format time period columns (Year, Month).
    
    Args:
        df: DataFrame with time period columns
        
    Returns:
        DataFrame with formatted time period columns
    """
    # Convert Year to string
    if "Year" in df.columns:
        df["Year"] = df["Year"].astype(str)
    
    # Create Date string for sorting if Month and Year are present
    if "Month" in df.columns and "Year" in df.columns:
        # Create a sortable date string (YYYY-MM)
        df["Date string"] = df["Year"].astype(str) + "-" + df["Month"].astype(str).str.zfill(2)
    
    return df

def standardize_column_order(df):
    """
    Standardizes column order across all metric tables.
    
    Args:
        df: DataFrame to reorder columns for
        
    Returns:
        DataFrame with standardized column order
    """
    # Define master column order for all standard metrics
    standard_columns_order = [
        # Identifiers
        "Year",
        "Month name",
        "Month",
        "Date string",
        "project_name",
        "project_number",
        
        # Core time metrics
        "hours_used",
        "hours_billable",
        "Billability %",
        
        # Financial metrics
        "Fee",
        "Total cost",
        "Total profit",
        "Profit margin %",
        
        # Rate metrics
        "Billable rate",
        "Effective rate",
        
        # Planned metrics
        "planned_hours",
        "planned_hourly_rate",
        "planned_fee",
        
        # Variance metrics
        "Hours variance",
        "Variance percentage",
        "Rate variance",
        "Rate variance percentage",
        "Fee variance",
        "Fee variance percentage",
        
        # Special metrics that should appear at the end
        "Unique projects",
        "Months"
    ]
    
    # Additional columns for forecast view
    forecast_columns = [
        "Month Value",
        "Accumulated Forecast",
        "Time Period"
    ]
    
    # Combine standard and forecast columns
    all_ordered_columns = standard_columns_order + forecast_columns
    
    # Get the columns that exist in both the dataframe and our order list
    existing_ordered_cols = [col for col in all_ordered_columns if col in df.columns]
    
    # Find any columns in the dataframe that aren't in our order list
    remaining_cols = [col for col in df.columns if col not in all_ordered_columns]
    
    # Final column order: standard columns first, then any remaining columns
    final_columns = existing_ordered_cols + remaining_cols
    
    # Reorder the dataframe columns
    return df[final_columns]
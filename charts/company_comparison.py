# charts/company_comparison.py
"""
Company-level period comparison visualization.
Provides KPI comparison across two time periods with summary cards and charts.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, date
from typing import Dict

from utils.comparison_helpers import (
    calculate_period_dates,
    calculate_period_from_comparison_type,
    format_period_label,
    format_period_label_short,
    aggregate_period_metrics,
    calculate_comparison,
    validate_period_data,
    get_metric_config
)
from utils.chart_styles import format_currency_value, get_currency_formatting


def format_metric_value(value: float, unit_type: str) -> str:
    """
    Format a metric value based on its unit type.

    Args:
        value: The numeric value to format
        unit_type: Type of unit ('hours', 'currency', 'currency_per_hour', 'percentage')

    Returns:
        Formatted string
    """
    symbol, position, _ = get_currency_formatting()

    if unit_type == 'hours':
        return f"{value:,.0f} hrs"
    elif unit_type == 'currency':
        return format_currency_value(value, with_symbol=True)
    elif unit_type == 'currency_per_hour':
        if position == 'before':
            return f"{symbol}{value:,.0f}/hr"
        else:
            return f"{value:,.0f} {symbol}/hr"
    elif unit_type == 'percentage':
        # Only profit_margin uses this with decimals; others should be .0f
        # Check if value is profit margin (typically small percentage)
        return f"{value:,.0f}%"
    else:
        return f"{value:,.0f}"


def render_period_card(
    period_label: str,
    period_metrics: Dict[str, float],
    comparison: Dict[str, Dict[str, any]],
    ribbon_color: str,
    period_name: str,
    show_delta: bool = True
) -> None:
    """
    Render a single period card with ribbon header and two-column metric layout.

    Args:
        period_label: Date range label (e.g., "JUL-SEP 2025")
        period_metrics: Dictionary of metric values for this period
        comparison: Comparison dictionary for delta indicators
        ribbon_color: Hex color for ribbon header
        period_name: "Period A" or "Period B"
        show_delta: Whether to show delta indicators
    """
    metric_config = get_metric_config()

    # Build metrics HTML for column 1
    col1_html = []
    metrics_col1 = [
        ('hours_used', period_metrics.get('hours_used', 0.0), 'hours'),
        ('fee', period_metrics.get('fee', 0.0), 'currency'),
        ('profit', period_metrics.get('profit', 0.0), 'currency')
    ]

    for metric_key, value, unit in metrics_col1:
        formatted_value = format_metric_value(value, unit)
        delta_html = ""

        if show_delta and metric_key in comparison:
            comp_data = comparison[metric_key]
            pct_change = comp_data['pct_change']
            direction = comp_data['direction']

            if direction != 'neutral':
                config = metric_config[metric_key]
                if direction == 'up':
                    color = '#2ca02c' if config['positive_is_good'] else '#d62728'
                    arrow = '↑'
                else:
                    color = '#d62728' if config['positive_is_good'] else '#2ca02c'
                    arrow = '↓'
                delta_html = f'<div style="font-size: 11px; color: {color}; margin-top: 2px;">{pct_change:+.1f}% {arrow}</div>'

        metric_html = f'<div style="margin-bottom: 20px;"><div style="font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 500;">{metric_config[metric_key]["label"]}</div><div style="font-size: 24px; font-weight: 700; color: #000;">{formatted_value}</div>{delta_html}</div>'
        col1_html.append(metric_html)

    # Build metrics HTML for column 2
    col2_html = []
    metrics_col2 = [
        ('billability', period_metrics.get('billability', 0.0), 'percentage'),
        ('effective_rate', period_metrics.get('effective_rate', 0.0), 'currency_per_hour'),
        ('profit_margin', period_metrics.get('profit_margin', 0.0), 'percentage')
    ]

    for metric_key, value, unit in metrics_col2:
        formatted_value = format_metric_value(value, unit)
        delta_html = ""

        if show_delta and metric_key in comparison:
            comp_data = comparison[metric_key]
            pct_change = comp_data['pct_change']
            direction = comp_data['direction']

            if direction != 'neutral':
                config = metric_config[metric_key]
                if direction == 'up':
                    color = '#2ca02c' if config['positive_is_good'] else '#d62728'
                    arrow = '↑'
                else:
                    color = '#d62728' if config['positive_is_good'] else '#2ca02c'
                    arrow = '↓'
                delta_html = f'<div style="font-size: 11px; color: {color}; margin-top: 2px;">{pct_change:+.1f}% {arrow}</div>'

        metric_html = f'<div style="margin-bottom: 20px;"><div style="font-size: 12px; color: #666; margin-bottom: 4px; font-weight: 500;">{metric_config[metric_key]["label"]}</div><div style="font-size: 24px; font-weight: 700; color: #000;">{formatted_value}</div>{delta_html}</div>'
        col2_html.append(metric_html)

    # Combine everything into final HTML
    card_html = f'''<div style="border: 2px solid {ribbon_color}; border-radius: 8px; padding: 0; background-color: white; box-shadow: 0 2px 4px rgba(0,0,0,0.1);"><div style="background-color: {ribbon_color}; color: white; padding: 12px; text-align: center; font-weight: 600; font-size: 18px; border-radius: 6px 6px 0 0;">{period_label}</div><div style="padding: 24px;"><table style="width: 100%; border-collapse: collapse;"><tr><td style="width: 50%; padding-right: 12px; vertical-align: top;">{''.join(col1_html)}</td><td style="width: 50%; padding-left: 12px; vertical-align: top;">{''.join(col2_html)}</td></tr></table></div></div>'''

    st.markdown(card_html, unsafe_allow_html=True)


def render_summary_cards(
    comparison: Dict[str, Dict[str, any]],
    period_a_label: str,
    period_b_label: str,
    period_a_start: datetime,
    period_a_end: datetime,
    period_b_start: datetime,
    period_b_end: datetime,
    period_a_metrics: Dict[str, float],
    period_b_metrics: Dict[str, float]
) -> None:
    """
    Render two side-by-side period cards for comparison.

    Args:
        comparison: Full comparison dictionary from calculate_comparison()
        period_a_label: Display label for Period A (long form)
        period_b_label: Display label for Period B (long form)
        period_a_start: Period A start date
        period_a_end: Period A end date
        period_b_start: Period B start date
        period_b_end: Period B end date
        period_a_metrics: Raw metrics for Period A
        period_b_metrics: Raw metrics for Period B
    """
    # Format short labels for card headers
    period_a_short = format_period_label_short(period_a_start, period_a_end)
    period_b_short = format_period_label_short(period_b_start, period_b_end)

    # Two equal columns for side-by-side cards
    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        render_period_card(
            period_label=period_a_short,
            period_metrics=period_a_metrics,
            comparison=comparison,
            ribbon_color="#1f77b4",  # Blue
            period_name="Period A"
        )

    with col2:
        render_period_card(
            period_label=period_b_short,
            period_metrics=period_b_metrics,
            comparison=comparison,
            ribbon_color="#2ca02c",  # Green
            period_name="Period B"
        )


def render_comparison_chart(
    selected_metric: str,
    comparison: Dict[str, Dict[str, any]],
    period_a_label: str,
    period_b_label: str
) -> None:
    """
    Render a grouped bar chart comparing Period A vs Period B for the selected metric.
    Includes percentage change labels and delta indicators to highlight even small differences.

    Args:
        selected_metric: Which metric to display
        comparison: Full comparison dictionary
        period_a_label: Display label for Period A
        period_b_label: Display label for Period B
    """
    metric_config = get_metric_config()
    config = metric_config[selected_metric]
    symbol, position, _ = get_currency_formatting()

    # Get values
    metric_data = comparison[selected_metric]
    value_a = metric_data['a']
    value_b = metric_data['b']
    pct_change = metric_data['pct_change']
    direction = metric_data['direction']

    # Determine text template (no decimals except for profit_margin)
    if selected_metric == 'profit_margin':
        text_template = '%{text:,.1f}'
    else:
        text_template = '%{text:,.0f}'

    # Determine change color
    if direction == 'up':
        change_color = '#2ca02c' if config['positive_is_good'] else '#d62728'  # Green if good, red if bad
    elif direction == 'down':
        change_color = '#d62728' if config['positive_is_good'] else '#2ca02c'  # Red if bad, green if good
    else:
        change_color = '#808080'  # Gray for neutral

    # Create bar chart
    fig = go.Figure()

    # Period A bar
    fig.add_trace(go.Bar(
        name='Period A',
        x=[period_a_label],
        y=[value_a],
        marker_color='#1f77b4',  # Dark blue
        text=[value_a],
        textposition='outside',
        texttemplate=text_template,
        hovertemplate=f'<b>{period_a_label}</b><br>Value: %{{y:,.0f}}<extra></extra>' if selected_metric != 'profit_margin' else f'<b>{period_a_label}</b><br>Value: %{{y:,.1f}}%<extra></extra>',
        showlegend=False
    ))

    # Period B bar
    fig.add_trace(go.Bar(
        name='Period B',
        x=[period_b_label],
        y=[value_b],
        marker_color='#aec7e8',  # Light blue
        text=[value_b],
        textposition='outside',
        texttemplate=text_template,
        hovertemplate=f'<b>{period_b_label}</b><br>Value: %{{y:,.0f}}<extra></extra>' if selected_metric != 'profit_margin' else f'<b>{period_b_label}</b><br>Value: %{{y:,.1f}}%<extra></extra>',
        showlegend=False
    ))

    # Add percentage change annotation above the chart (very visible)
    max_value = max(value_a, value_b)
    annotation_y = max_value * 1.15

    arrow_symbol = '↑' if direction == 'up' else '↓' if direction == 'down' else '→'
    fig.add_annotation(
        x=0.5,
        y=annotation_y,
        text=f"<b>{pct_change:+.1f}%</b> {arrow_symbol}",
        showarrow=False,
        font=dict(size=20, color=change_color),
        xref='paper',
        yref='y'
    )

    # Add delta value annotation (absolute difference)
    diff_value = metric_data['diff']
    delta_y = max_value * 1.05
    fig.add_annotation(
        x=0.5,
        y=delta_y,
        text=f"Δ {abs(diff_value):,.0f}" if selected_metric != 'profit_margin' else f"Δ {abs(diff_value):,.1f}",
        showarrow=False,
        font=dict(size=12, color=change_color),
        xref='paper',
        yref='y'
    )

    # Format y-axis title based on unit
    if config['unit'] == 'currency':
        y_title = f"{config['label']} ({symbol})"
    elif config['unit'] == 'currency_per_hour':
        y_title = f"{config['label']} ({symbol}/hr)"
    elif config['unit'] == 'percentage':
        y_title = f"{config['label']} (%)"
    elif config['unit'] == 'hours':
        y_title = f"{config['label']} (hrs)"
    else:
        y_title = config['label']

    # Update layout
    fig.update_layout(
        title="",
        xaxis_title="",
        yaxis_title=y_title,
        barmode='group',
        showlegend=False,
        height=550,
        margin=dict(l=20, r=20, t=100, b=20),  # Increased top margin for annotations
        font=dict(size=14),
        hovermode='x unified'
    )

    # Render chart
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_tab(filtered_df: pd.DataFrame, filter_settings: dict = None) -> None:
    """
    Main render function for the Period Comparison tab.

    Args:
        filtered_df: Filtered time records DataFrame from sidebar
        filter_settings: Dictionary of filter settings from sidebar
    """
    # Initialize session state keys if not present
    if 'comparison_type' not in st.session_state:
        st.session_state.comparison_type = 'Last 6 months vs previous 6 months'
    if 'comparison_selected_metric' not in st.session_state:
        st.session_state.comparison_selected_metric = 'effective_rate'

    # Get max and min dates from dataset
    max_date = filtered_df['record_date'].max().date()

    # Comparison type selector dropdown
    comparison_options = [
        'Last month vs previous month',
        'Last quarter vs previous quarter',
        'Last 6 months vs previous 6 months',
        'Last 12 months vs previous 12 months',
        'Year to date vs previous year to date',
        'Selected end year vs start year'
    ]

    # Align dropdowns horizontally
    col1, col2 = st.columns([1, 1])

    with col1:
        comparison_type = st.selectbox(
            label="",
            options=comparison_options,
            index=comparison_options.index(st.session_state.comparison_type),
            key='comparison_type_selector',
            label_visibility="collapsed"
        )
        st.session_state.comparison_type = comparison_type

    # Metric selector for chart
    metric_config = get_metric_config()
    metric_options = {name: config['label'] for name, config in metric_config.items()}

    with col2:
        selected_metric = st.selectbox(
            label="",
            options=list(metric_options.keys()),
            format_func=lambda x: metric_options[x],
            index=list(metric_options.keys()).index(st.session_state.comparison_selected_metric),
            key='comparison_metric_selector',
            label_visibility="collapsed"
        )
        st.session_state.comparison_selected_metric = selected_metric

    # Get start and end year from filter settings (if "Years" period type is selected)
    start_year = None
    end_year = None

    if filter_settings and 'date_filter_config' in filter_settings:
        filter_config = filter_settings['date_filter_config']
        if filter_config.get('period_type') == 'Years':
            start_year = filter_config.get('year_start', None)
            end_year = filter_config.get('year_end', None)

    # Calculate period dates using the helper function
    period_a_start, period_a_end, period_b_start, period_b_end = calculate_period_from_comparison_type(
        comparison_type,
        max_date,
        start_year,
        end_year
    )

    # Format period labels (for warnings only)
    period_a_label = format_period_label(period_a_start, period_a_end)
    period_b_label = format_period_label(period_b_start, period_b_end)

    # Validate Period B data availability
    is_valid, warning_msg = validate_period_data(filtered_df, period_b_start, period_b_end)

    if not is_valid:
        st.warning(warning_msg)
        st.info("💡 Try adjusting your comparison type or filters.")
        return

    # Aggregate metrics for both periods
    period_a_metrics = aggregate_period_metrics(filtered_df, period_a_start, period_a_end)
    period_b_metrics = aggregate_period_metrics(filtered_df, period_b_start, period_b_end)

    # Check if Period A has data
    if not period_a_metrics['has_data']:
        st.warning(f"⚠️ No data exists in Period A ({period_a_label}).")
        return

    # Calculate comparison
    comparison = calculate_comparison(period_a_metrics, period_b_metrics)

    # Render chart
    render_comparison_chart(
        selected_metric,
        comparison,
        period_a_label,
        period_b_label
    )

    # Optional: Show detailed numbers table
    with st.expander("📊 View Detailed Numbers"):
        # Create comparison table
        comparison_data = []
        for metric_name, metric_data in comparison.items():
            config = metric_config[metric_name]
            comparison_data.append({
                'Metric': config['label'],
                'Period A': metric_data['a'],
                'Period B': metric_data['b'],
                'Difference': metric_data['diff'],
                'Change %': metric_data['pct_change']
            })

        comparison_df = pd.DataFrame(comparison_data)
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )

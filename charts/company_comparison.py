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
    format_period_label,
    aggregate_period_metrics,
    calculate_comparison,
    validate_period_data,
    get_metric_config
)
from utils.chart_styles import format_currency_value, get_currency_formatting


def render_summary_card(
    metric_name: str,
    comparison_data: Dict[str, any],
    metric_config: Dict[str, any]
) -> None:
    """
    Render a single summary card with Period A, Period B, difference, and % change.

    Args:
        metric_name: Name of the metric (e.g., 'effective_rate')
        comparison_data: Comparison dict for this metric
        metric_config: Configuration dict for formatting
    """
    symbol, position, _ = get_currency_formatting()

    # Extract values
    value_a = comparison_data['a']
    value_b = comparison_data['b']
    diff = comparison_data['diff']
    pct_change = comparison_data['pct_change']
    direction = comparison_data['direction']

    # Format values based on unit type
    unit_type = metric_config['unit']
    positive_is_good = metric_config['positive_is_good']

    if unit_type == 'currency':
        # Format as currency
        val_a_str = format_currency_value(value_a, with_symbol=True)
        val_b_str = format_currency_value(value_b, with_symbol=True)
        diff_str = format_currency_value(abs(diff), with_symbol=True)
    elif unit_type == 'currency_per_hour':
        # Format as currency per hour
        if position == 'before':
            val_a_str = f"{symbol}{value_a:,.0f}/hr"
            val_b_str = f"{symbol}{value_b:,.0f}/hr"
            diff_str = f"{symbol}{abs(diff):,.0f}/hr"
        else:
            val_a_str = f"{value_a:,.0f} {symbol}/hr"
            val_b_str = f"{value_b:,.0f} {symbol}/hr"
            diff_str = f"{abs(diff):,.0f} {symbol}/hr"
    elif unit_type == 'percentage':
        # Format as percentage
        val_a_str = f"{value_a:,.1f}%"
        val_b_str = f"{value_b:,.1f}%"
        # For percentage metrics, use percentage points (pp) for difference
        diff_str = f"{abs(diff):,.1f} pp"
    else:
        # Fallback
        val_a_str = f"{value_a:,.1f}"
        val_b_str = f"{value_b:,.1f}"
        diff_str = f"{abs(diff):,.1f}"

    # Determine color for diff/pct_change based on direction and whether positive is good
    if direction == 'neutral':
        color = 'gray'
        arrow = ''
    elif direction == 'up':
        color = 'green' if positive_is_good else 'red'
        arrow = '↑'
    else:  # down
        color = 'red' if positive_is_good else 'green'
        arrow = '↓'

    # Add sign to diff
    diff_sign = '+' if diff >= 0 else '-'

    # Render card with HTML
    card_html = f"""
    <div style="
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 16px;
        background-color: #fafafa;
        height: 100%;
    ">
        <h4 style="margin: 0 0 12px 0; font-size: 16px; color: #333;">
            {metric_config['label']}
        </h4>
        <div style="margin-bottom: 8px;">
            <div style="font-size: 11px; color: #666; margin-bottom: 2px;">Period A</div>
            <div style="font-size: 20px; font-weight: 600; color: #000;">{val_a_str}</div>
        </div>
        <div style="margin-bottom: 8px;">
            <div style="font-size: 11px; color: #666; margin-bottom: 2px;">Period B</div>
            <div style="font-size: 16px; color: #555;">{val_b_str}</div>
        </div>
        <div style="margin-bottom: 4px;">
            <span style="font-size: 13px; color: #666;">Δ: </span>
            <span style="font-size: 13px; color: {color}; font-weight: 500;">
                {diff_sign}{diff_str}
            </span>
        </div>
        <div>
            <span style="font-size: 13px; color: #666;">Change: </span>
            <span style="font-size: 14px; color: {color}; font-weight: 600;">
                {pct_change:+.1f}% {arrow}
            </span>
        </div>
    </div>
    """

    st.markdown(card_html, unsafe_allow_html=True)


def render_summary_cards(comparison: Dict[str, Dict[str, any]]) -> None:
    """
    Render all summary cards in a row.

    Args:
        comparison: Full comparison dictionary from calculate_comparison()
    """
    metric_config = get_metric_config()

    # Create 5 columns for the 5 metrics
    cols = st.columns(5)

    metrics_order = ['effective_rate', 'billability', 'fee', 'profit', 'profit_margin']

    for idx, metric_name in enumerate(metrics_order):
        with cols[idx]:
            render_summary_card(
                metric_name,
                comparison[metric_name],
                metric_config[metric_name]
            )


def render_comparison_chart(
    selected_metric: str,
    comparison: Dict[str, Dict[str, any]],
    period_a_label: str,
    period_b_label: str
) -> None:
    """
    Render a grouped bar chart comparing Period A vs Period B for the selected metric.

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

    # Create bar chart
    fig = go.Figure()

    # Period A bar
    fig.add_trace(go.Bar(
        name='Period A',
        x=['Period A'],
        y=[value_a],
        marker_color='#1f77b4',  # Dark blue
        text=[value_a],
        textposition='outside',
        texttemplate='%{text:,.1f}',
        hovertemplate=f'<b>Period A</b><br>{period_a_label}<br>Value: %{{y:,.1f}}<extra></extra>'
    ))

    # Period B bar
    fig.add_trace(go.Bar(
        name='Period B',
        x=['Period B'],
        y=[value_b],
        marker_color='#aec7e8',  # Light blue
        text=[value_b],
        textposition='outside',
        texttemplate='%{text:,.1f}',
        hovertemplate=f'<b>Period B</b><br>{period_b_label}<br>Value: %{{y:,.1f}}<extra></extra>'
    ))

    # Format y-axis title based on unit
    if config['unit'] == 'currency':
        y_title = f"{config['label']} ({symbol})"
    elif config['unit'] == 'currency_per_hour':
        y_title = f"{config['label']} ({symbol}/hr)"
    elif config['unit'] == 'percentage':
        y_title = f"{config['label']} (%)"
    else:
        y_title = config['label']

    # Update layout
    fig.update_layout(
        title=f"{config['label']} Comparison",
        xaxis_title="",
        yaxis_title=y_title,
        barmode='group',
        showlegend=True,
        height=400,
        margin=dict(l=20, r=20, t=60, b=20),
        font=dict(size=14),
        hovermode='x unified'
    )

    # Render chart
    st.plotly_chart(fig, use_container_width=True)


def render_comparison_tab(filtered_df: pd.DataFrame) -> None:
    """
    Main render function for the Period Comparison tab.

    Args:
        filtered_df: Filtered time records DataFrame from sidebar
    """
    st.subheader("Period Comparison")

    # Initialize session state keys if not present
    if 'comparison_mode' not in st.session_state:
        st.session_state.comparison_mode = 'period'
    if 'comparison_months' not in st.session_state:
        st.session_state.comparison_months = 6
    if 'comparison_end_date' not in st.session_state:
        # Default to last date in dataset
        st.session_state.comparison_end_date = filtered_df['record_date'].max().date()
    if 'comparison_selected_metric' not in st.session_state:
        st.session_state.comparison_selected_metric = 'effective_rate'

    # Row 1: Selection Controls
    col1, col2, col3 = st.columns([2, 2, 2])

    with col1:
        comparison_mode = st.radio(
            "Comparison Mode",
            options=['period', 'year'],
            format_func=lambda x: 'Period vs Period' if x == 'period' else 'Year vs Year',
            index=0 if st.session_state.comparison_mode == 'period' else 1,
            horizontal=True,
            key='comparison_mode_radio'
        )
        st.session_state.comparison_mode = comparison_mode

    with col2:
        comparison_months = st.slider(
            "Time Frame (months)",
            min_value=1,
            max_value=12,
            value=st.session_state.comparison_months,
            step=1,
            key='comparison_months_slider'
        )
        st.session_state.comparison_months = comparison_months

    with col3:
        # Get max date from dataset
        max_date = filtered_df['record_date'].max().date()
        min_date = filtered_df['record_date'].min().date()

        comparison_end_date = st.date_input(
            "Period A End Date",
            value=st.session_state.comparison_end_date,
            min_value=min_date,
            max_value=max_date,
            key='comparison_end_date_picker'
        )
        st.session_state.comparison_end_date = comparison_end_date

    # Calculate period dates
    period_a_start, period_a_end, period_b_start, period_b_end = calculate_period_dates(
        st.session_state.comparison_end_date,
        st.session_state.comparison_months,
        st.session_state.comparison_mode
    )

    # Row 2: Display calculated periods
    st.markdown("---")
    col1, col2, col3 = st.columns([5, 1, 5])

    with col1:
        period_a_label = format_period_label(period_a_start, period_a_end)
        st.markdown(f"**Period A:** {period_a_label}")

    with col2:
        st.markdown("<div style='text-align: center; font-size: 20px; padding-top: 0px;'>vs</div>", unsafe_allow_html=True)

    with col3:
        period_b_label = format_period_label(period_b_start, period_b_end)
        st.markdown(f"**Period B:** {period_b_label}")

    # Validate Period B data availability
    is_valid, warning_msg = validate_period_data(filtered_df, period_b_start, period_b_end)

    if not is_valid:
        st.warning(warning_msg)
        st.info("💡 Try selecting a more recent end date or shorter time frame.")
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

    # Render summary cards
    st.markdown("### Key Metrics")
    render_summary_cards(comparison)

    # Render comparison chart
    st.markdown("---")
    st.markdown("### Detailed Comparison")

    # Metric selector for chart
    metric_config = get_metric_config()
    metric_options = {name: config['label'] for name, config in metric_config.items()}

    selected_metric = st.selectbox(
        "Select metric to visualize:",
        options=list(metric_options.keys()),
        format_func=lambda x: metric_options[x],
        index=list(metric_options.keys()).index(st.session_state.comparison_selected_metric),
        key='comparison_metric_selector'
    )
    st.session_state.comparison_selected_metric = selected_metric

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

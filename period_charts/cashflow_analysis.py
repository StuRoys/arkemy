"""
Cashflow Analysis Chart Module

This module provides cashflow visualization using Sankey diagrams and KPI cards.
Shows monthly income flow (hourly rate + fixed price fees) minus costs equalling profit.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from utils.currency_formatter import format_currency


def render_cashflow_analysis(df):
    """
    Render cashflow analysis page with Sankey diagram and KPI cards.

    Args:
        df: Unfiltered DataFrame from session state (time_records only)
    """
    if df is None or df.empty:
        st.warning("No data available for cashflow analysis")
        return

    # Ensure we're working with a copy
    df_copy = df.copy()

    # Convert record_date to datetime if needed
    if 'record_date' in df_copy.columns:
        df_copy['record_date'] = pd.to_datetime(df_copy['record_date'], errors='coerce')

    # Period selection
    st.markdown("### Period Selection")
    period_options = {
        "1M": 1,
        "3M": 3,
        "6M": 6,
        "1Y": 12,
        "All": "all"
    }

    selected_period_key = st.pills(
        "Period",
        options=list(period_options.keys()),
        default="1M",
        label_visibility="collapsed"
    )

    selected_period_value = period_options[selected_period_key]

    # Calculate periods
    max_date = df_copy['record_date'].max()

    if selected_period_value == "all":
        current_period_df = df_copy.copy()
        preceding_period_df = pd.DataFrame()  # No comparison for "All"
        has_preceding = False
    else:
        # Current period: last N months from max_date
        months = selected_period_value
        current_start = max_date - pd.DateOffset(months=months)
        current_period_df = df_copy[df_copy['record_date'] >= current_start]

        # Preceding period: same duration, immediately before current period
        preceding_start = current_start - pd.DateOffset(months=months)
        preceding_period_df = df_copy[
            (df_copy['record_date'] >= preceding_start) &
            (df_copy['record_date'] < current_start)
        ]
        has_preceding = not preceding_period_df.empty

    # Calculate metrics for current period
    current_metrics = calculate_cashflow_metrics(current_period_df)

    # Calculate metrics for preceding period (if available)
    if has_preceding:
        preceding_metrics = calculate_cashflow_metrics(preceding_period_df)
    else:
        preceding_metrics = {
            'total_income': 0,
            'total_cost': 0,
            'total_profit': 0,
            'hourly_fees': 0,
            'fixed_fees': 0
        }

    # Render Sankey Diagram
    st.markdown("### Cashflow Diagram")
    render_sankey_diagram(current_metrics)

    # Render KPI Cards
    st.markdown("### Period Comparison")
    render_kpi_cards(current_metrics, preceding_metrics, has_preceding)


def calculate_cashflow_metrics(df):
    """
    Calculate cashflow metrics from dataframe.

    Args:
        df: DataFrame with time_records data

    Returns:
        dict: Dictionary with cashflow metrics
    """
    if df.empty:
        return {
            'total_income': 0,
            'total_cost': 0,
            'total_profit': 0,
            'hourly_fees': 0,
            'fixed_fees': 0
        }

    # Calculate fees by price_model_type
    hourly_fees = 0
    fixed_fees = 0

    if 'price_model_type' in df.columns and 'fee_record' in df.columns:
        # Hourly rate fees
        hourly_mask = df['price_model_type'].str.lower() == 'hourly_rate'
        hourly_fees = df[hourly_mask]['fee_record'].sum() if hourly_mask.any() else 0

        # Fixed price fees
        fixed_mask = df['price_model_type'].str.lower() == 'fixed_price'
        fixed_fees = df[fixed_mask]['fee_record'].sum() if fixed_mask.any() else 0

    # Total income (sum of all fees)
    total_income = df['fee_record'].sum() if 'fee_record' in df.columns else 0

    # Total cost
    total_cost = df['cost_record'].sum() if 'cost_record' in df.columns else 0

    # Total profit
    total_profit = df['profit_record'].sum() if 'profit_record' in df.columns else 0

    return {
        'total_income': total_income,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'hourly_fees': hourly_fees,
        'fixed_fees': fixed_fees
    }


def render_sankey_diagram(metrics):
    """
    Render Sankey diagram showing cashflow.
    Flow: Hourly Fees + Fixed Price Fees → Total Income → Costs + Profit

    Args:
        metrics: Dictionary with cashflow metrics
    """
    # Define color map (blue for income, red for cost, green for profit)
    color_map = {
        "Hourly Rate Fees": "#5b7fa7",      # Deep blue
        "Fixed Price Fees": "#88b1df",      # Light blue
        "Total Income": "#1f77b4",          # Standard blue
        "Costs": "#e64a45",                 # Red
        "Profit": "#4caf50"                 # Green
    }

    # Extract metrics
    hourly_fees = metrics['hourly_fees']
    fixed_fees = metrics['fixed_fees']
    total_income = metrics['total_income']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']

    # Define nodes
    node_labels = [
        "Hourly Rate Fees",    # 0
        "Fixed Price Fees",    # 1
        "Total Income",        # 2
        "Costs",               # 3
        "Profit"               # 4
    ]

    node_colors = [color_map.get(label, "#000000") for label in node_labels]

    # Define links (connections)
    links = []

    # Hourly Fees → Total Income
    if hourly_fees > 0:
        links.append({"source": 0, "target": 2, "value": hourly_fees})

    # Fixed Price Fees → Total Income
    if fixed_fees > 0:
        links.append({"source": 1, "target": 2, "value": fixed_fees})

    # Total Income → Costs
    if total_cost > 0:
        links.append({"source": 2, "target": 3, "value": total_cost})

    # Total Income → Profit
    if total_profit > 0:
        links.append({"source": 2, "target": 4, "value": total_profit})

    # Create node values for hover display
    node_values = [hourly_fees, fixed_fees, total_income, total_cost, total_profit]

    # Format values for hover
    formatted_values = [format_currency(v, decimals=0) for v in node_values]

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",
        node=dict(
            pad=40,
            thickness=30,
            line=dict(color="black", width=0.5),
            label=node_labels,
            color=node_colors,
            customdata=formatted_values,
            hovertemplate='%{label}: %{customdata}<extra></extra>'
        ),
        link=dict(
            source=[link["source"] for link in links],
            target=[link["target"] for link in links],
            value=[link["value"] for link in links],
            hovertemplate='%{value:,.0f}<extra></extra>'
        )
    )])

    # Update layout
    fig.update_layout(
        font=dict(
            family="Arial, sans-serif",
            size=16,
            color="black"
        ),
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(255,255,255,0.9)',
        plot_bgcolor='rgba(255,255,255,0.9)'
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def render_kpi_cards(current_metrics, preceding_metrics, has_preceding):
    """
    Render KPI cards with period comparison.
    3 rows (Income, Cost, Profit) × 2 cols (Current, Preceding)

    Args:
        current_metrics: Dictionary with current period metrics
        preceding_metrics: Dictionary with preceding period metrics
        has_preceding: Boolean indicating if preceding period data exists
    """
    # Calculate deltas
    income_delta = current_metrics['total_income'] - preceding_metrics['total_income']
    cost_delta = current_metrics['total_cost'] - preceding_metrics['total_cost']
    profit_delta = current_metrics['total_profit'] - preceding_metrics['total_profit']

    # Row 1: Income (Blue)
    st.markdown("#### 💵 Income")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Current Period",
            value=format_currency(current_metrics['total_income'], decimals=0),
            delta=format_currency(income_delta, decimals=0) if has_preceding else None,
            delta_color="normal"
        )

    with col2:
        if has_preceding:
            st.metric(
                label="Preceding Period",
                value=format_currency(preceding_metrics['total_income'], decimals=0)
            )
        else:
            st.metric(
                label="Preceding Period",
                value="N/A"
            )

    # Row 2: Cost (Red)
    st.markdown("#### 💸 Cost")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Current Period",
            value=format_currency(current_metrics['total_cost'], decimals=0),
            delta=format_currency(cost_delta, decimals=0) if has_preceding else None,
            delta_color="inverse"  # Higher cost = bad (red), lower cost = good (green)
        )

    with col2:
        if has_preceding:
            st.metric(
                label="Preceding Period",
                value=format_currency(preceding_metrics['total_cost'], decimals=0)
            )
        else:
            st.metric(
                label="Preceding Period",
                value="N/A"
            )

    # Row 3: Profit (Green)
    st.markdown("#### 💰 Profit")
    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            label="Current Period",
            value=format_currency(current_metrics['total_profit'], decimals=0),
            delta=format_currency(profit_delta, decimals=0) if has_preceding else None,
            delta_color="normal"
        )

    with col2:
        if has_preceding:
            st.metric(
                label="Preceding Period",
                value=format_currency(preceding_metrics['total_profit'], decimals=0)
            )
        else:
            st.metric(
                label="Preceding Period",
                value="N/A"
            )

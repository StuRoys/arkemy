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

    # Period and Entity selection
    # Create 2-column layout for Period and Entity selectors
    col1, col2 = st.columns(2)

    with col1:
        period_options = {
            "1M": 1,
            "3M": 3,
            "6M": 6,
            "YTD": "ytd",
            "1Y": 12,
            "All": "all"
        }

        selected_period_key = st.pills(
            "Period",
            options=list(period_options.keys()),
            default="1M",
            label_visibility="visible"
        )

        selected_period_value = period_options.get(selected_period_key, 1)  # Default to 1 month if None

    with col2:
        entity_options = ["Project", "Customer", "Person", "Price Model"]

        selected_entity = st.pills(
            "View",
            options=entity_options,
            default="Project",
            label_visibility="visible"
        )

    # Calculate periods based on CURRENT date (today), not max_date in dataset
    current_date = pd.Timestamp.now()
    max_date = df_copy['record_date'].max()
    min_date = df_copy['record_date'].min()

    # Find last complete month (current month - 1)
    last_month_end = current_date.replace(day=1) - pd.DateOffset(days=1)
    last_complete_month_end = last_month_end.replace(day=1) + pd.offsets.MonthEnd(0)

    if selected_period_value == "all":
        current_start = min_date
        current_end = max_date
        current_period_df = df_copy.copy()

        # Comparison period: same period last year
        comparison_start = current_start - pd.DateOffset(years=1)
        comparison_end = current_end - pd.DateOffset(years=1)
        comparison_period_df = df_copy[
            (df_copy['record_date'] >= comparison_start) &
            (df_copy['record_date'] <= comparison_end)
        ]
        has_comparison = not comparison_period_df.empty
    elif selected_period_value == "ytd":
        # YTD: January 1st to end of last complete month
        year_start = pd.Timestamp(year=current_date.year, month=1, day=1)
        current_start = year_start
        current_end = last_complete_month_end

        current_period_df = df_copy[
            (df_copy['record_date'] >= current_start) &
            (df_copy['record_date'] <= current_end)
        ]

        # Comparison period: same period last year
        comparison_start = current_start - pd.DateOffset(years=1)
        comparison_end = current_end - pd.DateOffset(years=1)
        comparison_period_df = df_copy[
            (df_copy['record_date'] >= comparison_start) &
            (df_copy['record_date'] <= comparison_end)
        ]
        has_comparison = not comparison_period_df.empty
    else:
        # Month-based periods: N months ending at last complete month
        months = selected_period_value
        current_end = last_complete_month_end
        current_start = (current_end.replace(day=1) - pd.DateOffset(months=months-1))

        current_period_df = df_copy[
            (df_copy['record_date'] >= current_start) &
            (df_copy['record_date'] <= current_end)
        ]

        # Comparison period: same period last year
        comparison_start = current_start - pd.DateOffset(years=1)
        comparison_end = current_end - pd.DateOffset(years=1)
        comparison_period_df = df_copy[
            (df_copy['record_date'] >= comparison_start) &
            (df_copy['record_date'] <= comparison_end)
        ]
        has_comparison = not comparison_period_df.empty

    # Display date range below pills (show month boundaries)
    if selected_period_value == "all":
        date_range_text = f"{current_start.strftime('%b %Y').upper()} - {current_end.strftime('%b %Y').upper()}"
    else:
        date_range_text = f"{current_start.strftime('%b %Y').upper()} - {current_end.strftime('%b %Y').upper()}"

    st.caption(date_range_text)

    # Calculate metrics for current period
    current_metrics = calculate_cashflow_metrics(current_period_df, entity_type=selected_entity)

    # Calculate metrics for comparison period (same period last year)
    if has_comparison:
        comparison_metrics = calculate_cashflow_metrics(comparison_period_df, entity_type=selected_entity)
    else:
        comparison_metrics = {
            'total_income': 0,
            'total_cost': 0,
            'total_profit': 0,
            'project_fees': []
        }

    # Render Sankey Diagram
    render_sankey_diagram(current_metrics)

    # Render KPI Cards
    render_kpi_cards(current_metrics, comparison_metrics, has_comparison,
                     current_start, current_end, comparison_start, comparison_end)


def calculate_cashflow_metrics(df, entity_type="Project"):
    """
    Calculate cashflow metrics from dataframe, including entity-level fees.

    Args:
        df: DataFrame with time_records data
        entity_type: Type of entity to group by ("Project", "Customer", or "Person")

    Returns:
        dict: Dictionary with cashflow metrics including project_fees list
    """
    if df.empty:
        return {
            'total_income': 0,
            'total_cost': 0,
            'total_profit': 0,
            'project_fees': []
        }

    # Map entity type to column name
    entity_column_map = {
        "Project": "project_name",
        "Customer": "customer_name",
        "Person": "person_name",
        "Price Model": "price_model_type"
    }

    entity_column = entity_column_map.get(entity_type, "project_name")

    # Calculate entity-level fees
    project_fees = []
    if entity_column in df.columns and 'fee_record' in df.columns:
        entity_groups = df.groupby(entity_column)['fee_record'].sum()
        # Filter out entities with 0 fees and sort by fee amount (descending)
        project_fees = [
            {'name': name, 'fee': fee}
            for name, fee in entity_groups.items()
            if fee > 0
        ]
        project_fees.sort(key=lambda x: x['fee'], reverse=True)

    # Total income (sum of all fees)
    total_income = df['fee_record'].sum() if 'fee_record' in df.columns else 0

    # Total cost
    total_cost = df['cost_record'].sum() if 'cost_record' in df.columns else 0

    # Total profit (calculated as income - cost to ensure they add up to 100%)
    total_profit = total_income - total_cost

    return {
        'total_income': total_income,
        'total_cost': total_cost,
        'total_profit': total_profit,
        'project_fees': project_fees
    }


def render_sankey_diagram(metrics, top_n_projects=10):
    """
    Render Sankey diagram showing cashflow.
    Flow: Project 1 + Project 2 + ... → Total Income → Profit + Costs

    Args:
        metrics: Dictionary with cashflow metrics including project_fees
        top_n_projects: Number of top projects to show individually (default 10)
    """
    # Extract metrics
    project_fees = metrics['project_fees']
    total_income = metrics['total_income']
    total_cost = metrics['total_cost']
    total_profit = metrics['total_profit']

    # Split projects into top N and others
    if len(project_fees) > top_n_projects:
        top_projects = project_fees[:top_n_projects]
        other_projects = project_fees[top_n_projects:]

        # Calculate total for "Other"
        other_total = sum(p['fee'] for p in other_projects)

        # Add "Other" as a single node
        display_projects = top_projects + [{'name': f'Other ({len(other_projects)})', 'fee': other_total}]
    else:
        display_projects = project_fees

    # Build node labels: Projects + Total Income + Profit + Costs
    node_labels = []
    node_values = []

    # Add project nodes with percentages
    for project in display_projects:
        percentage = (project['fee'] / total_income * 100) if total_income > 0 else 0
        label_with_percentage = f"{project['name']} ({percentage:.1f}%)"
        node_labels.append(label_with_percentage)
        node_values.append(project['fee'])

    # Calculate index for Total Income node
    total_income_idx = len(node_labels)

    # Add Total Income, Profit, Costs nodes with percentages
    profit_percentage = (total_profit / total_income * 100) if total_income > 0 else 0
    cost_percentage = (total_cost / total_income * 100) if total_income > 0 else 0

    node_labels.extend([
        "Total Income (100%)",
        f"Profit ({profit_percentage:.1f}%)",
        f"Costs ({cost_percentage:.1f}%)"
    ])
    node_values.extend([total_income, total_profit, total_cost])

    # Calculate indices for Profit and Costs
    profit_idx = total_income_idx + 1
    costs_idx = total_income_idx + 2

    # Generate colors for nodes
    # Use a color palette for projects, specific colors for Income/Profit/Costs
    project_colors = [
        "#5b7fa7", "#88b1df", "#7eb3d5", "#a8c5e3", "#4a9bd1",
        "#6ba3d0", "#8cb8dc", "#5d92c2", "#7aa5cf", "#93bbde"
    ]

    node_colors = []
    for i in range(len(display_projects)):
        # Cycle through project colors (last one is "Other" if grouped)
        if i == len(display_projects) - 1 and len(project_fees) > top_n_projects:
            # Use a distinct color for "Other"
            node_colors.append("#9ca3af")  # Gray for "Other"
        else:
            # Cycle through project colors
            node_colors.append(project_colors[i % len(project_colors)])

    # Add specific colors for Total Income, Profit, Costs
    node_colors.extend([
        "#1f77b4",  # Total Income - Standard blue
        "#4caf50",  # Profit - Green
        "#e64a45"   # Costs - Red
    ])

    # Format values for hover
    formatted_values = [format_currency(v, decimals=0) for v in node_values]

    # Combine label and value for hover
    hover_labels = [f"{label}<br>{value}" for label, value in zip(node_labels, formatted_values)]

    # Define links (connections)
    link_sources = []
    link_targets = []
    link_values = []
    link_colors = []

    # Projects → Total Income
    for i, project in enumerate(display_projects):
        link_sources.append(i)
        link_targets.append(total_income_idx)
        link_values.append(project['fee'])
        # Use project color with transparency
        color = node_colors[i]
        rgba_color = f"rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.3)"
        link_colors.append(rgba_color)

    # Total Income → Profit
    if total_profit > 0:
        link_sources.append(total_income_idx)
        link_targets.append(profit_idx)
        link_values.append(total_profit)
        link_colors.append('rgba(76, 175, 80, 0.3)')  # Green with transparency

    # Total Income → Costs
    if total_cost > 0:
        link_sources.append(total_income_idx)
        link_targets.append(costs_idx)
        link_values.append(total_cost)
        link_colors.append('rgba(230, 74, 69, 0.3)')  # Red with transparency

    # Create the Sankey diagram
    fig = go.Figure(data=[go.Sankey(
        arrangement="snap",  # Auto-arrange nodes
        node=dict(
            pad=20,
            thickness=25,
            line=dict(color="rgba(226, 232, 240, 0.2)", width=1),
            label=node_labels,  # Show labels on nodes
            color=node_colors,
            customdata=hover_labels,
            hovertemplate='%{customdata}<extra></extra>'
        ),
        link=dict(
            source=link_sources,
            target=link_targets,
            value=link_values,
            color=link_colors,
            hovertemplate='%{value:,.0f}<extra></extra>'
        )
    )])

    # Update layout - match dark theme
    fig.update_layout(
        font=dict(
            family="Space Grotesk, sans-serif",
            size=12,
            color="#e2e8f0"  # Theme textColor
        ),
        height=500,
        margin=dict(l=20, r=20, t=20, b=20),
        paper_bgcolor='rgba(29, 41, 61, 0.3)',  # backgroundColor with transparency
        plot_bgcolor='rgba(0, 0, 0, 0)'  # Transparent plot background
    )

    # Display the chart
    st.plotly_chart(fig, use_container_width=True)


def render_kpi_cards(current_metrics, comparison_metrics, has_comparison,
                     current_start, current_end, comparison_start, comparison_end):
    """
    Render KPI cards with year-over-year comparison using colored containers.
    3 containers (Income, Cost, Profit) with 2 rows each (Current Year, Previous Year)

    Args:
        current_metrics: Dictionary with current period metrics
        comparison_metrics: Dictionary with comparison period metrics (same period last year)
        has_comparison: Boolean indicating if comparison period data exists
        current_start: Start date of current period
        current_end: End date of current period
        comparison_start: Start date of comparison period
        comparison_end: End date of comparison period
    """
    # Calculate deltas
    income_delta = current_metrics['total_income'] - comparison_metrics['total_income']
    cost_delta = current_metrics['total_cost'] - comparison_metrics['total_cost']
    profit_delta = current_metrics['total_profit'] - comparison_metrics['total_profit']

    # Format date labels
    current_label = f"{current_start.strftime('%b %Y').upper()} - {current_end.strftime('%b %Y').upper()}"
    comparison_label = f"{comparison_start.strftime('%b %Y').upper()} - {comparison_end.strftime('%b %Y').upper()}"

    # Create 3 columns for the containers
    metric_col1, metric_col2, metric_col3 = st.columns(3)

    # Income Container (Blue accent)
    with metric_col1:
        income_container = st.container(border=True)
        with income_container:
            st.markdown("#### Income")
            st.metric(
                label=current_label,
                value=format_currency(current_metrics['total_income'], decimals=0),
                delta=format_currency(income_delta, decimals=0) if has_comparison else None,
                delta_color="normal"
            )
            if has_comparison:
                st.metric(
                    label=comparison_label,
                    value=format_currency(comparison_metrics['total_income'], decimals=0)
                )
            else:
                st.metric(
                    label=comparison_label,
                    value="N/A"
                )

    # Cost Container (Red accent)
    with metric_col2:
        cost_container = st.container(border=True)
        with cost_container:
            st.markdown("#### Cost")
            st.metric(
                label=current_label,
                value=format_currency(current_metrics['total_cost'], decimals=0),
                delta=format_currency(cost_delta, decimals=0) if has_comparison else None,
                delta_color="inverse"  # Higher cost = bad (red), lower cost = good (green)
            )
            if has_comparison:
                st.metric(
                    label=comparison_label,
                    value=format_currency(comparison_metrics['total_cost'], decimals=0)
                )
            else:
                st.metric(
                    label=comparison_label,
                    value="N/A"
                )

    # Profit Container (Green accent)
    with metric_col3:
        profit_container = st.container(border=True)
        with profit_container:
            st.markdown("#### Profit")
            st.metric(
                label=current_label,
                value=format_currency(current_metrics['total_profit'], decimals=0),
                delta=format_currency(profit_delta, decimals=0) if has_comparison else None,
                delta_color="normal"
            )
            if has_comparison:
                st.metric(
                    label=comparison_label,
                    value=format_currency(comparison_metrics['total_profit'], decimals=0)
                )
            else:
                st.metric(
                    label=comparison_label,
                    value="N/A"
                )

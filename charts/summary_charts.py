# charts/summary_charts.py
import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np
from typing import Dict, Any, List, Tuple
from utils.chart_styles import get_currency_formatting
from utils.currency_formatter import format_millions, get_currency_code, CURRENCY_SYMBOLS

def render_summary_tab(
    filtered_df: pd.DataFrame,
    filter_settings: Dict[str, Any]
) -> None:
    """
    Renders a matrix of project performance data.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        filter_settings: Dictionary containing all active filter settings
    """
    
    # Check if dataframe is empty
    if filtered_df.empty:
        st.warning("No data available with the current filter settings. Please adjust your filters to see a summary.")
        return
    
    # Generate filter description
    filter_description = generate_filter_description(filter_settings)
    
    # Calculate key metrics
    total_hours = filtered_df["hours_used"].sum()
    total_billable_hours = filtered_df["hours_billable"].sum()
    billability_percentage = (total_billable_hours / total_hours * 100) if total_hours > 0 else 0
    total_projects = filtered_df["project_number"].nunique()
    
    # Fee metrics (if hourly rate exists)
    has_fee = "billable_rate_record" in filtered_df.columns
    total_fee = None
    if has_fee:
        total_fee = (filtered_df["hours_billable"] * filtered_df["billable_rate_record"]).sum()
        avg_hourly_rate = total_fee / total_billable_hours if total_billable_hours > 0 else 0
    
    # Get data for matrix
    customer_insights = get_customer_insights(filtered_df, top_n=10)
    project_insights = get_top_projects(filtered_df, top_n=10)
    project_type_insights = get_project_type_insights(filtered_df, top_n=10)
    phase_insights = get_phase_insights(filtered_df, top_n=10)
    activity_insights = get_activity_insights(filtered_df, top_n=10)
    
    st.markdown("<hr>", unsafe_allow_html=True)
    
    # Define card styles once
    st.markdown("""
        <style>
        .card-container {
            background-color: #f8f9fa;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            height: 100%;
            min-height: 140px;
        }
        .card-title {
            font-size: 1.2rem;
            font-weight: bold;
            margin-bottom: 10px;
            color: #1E3050;
            border-bottom: 1px solid #dee2e6;
            padding-bottom: 5px;
        }
        .card-content {
            font-size: 1.1rem;
        }
        .no-data {
            color: #6c757d;
            font-style: italic;
        }
        .matrix-header {
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
            font-size: 1.4rem;
        }
        .row-header {
            font-weight: bold;
            margin-top: 10px;
            margin-bottom: 5px;
            font-size: 1.3rem;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create matrix layout headers
    col_headers = st.columns(3)
    with col_headers[0]:
        st.markdown('<div class="matrix-header">💰 Fee</div>', unsafe_allow_html=True)
    with col_headers[1]:
        st.markdown('<div class="matrix-header">⏱️ Hours Worked</div>', unsafe_allow_html=True)
    with col_headers[2]:
        st.markdown('<div class="matrix-header">💲 Avg. Hourly Rate</div>', unsafe_allow_html=True)
        
    # Row 1: Customers
    st.markdown('<div class="row-header">🏢 Customers</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Fee
    with cols[0]:
        create_card(
            title="Top Customers by Fee",
            content=render_by_fee(customer_insights.get("top_customers", []), has_fee, "customer"),
            show_data=has_fee and len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Customers by Hours",
            content=render_by_hours(customer_insights.get("top_customers", []), "customer"),
            show_data=len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Customers by Hourly Rate",
            content=render_by_rate(customer_insights.get("top_customers", []), has_fee, "customer"),
            show_data=has_fee and len(customer_insights.get("top_customers", [])) > 0
        )
    
    # Row 2: Projects
    st.markdown('<div class="row-header">📋 Projects</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Fee
    with cols[0]:
        create_card(
            title="Top Projects by Fee",
            content=render_by_fee(project_insights, has_fee, "project"),
            show_data=has_fee and len(project_insights) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Projects by Hours",
            content=render_by_hours(project_insights, "project"),
            show_data=len(project_insights) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Projects by Hourly Rate",
            content=render_by_rate(project_insights, has_fee, "project"),
            show_data=has_fee and len(project_insights) > 0
        )
    
    # Row 3: Project Types
    st.markdown('<div class="row-header">📊 Project Types</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Fee
    with cols[0]:
        create_card(
            title="Top Project Types by Fee",
            content=render_by_fee(project_type_insights.get("top_project_types", []), has_fee, "project_type"),
            show_data=has_fee and len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Project Types by Hours",
            content=render_by_hours(project_type_insights.get("top_project_types", []), "project_type"),
            show_data=len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Project Types by Hourly Rate",
            content=render_by_rate(project_type_insights.get("top_project_types", []), has_fee, "project_type"),
            show_data=has_fee and len(project_type_insights.get("top_project_types", [])) > 0
        )
    
    # Row 4: Phases
    st.markdown('<div class="row-header">🔄 Phases</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Fee
    with cols[0]:
        create_card(
            title="Top Phases by Fee",
            content=render_by_fee(phase_insights.get("top_phases", []), has_fee, "phase"),
            show_data=has_fee and len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Phases by Hours",
            content=render_by_hours(phase_insights.get("top_phases", []), "phase"),
            show_data=len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Phases by Hourly Rate",
            content=render_by_rate(phase_insights.get("top_phases", []), has_fee, "phase"),
            show_data=has_fee and len(phase_insights.get("top_phases", [])) > 0
        )
    
    # Row 5: Activities
    st.markdown('<div class="row-header">🔨 Activities</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    
    # Fee
    with cols[0]:
        create_card(
            title="Top Activities by Fee",
            content=render_by_fee(activity_insights.get("top_activities", []), has_fee, "activity"),
            show_data=has_fee and len(activity_insights.get("top_activities", [])) > 0
        )
    
    # Hours
    with cols[1]:
        create_card(
            title="Top Activities by Hours",
            content=render_by_hours(activity_insights.get("top_activities", []), "activity"),
            show_data=len(activity_insights.get("top_activities", [])) > 0
        )
    
    # Rate
    with cols[2]:
        create_card(
            title="Top Activities by Hourly Rate",
            content=render_by_rate(activity_insights.get("top_activities", []), has_fee, "activity"),
            show_data=has_fee and len(activity_insights.get("top_activities", [])) > 0
        )


def create_card(title: str, content: str, show_data: bool = True) -> None:
    """
    Creates a card-like container for displaying information.
    
    Args:
        title: Card title
        content: Card content (HTML/markdown)
        show_data: Whether to show data or a placeholder message
    """
    # Create the card HTML
    if show_data:
        st.markdown(f"""
            <div class="card-container">
                <div class="card-title">{title}</div>
                <div class="card-content">
                    {content}
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div class="card-container">
                <div class="card-title">{title}</div>
                <div class="card-content">
                    <div class="no-data">No data available</div>
        """, unsafe_allow_html=True)


def render_by_fee(items: List[Dict[str, Any]], has_fee: bool, item_type: str) -> str:
    """
    Renders HTML for items sorted by fee
    
    Args:
        items: List of items (customers, projects, etc.)
        has_fee: Whether fee data is available
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items or not has_fee:
        return "<div class='no-data'>No fee data available</div>"
    
    # Sort items by fee if present
    sorted_items = sorted(items, key=lambda x: x.get('fee', 0), reverse=True)
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        if "fee" not in item:
            continue
            
        item_name = item.get('name', '')
        fee = format_millions(item['fee'])
        
        # Add percentage if available or calculate it
        percentage_text = ""
        if "fee_percentage" in item:
            percentage_text = f" ({item['fee_percentage']:.1f}% of total)"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{fee}{percentage_text}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No fee data available</div>"


def render_by_hours(items: List[Dict[str, Any]], item_type: str) -> str:
    """
    Renders HTML for items sorted by hours worked
    
    Args:
        items: List of items (customers, projects, etc.)
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items:
        return "<div class='no-data'>No hours data available</div>"
    
    # Sort items by hours if present
    sorted_items = sorted(items, key=lambda x: x.get('hours', 0), reverse=True)
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        if "hours" not in item:
            continue
            
        item_name = item.get('name', '')
        # Format hours as whole number with space as thousand separator
        hours = f"{int(item['hours']):,}".replace(',', ' ') + " hours"
        
        # Add additional context based on item type
        context_text = ""
        if item_type == "customer" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        elif item_type == "project" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        elif item_type == "project_type" and "projects" in item:
            context_text = f" ({item['projects']} projects)"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{hours}{context_text}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No hours data available</div>"


def render_by_rate(items: List[Dict[str, Any]], has_fee: bool, item_type: str) -> str:
    """
    Renders HTML for items sorted by hourly rate
    
    Args:
        items: List of items (customers, projects, etc.)
        has_fee: Whether fee data is available
        item_type: Type of item (customer, project, etc.)
    
    Returns:
        HTML string with formatted content
    """
    if not items or not has_fee:
        return "<div class='no-data'>No hourly rate data available</div>"
    
    # Calculate and add hourly rate if not present
    for item in items:
        if "fee" in item and "hours" in item and "rate" not in item and item["hours"] > 0:
            item["rate"] = item["fee"] / item["hours"]
    
    # Sort items by rate
    sorted_items = sorted(items, key=lambda x: x.get('rate', 0) 
                          if isinstance(x.get('rate', 0), (int, float)) else 0, reverse=True)
    
    # Get currency formatting
    symbol, position, _ = get_currency_formatting()
    
    html = ""
    for i, item in enumerate(sorted_items[:10]):
        # Skip items with no hourly rate or with zero hours
        if "rate" not in item or item.get("hours", 0) <= 0:
            continue
            
        item_name = item.get('name', '')
        
        # Format the rate with appropriate currency symbol and position
        if position == 'before':
            rate = f"{symbol}{item['rate']:.0f}/hour"
        else:
            rate = f"{item['rate']:.0f} {symbol}/hour"
        
        html += f"""
            <div style="margin-bottom: 8px;">
                <div style="font-weight: bold;">{i+1}. {item_name}</div>
                <div>{rate}</div>
            </div>
        """
    
    return html if html else "<div class='no-data'>No hourly rate data available</div>"


def generate_filter_description(filter_settings: Dict[str, Any]) -> str:
    """
    Generates a natural language description of the applied filters.
    
    Args:
        filter_settings: Dictionary containing all active filter settings
        
    Returns:
        String describing the filters that are applied
    """
    descriptions = []
    
    # Date filter description
    if "date_filter_type" in filter_settings:
        if filter_settings["date_filter_type"] == "All time":
            descriptions.append("across all time periods")
        elif filter_settings["date_filter_type"] == "Custom range":
            start_date = filter_settings.get("start_date")
            end_date = filter_settings.get("end_date")
            if start_date and end_date:
                start_str = start_date.strftime("%B %d, %Y")
                end_str = end_date.strftime("%B %d, %Y")
                descriptions.append(f"from {start_str} to {end_str}")
        else:
            descriptions.append(f"during {filter_settings['date_filter_type'].lower()}")
    
    # Customer filter description
    if "included_customers" in filter_settings and filter_settings["included_customers"]:
        if len(filter_settings["included_customers"]) == 1:
            descriptions.append(f"for customer {filter_settings['included_customers'][0]}")
        else:
            descriptions.append(f"for {len(filter_settings['included_customers'])} selected customers")
    
    # Project filter description
    if "included_projects" in filter_settings and filter_settings["included_projects"]:
        if len(filter_settings["included_projects"]) == 1:
            descriptions.append(f"focusing on project {filter_settings['included_projects'][0]}")
        else:
            descriptions.append(f"focusing on {len(filter_settings['included_projects'])} selected projects")
    
    # Project type filter description
    if "included_types" in filter_settings and filter_settings["included_types"]:
        if len(filter_settings["included_types"]) == 1:
            descriptions.append(f"for {filter_settings['included_types'][0]} type projects")
        else:
            descriptions.append(f"for {', '.join(filter_settings['included_types'])} type projects")

    # Project hours range filter description
    if "project_min_hours" in filter_settings and "project_max_hours" in filter_settings:
        min_hours = filter_settings["project_min_hours"]
        max_hours = filter_settings["project_max_hours"]
        descriptions.append(f"in projects between {min_hours} and {max_hours} hours")
    
    # Billability filter description
    if "selected_billability" in filter_settings:
        if filter_settings["selected_billability"] == "billable":
            descriptions.append("considering only billable hours")
        elif filter_settings["selected_billability"] == "non-billable":
            descriptions.append("considering only non-billable hours")
    
    # Combine all descriptions
    if descriptions:
        return "Based on time records " + ", ".join(descriptions) + ", "
    else:
        return "Based on all time records, "


def get_top_projects(df: pd.DataFrame, top_n: int = 3) -> List[Dict[str, Any]]:
    """
    Identifies the top projects by fee.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top projects to return
        
    Returns:
        List of dictionaries with project metrics
    """
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "project_name" not in df.columns or "project_number" not in df.columns:
        return []
    
    # Check if we can calculate fee
    has_fee = "billable_rate_record" in df.columns and "hours_billable" in df.columns
    
    # Aggregate data by project
    project_metrics = []
    
    # Group by project and calculate metrics
    project_agg = df.groupby(["project_number", "project_name"]).agg({
        "hours_used": "sum",
        "hours_billable": "sum"
    }).reset_index()
    
    if has_fee:
        # Calculate fee
        project_agg["Fee"] = df.groupby(["project_number"]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")["Fee"]
        
        # Calculate hourly rate
        project_agg["Rate"] = project_agg["Fee"] / project_agg["hours_used"].where(project_agg["hours_used"] > 0, 1)
        
        # Calculate total fee for percentage calculation
        total_fee = project_agg["Fee"].sum()
    
    # Create project info dictionaries
    for _, project in project_agg.iterrows():
        project_info = {
            "number": project["project_number"],
            "name": project["project_name"],
            "hours": project["hours_used"]
        }
        
        if has_fee:
            project_info["fee"] = project["Fee"]
            project_info["rate"] = project["Rate"]
            project_info["fee_percentage"] = (project["Fee"] / total_fee * 100) if total_fee > 0 else 0
        
        project_metrics.append(project_info)
    
    return project_metrics


def get_customer_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about top customers from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top customers to return
        
    Returns:
        Dictionary with customer insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "customer_number" not in df.columns or "customer_name" not in df.columns:
        return insights
    
    # Calculate customer metrics
    customer_agg = df.groupby(["customer_number", "customer_name"]).agg({
        "hours_used": "sum",
        "project_number": "nunique"
    }).reset_index()
    
    # Check if we can calculate fee
    has_fee = "billable_rate_record" in df.columns and "hours_billable" in df.columns
    
    if has_fee:
        # Calculate fee by customer
        customer_agg["Fee"] = df.groupby(["customer_number"]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")["Fee"]
        
        # Calculate hourly rate
        customer_agg["Rate"] = customer_agg["Fee"] / customer_agg["hours_used"].where(customer_agg["hours_used"] > 0, 1)
        
        # Calculate total fee
        total_fee = customer_agg["Fee"].sum()
    
    # Store top customers data
    top_customers_list = []
    for _, customer in customer_agg.iterrows():
        customer_info = {
            "name": customer["customer_name"],
            "number": customer["customer_number"],
            "hours": customer["hours_used"],
            "projects": customer["project_number"]
        }
        
        if has_fee:
            customer_info["fee"] = customer["Fee"]
            customer_info["rate"] = customer["Rate"]
            customer_info["fee_percentage"] = (customer["Fee"] / total_fee * 100) if total_fee > 0 else 0
        
        top_customers_list.append(customer_info)
    
    insights["top_customers"] = top_customers_list
    insights["total_customers"] = len(customer_agg)
    
    return insights


def get_project_type_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about project types from the filtered data.

    Args:
        df: Filtered DataFrame
        top_n: Number of top project types to return

    Returns:
        Dictionary with project type insights
    """
    from utils.processors import get_all_tag_columns, aggregate_by_project_tag

    insights = {}

    # Check if dataframe is empty or lacks necessary columns
    available_tags = get_all_tag_columns(df)
    if df.empty or not available_tags:
        return insights

    # Use the first (legacy) tag column for summary insights
    tag_column = available_tags[0]

    # Calculate project type metrics using the generic function
    project_type_agg = aggregate_by_project_tag(df, tag_column=tag_column)

    if project_type_agg.empty:
        return insights

    # Check if we have fee data
    has_fee = "Fee" in project_type_agg.columns

    # Calculate total fee for percentage calculation
    total_fee = project_type_agg["Fee"].sum() if has_fee else 0

    # Store top project types data
    top_project_types_list = []
    for _, project_type in project_type_agg.iterrows():
        project_type_info = {
            "name": project_type[tag_column],
            "hours": project_type["hours_used"],
            "projects": project_type["Number of projects"]
        }

        if has_fee:
            project_type_info["fee"] = project_type["Fee"]
            project_type_info["rate"] = project_type["Effective rate"]
            project_type_info["fee_percentage"] = (project_type["Fee"] / total_fee * 100) if total_fee > 0 else 0

        top_project_types_list.append(project_type_info)

    insights["top_project_types"] = top_project_types_list
    insights["total_project_types"] = len(project_type_agg)

    return insights


def get_phase_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about project phases from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top phases to return
        
    Returns:
        Dictionary with phase insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "phase_tag" not in df.columns:
        return insights
    
    # Calculate phase metrics
    phase_agg = df.groupby(["phase_tag"]).agg({
        "hours_used": "sum"
    }).reset_index()
    
    # Check if we can calculate fee
    has_fee = "billable_rate_record" in df.columns and "hours_billable" in df.columns
    
    if has_fee:
        # Calculate fee by phase
        phase_agg["Fee"] = df.groupby(["phase_tag"]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")["Fee"]
        
        # Calculate hourly rate
        phase_agg["Rate"] = phase_agg["Fee"] / phase_agg["hours_used"].where(phase_agg["hours_used"] > 0, 1)
        
        # Calculate total fee for percentage calculation
        total_fee = phase_agg["Fee"].sum()
    
    # Store top phases data
    top_phases_list = []
    for _, phase in phase_agg.iterrows():
        phase_info = {
            "name": phase["phase_tag"],
            "hours": phase["hours_used"]
        }
        
        if has_fee:
            phase_info["fee"] = phase["Fee"]
            phase_info["rate"] = phase["Rate"]
            phase_info["fee_percentage"] = (phase["Fee"] / total_fee * 100) if total_fee > 0 else 0
        
        top_phases_list.append(phase_info)
    
    insights["top_phases"] = top_phases_list
    insights["total_phases"] = len(phase_agg)
    
    return insights


def get_activity_insights(df: pd.DataFrame, top_n: int = 3) -> Dict[str, Any]:
    """
    Extracts key insights about activities from the filtered data.
    
    Args:
        df: Filtered DataFrame
        top_n: Number of top activities to return
        
    Returns:
        Dictionary with activity insights
    """
    insights = {}
    
    # Check if dataframe is empty or lacks necessary columns
    if df.empty or "activity_tag" not in df.columns:
        return insights
    
    # Calculate activity metrics
    activity_agg = df.groupby(["activity_tag"]).agg({
        "hours_used": "sum"
    }).reset_index()
    
    # Check if we can calculate fee
    has_fee = "billable_rate_record" in df.columns and "hours_billable" in df.columns
    
    if has_fee:
        # Calculate fee by activity
        activity_agg["Fee"] = df.groupby(["activity_tag"]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")["Fee"]
        
        # Calculate hourly rate
        activity_agg["Rate"] = activity_agg["Fee"] / activity_agg["hours_used"].where(activity_agg["hours_used"] > 0, 1)
        
        # Calculate total fee for percentage calculation
        total_fee = activity_agg["Fee"].sum()
    
    # Store top activities data
    top_activities_list = []
    for _, activity in activity_agg.iterrows():
        activity_info = {
            "name": activity["activity_tag"],
            "hours": activity["hours_used"]
        }
        
        if has_fee:
            activity_info["fee"] = activity["Fee"]
            activity_info["rate"] = activity["Rate"]
            activity_info["fee_percentage"] = (activity["Fee"] / total_fee * 100) if total_fee > 0 else 0
        
        top_activities_list.append(activity_info)
    
    insights["top_activities"] = top_activities_list
    insights["total_activities"] = len(activity_agg)
    
    return insights
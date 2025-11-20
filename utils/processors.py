# processors.py
import pandas as pd
import numpy as np
import re
from typing import Dict, List, Tuple, Any, Optional
from utils.tag_manager import get_tag_display_name
from utils.chart_styles import SUM_METRICS


def add_percentage_columns(df: pd.DataFrame, sum_metrics: List[str]) -> pd.DataFrame:
    """
    Add percentage columns for sum metrics.

    For each metric in sum_metrics, creates a new column with '_pct' suffix
    containing the percentage of that metric relative to its total.

    Args:
        df: DataFrame to add percentage columns to
        sum_metrics: List of column names to calculate percentages for

    Returns:
        DataFrame with new percentage columns added
    """
    # Make a copy to avoid modifying the original
    result_df = df.copy()

    # For each sum metric, calculate its percentage of the total
    for metric in sum_metrics:
        if metric in result_df.columns:
            total = result_df[metric].sum()
            if total > 0:
                result_df[f'{metric}_pct'] = (result_df[metric] / total) * 100
            else:
                # Handle edge case where total is 0
                result_df[f'{metric}_pct'] = 0

    return result_df


def get_all_tag_columns(df: pd.DataFrame) -> list:
    """
    Detect tag columns with specific prefixes.
    Matches columns starting with: project_tag*, phase_tag*, activity_tag*, record_tag*

    Args:
        df: DataFrame to search

    Returns:
        List of tag column names, sorted by prefix groups then index
        Example: ['activity_tag_1', 'phase_tag_1', 'phase_tag_2', 'project_tag_1', 'project_tag_2', 'record_tag_1']
    """
    # Whitelist of allowed tag prefixes
    allowed_prefixes = ['project_tag', 'phase_tag', 'activity_tag', 'record_tag']

    tag_cols = []

    for col in df.columns:
        # Check if column starts with any allowed prefix
        for prefix in allowed_prefixes:
            if col.startswith(prefix):
                tag_cols.append(col)
                break  # Don't check other prefixes

    # Sort by prefix groups, then by index
    def sort_key(col):
        for prefix in allowed_prefixes:
            if col.startswith(prefix):
                # Extract what comes after the prefix
                remainder = col[len(prefix):]
                if remainder == '':
                    # Just 'project_tag' with no suffix
                    return (prefix, 0, col)
                elif remainder.startswith('_'):
                    # 'project_tag_1' or 'project_tag_2'
                    try:
                        index = int(remainder[1:])
                        return (prefix, index, col)
                    except ValueError:
                        return (prefix, 0, col)
        return (col, 999, col)  # Fallback

    sorted_cols = sorted(tag_cols, key=sort_key)
    return sorted_cols


def get_project_tag_columns(df: pd.DataFrame) -> list:
    """
    DEPRECATED: Use get_all_tag_columns() instead.
    Kept for backward compatibility.

    Detect all project tag columns in the dataframe.
    Handles both 'project_tag' (legacy) and 'project_tag_*' (indexed) patterns.

    Args:
        df: DataFrame to search

    Returns:
        List of tag column names in order: ['project_tag', 'project_tag_1', 'project_tag_2', ...]
    """
    return get_all_tag_columns(df)


def get_project_tag_columns_with_labels(df: pd.DataFrame, tag_mappings: Dict[str, str] = None) -> Dict[str, str]:
    """
    Get project tag columns with their display labels.

    Args:
        df: DataFrame to search
        tag_mappings: Optional mapping of column_name -> display_label from extract_tag_mappings()

    Returns:
        Dictionary mapping: {column_name: display_label}
        Example: {'project_tag_1': 'Prosjekttype', 'project_tag_2': 'Prosjektfase'}
    """
    if tag_mappings is None:
        tag_mappings = {}

    tag_cols = get_project_tag_columns(df)
    result = {}

    for col in tag_cols:
        display_name = get_tag_display_name(col, tag_mappings)
        result[col] = display_name

    return result


def calculate_profit_from_totals(total_fee: float, total_cost: float) -> float:
    """
    Calculate profit as the difference between total fee and total cost.

    Args:
        total_fee: Total fees earned
        total_cost: Total costs incurred

    Returns:
        Profit (fee - cost)
    """
    return total_fee - total_cost


def calculate_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics from the validated dataframe.

    Args:
        df: Validated and transformed dataframe

    Returns:
        Dictionary containing summary metrics
    """
    metrics = {}
    
    # Count metrics
    metrics["total_entries"] = len(df)
    metrics["unique_customers"] = df["customer_number"].nunique()
    metrics["unique_projects"] = df["project_number"].nunique()
    metrics["unique_people"] = df["person_name"].nunique()
    
    # Sum metrics
    metrics["total_hours"] = df["hours_used"].sum()
    metrics["total_billable_hours"] = df["hours_billable"].sum()
    
    # Date metrics
    if "record_date" in df.columns and not df.empty:
        metrics["first_time_record"] = df["record_date"].min()
        metrics["last_time_record"] = df["record_date"].max()
        # Calculate years between first and last time record
        date_diff = metrics["last_time_record"] - metrics["first_time_record"]
        metrics["years_between"] = date_diff.days / 365.25  # More accurate representation of a year
    else:
        metrics["first_time_record"] = None
        metrics["last_time_record"] = None
        metrics["years_between"] = 0
    
    # Calculated metrics
    if metrics["total_hours"] > 0:
        metrics["billability_percentage"] = (metrics["total_billable_hours"] / metrics["total_hours"]) * 100
    else:
        metrics["billability_percentage"] = 0
    
    # Fee metrics (new approach with fallback)
    if "fee_record" in df.columns:
        metrics["total_fee"] = df["fee_record"].sum()
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        billable_df = df.copy()
        billable_df.loc[billable_df["hours_billable"] <= 0, "billable_rate_record"] = 0
        metrics["total_fee"] = (billable_df["hours_billable"] * billable_df["billable_rate_record"]).sum()
    else:
        metrics["total_fee"] = 0
    
    # Cost metrics
    if "cost_record" in df.columns:
        metrics["total_cost"] = df["cost_record"].sum()
    else:
        metrics["total_cost"] = 0

    # Profit metrics: calculate from fee and cost totals, not from summing individual records
    metrics["total_profit"] = calculate_profit_from_totals(metrics["total_fee"], metrics["total_cost"])

    # Calculate profit margin
    if metrics["total_fee"] > 0:
        metrics["profit_margin_percentage"] = (metrics["total_profit"] / metrics["total_fee"]) * 100
    else:
        metrics["profit_margin_percentage"] = 0
    
    # Fee-based calculations
    if metrics["unique_projects"] > 0:
        metrics["avg_fee_per_project"] = metrics["total_fee"] / metrics["unique_projects"]
    else:
        metrics["avg_fee_per_project"] = 0
        
    # Calculate billable hourly rate (average rate for billable hours only)
    if metrics["total_billable_hours"] > 0:
        metrics["Billable rate"] = metrics["total_fee"] / metrics["total_billable_hours"]
    else:
        metrics["Billable rate"] = 0
        
    # Calculate effective hourly rate (fee divided by all hours)
    if metrics["total_hours"] > 0:
        metrics["Effective rate"] = metrics["total_fee"] / metrics["total_hours"]
    else:
        metrics["Effective rate"] = 0
    
    return metrics


def aggregate_by_time(df: pd.DataFrame, time_period: str = 'day') -> pd.DataFrame:
    """
    Aggregate data by specified time period.
    
    Args:
        df: Validated and transformed dataframe
        time_period: Time period to aggregate by ('day', 'week', 'month', 'year')
        
    Returns:
        Aggregated dataframe
    """
    # Ensure Date column exists and is datetime type
    if "record_date" not in df.columns:
        raise ValueError("record_date column not found in dataframe")
    
    # Create date categories based on specified time period
    if time_period == 'day':
        date_groups = df["record_date"]
    elif time_period == 'week':
        date_groups = df["record_date"].dt.isocalendar().week
    elif time_period == 'month':
        date_groups = df["record_date"].dt.to_period('M')
    elif time_period == 'year':
        date_groups = df["record_date"].dt.year
    else:
        raise ValueError(f"Invalid time period: {time_period}")
    
    # Aggregate metrics by time period
    agg_df = df.groupby(date_groups).agg({
        "hours_used": "sum",
        "hours_billable": "sum"
    }).reset_index()
    
    # Add calculated columns
    agg_df["Non-billable hours"] = agg_df["hours_used"] - agg_df["hours_billable"]
    agg_df["Billability %"] = (agg_df["hours_billable"] / agg_df["hours_used"] * 100).round(2)
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_date = df.groupby(date_groups)["fee_record"].sum().reset_index(name="Fee")
        agg_df = pd.merge(agg_df, fee_by_date, on="record_date")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_date = df.groupby(date_groups).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        agg_df = pd.merge(agg_df, fee_by_date, on="record_date")
    else:
        agg_df["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_date = df.groupby(date_groups)["cost_record"].sum().reset_index(name="Total cost")
        agg_df = pd.merge(agg_df, cost_by_date, on="record_date")
    else:
        agg_df["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_date = df.groupby(date_groups)["profit_record"].sum().reset_index(name="Total profit")
        agg_df = pd.merge(agg_df, profit_by_date, on="record_date")
    else:
        agg_df["Total profit"] = 0
    
    # Calculate rates
    agg_df["Billable rate"] = 0  # Default
    mask = agg_df["hours_billable"] > 0
    agg_df.loc[mask, "Billable rate"] = agg_df.loc[mask, "Fee"] / agg_df.loc[mask, "hours_billable"]
    
    agg_df["Effective rate"] = 0  # Default
    mask = agg_df["hours_used"] > 0
    agg_df.loc[mask, "Effective rate"] = agg_df.loc[mask, "Fee"] / agg_df.loc[mask, "hours_used"]
    
    # Calculate profit margin
    agg_df["Profit margin %"] = 0.0
    mask = agg_df["Fee"] > 0
    agg_df.loc[mask, "Profit margin %"] = (agg_df.loc[mask, "Total profit"] / agg_df.loc[mask, "Fee"] * 100).round(2)
    
    return agg_df

def aggregate_by_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by year.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with yearly aggregations
    """
    # Ensure Date column exists and is datetime type
    if "record_date" not in df.columns:
        raise ValueError("record_date column not found in dataframe")
    
    # Extract year from the Date column
    year_df = df.copy()
    year_df['Year'] = year_df['record_date'].dt.year
    
    # Aggregate metrics by year
    year_agg = year_df.groupby("Year").agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "customer_number": "nunique",
        "person_name": "nunique"
    }).reset_index()
    
    # Add calculated columns
    year_agg["Non-billable hours"] = year_agg["hours_used"] - year_agg["hours_billable"]
    year_agg["Billability %"] = (year_agg["hours_billable"] / year_agg["hours_used"] * 100).round(2)
    year_agg.rename(columns={
        "project_number": "Number of projects",
        "customer_number": "Number of customers",
        "person_name": "Number of people"
    }, inplace=True)
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_year = year_df.groupby("Year")["fee_record"].sum().reset_index(name="Fee")
        year_agg = pd.merge(year_agg, fee_by_year, on="Year")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_year = year_df.groupby("Year").apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        year_agg = pd.merge(year_agg, fee_by_year, on="Year")
    else:
        year_agg["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_year = year_df.groupby("Year")["cost_record"].sum().reset_index(name="Total cost")
        year_agg = pd.merge(year_agg, cost_by_year, on="Year")
    else:
        year_agg["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_year = year_df.groupby("Year")["profit_record"].sum().reset_index(name="Total profit")
        year_agg = pd.merge(year_agg, profit_by_year, on="Year")
    else:
        year_agg["Total profit"] = 0
    
    # Calculate rates
    year_agg["Billable rate"] = 0  # Default
    mask = year_agg["hours_billable"] > 0
    year_agg.loc[mask, "Billable rate"] = year_agg.loc[mask, "Fee"] / year_agg.loc[mask, "hours_billable"]
    
    year_agg["Effective rate"] = 0  # Default
    mask = year_agg["hours_used"] > 0
    year_agg.loc[mask, "Effective rate"] = year_agg.loc[mask, "Fee"] / year_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    year_agg["Profit margin %"] = 0.0
    mask = year_agg["Fee"] > 0
    year_agg.loc[mask, "Profit margin %"] = (year_agg.loc[mask, "Total profit"] / year_agg.loc[mask, "Fee"] * 100).round(2)
    
    return year_agg


def aggregate_by_customer(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by customer.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with customer aggregations
    """
    customer_agg = df.groupby(["customer_number", "customer_name"], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique"
    }).reset_index()

    # Replace NaN customer_name values with "Unknown Customer" for display
    customer_agg["customer_name"] = customer_agg["customer_name"].fillna("Unknown Customer")

    customer_agg["Non-billable hours"] = customer_agg["hours_used"] - customer_agg["hours_billable"]
    customer_agg["Billability %"] = (customer_agg["hours_billable"] / customer_agg["hours_used"] * 100).round(2)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_customer = df.groupby("customer_number", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        customer_agg = pd.merge(customer_agg, fee_by_customer, on="customer_number")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_customer = df.groupby("customer_number", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        customer_agg = pd.merge(customer_agg, fee_by_customer, on="customer_number")
    else:
        customer_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_customer = df.groupby("customer_number", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        customer_agg = pd.merge(customer_agg, cost_by_customer, on="customer_number")
    else:
        customer_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_customer = df.groupby("customer_number", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        customer_agg = pd.merge(customer_agg, profit_by_customer, on="customer_number")
    else:
        customer_agg["Total profit"] = 0
    
    # Calculate rates
    customer_agg["Billable rate"] = 0  # Default
    mask = customer_agg["hours_billable"] > 0
    customer_agg.loc[mask, "Billable rate"] = customer_agg.loc[mask, "Fee"] / customer_agg.loc[mask, "hours_billable"]
    
    customer_agg["Effective rate"] = 0  # Default
    mask = customer_agg["hours_used"] > 0
    customer_agg.loc[mask, "Effective rate"] = customer_agg.loc[mask, "Fee"] / customer_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    customer_agg["Profit margin %"] = 0.0
    mask = customer_agg["Fee"] > 0
    customer_agg.loc[mask, "Profit margin %"] = (customer_agg.loc[mask, "Total profit"] / customer_agg.loc[mask, "Fee"] * 100).round(2)

    # Rename columns for display
    customer_agg.rename(columns={
        "project_number": "Number of projects",
        "customer_number": "Customer number",
        "customer_name": "Customer name"
    }, inplace=True)

    # Add percentage columns for sum metrics
    customer_agg = add_percentage_columns(customer_agg, SUM_METRICS)

    return customer_agg


def aggregate_by_customer_group(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by customer group.

    Args:
        df: Validated and transformed dataframe

    Returns:
        Dataframe with customer group aggregations
    """
    # Check if customer_group column exists
    if "customer_group" not in df.columns:
        # If customer_group doesn't exist, return empty dataframe with expected columns
        return pd.DataFrame()

    customer_group_agg = df.groupby("customer_group").agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique"
    }).reset_index()

    customer_group_agg["Non-billable hours"] = customer_group_agg["hours_used"] - customer_group_agg["hours_billable"]
    customer_group_agg["Billability %"] = (customer_group_agg["hours_billable"] / customer_group_agg["hours_used"] * 100).round(2)
    customer_group_agg.rename(columns={"project_number": "Number of projects"}, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_group = df.groupby("customer_group")["fee_record"].sum().reset_index(name="Fee")
        customer_group_agg = pd.merge(customer_group_agg, fee_by_group, on="customer_group")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_group = df.groupby("customer_group").apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        customer_group_agg = pd.merge(customer_group_agg, fee_by_group, on="customer_group")
    else:
        customer_group_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_group = df.groupby("customer_group")["cost_record"].sum().reset_index(name="Total cost")
        customer_group_agg = pd.merge(customer_group_agg, cost_by_group, on="customer_group")
    else:
        customer_group_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_group = df.groupby("customer_group")["profit_record"].sum().reset_index(name="Total profit")
        customer_group_agg = pd.merge(customer_group_agg, profit_by_group, on="customer_group")
    else:
        customer_group_agg["Total profit"] = 0

    # Calculate rates
    customer_group_agg["Billable rate"] = 0  # Default
    mask = customer_group_agg["hours_billable"] > 0
    customer_group_agg.loc[mask, "Billable rate"] = customer_group_agg.loc[mask, "Fee"] / customer_group_agg.loc[mask, "hours_billable"]

    customer_group_agg["Effective rate"] = 0  # Default
    mask = customer_group_agg["hours_used"] > 0
    customer_group_agg.loc[mask, "Effective rate"] = customer_group_agg.loc[mask, "Fee"] / customer_group_agg.loc[mask, "hours_used"]

    # Calculate profit margin
    customer_group_agg["Profit margin %"] = 0.0
    mask = customer_group_agg["Fee"] > 0
    customer_group_agg.loc[mask, "Profit margin %"] = (customer_group_agg.loc[mask, "Total profit"] / customer_group_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    customer_group_agg = add_percentage_columns(customer_group_agg, SUM_METRICS)

    return customer_group_agg


def aggregate_by_project(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by project.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with project aggregations
    """
    # Check if Project type column exists
    if "project_tag" in df.columns:
        # Use all three columns if Project type exists
        # dropna=False ensures records with NULL project_tag are included
        project_agg = df.groupby(["project_number", "project_name", "project_tag"], dropna=False).agg({
            "hours_used": "sum",
            "hours_billable": "sum",
            "person_name": "nunique"
        }).reset_index()
        # Replace NaN project_tag values with "Untagged" for display
        project_agg["project_tag"] = project_agg["project_tag"].fillna("Untagged")
    else:
        # Only use Project number and Project columns if Project type doesn't exist
        project_agg = df.groupby(["project_number", "project_name"], dropna=False).agg({
            "hours_used": "sum",
            "hours_billable": "sum",
            "person_name": "nunique"
        }).reset_index()
        # Add an empty Project type column to maintain expected schema
        project_agg["project_tag"] = "Unknown"
    
    project_agg["Non-billable hours"] = project_agg["hours_used"] - project_agg["hours_billable"]
    project_agg["Billability %"] = (project_agg["hours_billable"] / project_agg["hours_used"] * 100).round(2)
    project_agg.rename(columns={"person_name": "Number of people"}, inplace=True)
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_project = df.groupby("project_number", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        project_agg = pd.merge(project_agg, fee_by_project, on="project_number")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_project = df.groupby("project_number", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        project_agg = pd.merge(project_agg, fee_by_project, on="project_number")
    else:
        project_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_project = df.groupby("project_number", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        project_agg = pd.merge(project_agg, cost_by_project, on="project_number")
    else:
        project_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_project = df.groupby("project_number", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        project_agg = pd.merge(project_agg, profit_by_project, on="project_number")
    else:
        project_agg["Total profit"] = 0
    
    # Calculate rates
    project_agg["Billable rate"] = 0  # Default
    mask = project_agg["hours_billable"] > 0
    project_agg.loc[mask, "Billable rate"] = project_agg.loc[mask, "Fee"] / project_agg.loc[mask, "hours_billable"]
    
    project_agg["Effective rate"] = 0  # Default
    mask = project_agg["hours_used"] > 0
    project_agg.loc[mask, "Effective rate"] = project_agg.loc[mask, "Fee"] / project_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    project_agg["Profit margin %"] = 0.0
    mask = project_agg["Fee"] > 0
    project_agg.loc[mask, "Profit margin %"] = (project_agg.loc[mask, "Total profit"] / project_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    project_agg = add_percentage_columns(project_agg, SUM_METRICS)

    return project_agg


def aggregate_by_project_tag(df: pd.DataFrame, tag_column: str = "project_tag") -> pd.DataFrame:
    """
    Aggregate data by project tag dimension.

    Args:
        df: Validated and transformed dataframe
        tag_column: Name of tag column to group by (e.g., "project_tag", "project_tag_1", "project_tag_2")

    Returns:
        Dataframe with project tag aggregations
    """
    # Check if tag column exists
    if tag_column not in df.columns:
        return pd.DataFrame()

    project_tag_agg = df.groupby([tag_column], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "person_name": "nunique"
    }).reset_index()

    # Replace NaN tag values with "Untagged" for display
    project_tag_agg[tag_column] = project_tag_agg[tag_column].fillna("Untagged")

    project_tag_agg["Non-billable hours"] = project_tag_agg["hours_used"] - project_tag_agg["hours_billable"]
    project_tag_agg["Billability %"] = (project_tag_agg["hours_billable"] / project_tag_agg["hours_used"] * 100).round(2)
    project_tag_agg.rename(columns={
        "project_number": "Number of projects",
        "person_name": "Number of people"
    }, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_tag = df.groupby(tag_column, dropna=False)["fee_record"].sum().reset_index(name="Fee")
        project_tag_agg = pd.merge(project_tag_agg, fee_by_tag, on=tag_column)
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_tag = df.groupby(tag_column, dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        project_tag_agg = pd.merge(project_tag_agg, fee_by_tag, on=tag_column)
    else:
        project_tag_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_tag = df.groupby(tag_column, dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        project_tag_agg = pd.merge(project_tag_agg, cost_by_tag, on=tag_column)
    else:
        project_tag_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_tag = df.groupby(tag_column, dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        project_tag_agg = pd.merge(project_tag_agg, profit_by_tag, on=tag_column)
    else:
        project_tag_agg["Total profit"] = 0

    # Calculate rates
    project_tag_agg["Billable rate"] = 0  # Default
    mask = project_tag_agg["hours_billable"] > 0
    project_tag_agg.loc[mask, "Billable rate"] = project_tag_agg.loc[mask, "Fee"] / project_tag_agg.loc[mask, "hours_billable"]

    project_tag_agg["Effective rate"] = 0  # Default
    mask = project_tag_agg["hours_used"] > 0
    project_tag_agg.loc[mask, "Effective rate"] = project_tag_agg.loc[mask, "Fee"] / project_tag_agg.loc[mask, "hours_used"]

    # Calculate profit margin
    project_tag_agg["Profit margin %"] = 0.0
    mask = project_tag_agg["Fee"] > 0
    project_tag_agg.loc[mask, "Profit margin %"] = (project_tag_agg.loc[mask, "Total profit"] / project_tag_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    project_tag_agg = add_percentage_columns(project_tag_agg, SUM_METRICS)

    return project_tag_agg


def aggregate_by_project_type(df: pd.DataFrame) -> pd.DataFrame:
    """
    Deprecated: Use aggregate_by_project_tag() instead.
    This function is kept for backward compatibility.
    """
    return aggregate_by_project_tag(df, tag_column="project_tag")


def aggregate_by_phase(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by project phase.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with phase aggregations
    """
    phase_agg = df.groupby(["phase_tag"], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "person_name": "nunique"
    }).reset_index()

    # Replace NaN phase_tag values with "No Phase" for display
    phase_agg["phase_tag"] = phase_agg["phase_tag"].fillna("No Phase")

    phase_agg["Non-billable hours"] = phase_agg["hours_used"] - phase_agg["hours_billable"]
    phase_agg["Billability %"] = (phase_agg["hours_billable"] / phase_agg["hours_used"] * 100).round(2)
    phase_agg.rename(columns={
        "project_number": "Number of projects",
        "person_name": "Number of people"
    }, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_phase = df.groupby("phase_tag", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        phase_agg = pd.merge(phase_agg, fee_by_phase, on="phase_tag")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_phase = df.groupby("phase_tag", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        phase_agg = pd.merge(phase_agg, fee_by_phase, on="phase_tag")
    else:
        phase_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_phase = df.groupby("phase_tag", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        phase_agg = pd.merge(phase_agg, cost_by_phase, on="phase_tag")
    else:
        phase_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_phase = df.groupby("phase_tag", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        phase_agg = pd.merge(phase_agg, profit_by_phase, on="phase_tag")
    else:
        phase_agg["Total profit"] = 0
    
    # Calculate rates
    phase_agg["Billable rate"] = 0  # Default
    mask = phase_agg["hours_billable"] > 0
    phase_agg.loc[mask, "Billable rate"] = phase_agg.loc[mask, "Fee"] / phase_agg.loc[mask, "hours_billable"]
    
    phase_agg["Effective rate"] = 0  # Default
    mask = phase_agg["hours_used"] > 0
    phase_agg.loc[mask, "Effective rate"] = phase_agg.loc[mask, "Fee"] / phase_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    phase_agg["Profit margin %"] = 0.0
    mask = phase_agg["Fee"] > 0
    phase_agg.loc[mask, "Profit margin %"] = (phase_agg.loc[mask, "Total profit"] / phase_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    phase_agg = add_percentage_columns(phase_agg, SUM_METRICS)

    return phase_agg

def aggregate_by_price_model(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by price model.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with price model aggregations
    """
    price_model_agg = df.groupby(["price_model_type"], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "person_name": "nunique"
    }).reset_index()

    # Replace NaN price_model_type values with "No Price Model" for display
    price_model_agg["price_model_type"] = price_model_agg["price_model_type"].fillna("No Price Model")

    price_model_agg["Non-billable hours"] = price_model_agg["hours_used"] - price_model_agg["hours_billable"]
    price_model_agg["Billability %"] = (price_model_agg["hours_billable"] / price_model_agg["hours_used"] * 100).round(2)
    price_model_agg.rename(columns={
        "project_number": "Number of projects",
        "person_name": "Number of people"
    }, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_price_model = df.groupby("price_model_type", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        price_model_agg = pd.merge(price_model_agg, fee_by_price_model, on="price_model_type")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_price_model = df.groupby("price_model_type", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        price_model_agg = pd.merge(price_model_agg, fee_by_price_model, on="price_model_type")
    else:
        price_model_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_price_model = df.groupby("price_model_type", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        price_model_agg = pd.merge(price_model_agg, cost_by_price_model, on="price_model_type")
    else:
        price_model_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_price_model = df.groupby("price_model_type", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        price_model_agg = pd.merge(price_model_agg, profit_by_price_model, on="price_model_type")
    else:
        price_model_agg["Total profit"] = 0
    
    # Calculate rates
    price_model_agg["Billable rate"] = 0  # Default
    mask = price_model_agg["hours_billable"] > 0
    price_model_agg.loc[mask, "Billable rate"] = price_model_agg.loc[mask, "Fee"] / price_model_agg.loc[mask, "hours_billable"]
    
    price_model_agg["Effective rate"] = 0  # Default
    mask = price_model_agg["hours_used"] > 0
    price_model_agg.loc[mask, "Effective rate"] = price_model_agg.loc[mask, "Fee"] / price_model_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    price_model_agg["Profit margin %"] = 0.0
    mask = price_model_agg["Fee"] > 0
    price_model_agg.loc[mask, "Profit margin %"] = (price_model_agg.loc[mask, "Total profit"] / price_model_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    price_model_agg = add_percentage_columns(price_model_agg, SUM_METRICS)

    return price_model_agg


def aggregate_by_activity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by activity.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with activity aggregations
    """
    activity_agg = df.groupby(["activity_tag"], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "person_name": "nunique"
    }).reset_index()

    # Replace NaN activity_tag values with "No Activity" for display
    activity_agg["activity_tag"] = activity_agg["activity_tag"].fillna("No Activity")

    activity_agg["Non-billable hours"] = activity_agg["hours_used"] - activity_agg["hours_billable"]
    activity_agg["Billability %"] = (activity_agg["hours_billable"] / activity_agg["hours_used"] * 100).round(2)
    activity_agg.rename(columns={
        "project_number": "Number of projects",
        "person_name": "Number of people"
    }, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_activity = df.groupby("activity_tag", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        activity_agg = pd.merge(activity_agg, fee_by_activity, on="activity_tag")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_activity = df.groupby("activity_tag", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        activity_agg = pd.merge(activity_agg, fee_by_activity, on="activity_tag")
    else:
        activity_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_activity = df.groupby("activity_tag", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        activity_agg = pd.merge(activity_agg, cost_by_activity, on="activity_tag")
    else:
        activity_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_activity = df.groupby("activity_tag", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        activity_agg = pd.merge(activity_agg, profit_by_activity, on="activity_tag")
    else:
        activity_agg["Total profit"] = 0
    
    # Calculate rates
    activity_agg["Billable rate"] = 0  # Default
    mask = activity_agg["hours_billable"] > 0
    activity_agg.loc[mask, "Billable rate"] = activity_agg.loc[mask, "Fee"] / activity_agg.loc[mask, "hours_billable"]
    
    activity_agg["Effective rate"] = 0  # Default
    mask = activity_agg["hours_used"] > 0
    activity_agg.loc[mask, "Effective rate"] = activity_agg.loc[mask, "Fee"] / activity_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    activity_agg["Profit margin %"] = 0.0
    mask = activity_agg["Fee"] > 0
    activity_agg.loc[mask, "Profit margin %"] = (activity_agg.loc[mask, "Total profit"] / activity_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    activity_agg = add_percentage_columns(activity_agg, SUM_METRICS)

    return activity_agg


def aggregate_by_person(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by person.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with person aggregations
    """
    person_agg = df.groupby(["person_name"], dropna=False).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique"
    }).reset_index()

    # Replace NaN person_name values with "Unknown Person" for display
    person_agg["person_name"] = person_agg["person_name"].fillna("Unknown Person")

    person_agg["Non-billable hours"] = person_agg["hours_used"] - person_agg["hours_billable"]
    person_agg["Billability %"] = (person_agg["hours_billable"] / person_agg["hours_used"] * 100).round(2)
    person_agg.rename(columns={"project_number": "Number of projects"}, inplace=True)

    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_person = df.groupby("person_name", dropna=False)["fee_record"].sum().reset_index(name="Fee")
        person_agg = pd.merge(person_agg, fee_by_person, on="person_name")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_person = df.groupby("person_name", dropna=False).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        person_agg = pd.merge(person_agg, fee_by_person, on="person_name")
    else:
        person_agg["Fee"] = 0

    # Add cost
    if "cost_record" in df.columns:
        cost_by_person = df.groupby("person_name", dropna=False)["cost_record"].sum().reset_index(name="Total cost")
        person_agg = pd.merge(person_agg, cost_by_person, on="person_name")
    else:
        person_agg["Total cost"] = 0

    # Add profit
    if "profit_record" in df.columns:
        profit_by_person = df.groupby("person_name", dropna=False)["profit_record"].sum().reset_index(name="Total profit")
        person_agg = pd.merge(person_agg, profit_by_person, on="person_name")
    else:
        person_agg["Total profit"] = 0
    
    # Calculate rates
    person_agg["Billable rate"] = 0  # Default
    mask = person_agg["hours_billable"] > 0
    person_agg.loc[mask, "Billable rate"] = person_agg.loc[mask, "Fee"] / person_agg.loc[mask, "hours_billable"]
    
    person_agg["Effective rate"] = 0  # Default
    mask = person_agg["hours_used"] > 0
    person_agg.loc[mask, "Effective rate"] = person_agg.loc[mask, "Fee"] / person_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    person_agg["Profit margin %"] = 0.0
    mask = person_agg["Fee"] > 0
    person_agg.loc[mask, "Profit margin %"] = (person_agg.loc[mask, "Total profit"] / person_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    person_agg = add_percentage_columns(person_agg, SUM_METRICS)

    return person_agg


def find_top_items(df: pd.DataFrame, category: str, metric: str, top_n: int = 5) -> pd.DataFrame:
    """
    Find top items by a specific metric.
    
    Args:
        df: Validated and transformed dataframe
        category: Category to group by ('customer', 'project', 'person')
        metric: Metric to sort by ('hours', 'billable', 'fee', 'cost', 'profit')
        top_n: Number of top items to return
        
    Returns:
        Dataframe with top items
    """
    if category == 'customer':
        group_cols = ["customer_number", "customer_name"]
    elif category == 'project':
        group_cols = ["project_number", "project_name"]
    elif category == 'person':
        group_cols = ["person_name"]
    else:
        raise ValueError(f"Invalid category: {category}")
    
    # Calculate metrics for each group
    result = df.groupby(group_cols).agg({
        "hours_used": "sum",
        "hours_billable": "sum"
    }).reset_index()
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_group = df.groupby(group_cols[0])["fee_record"].sum().reset_index(name="Fee")
        result = pd.merge(result, fee_by_group, on=group_cols[0])
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_group = df.groupby(group_cols[0]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        result = pd.merge(result, fee_by_group, on=group_cols[0])
    else:
        result["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_group = df.groupby(group_cols[0])["cost_record"].sum().reset_index(name="Total cost")
        result = pd.merge(result, cost_by_group, on=group_cols[0])
    else:
        result["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_group = df.groupby(group_cols[0])["profit_record"].sum().reset_index(name="Total profit")
        result = pd.merge(result, profit_by_group, on=group_cols[0])
    else:
        result["Total profit"] = 0
    
    # Calculate rates
    result["Billable rate"] = 0  # Default
    mask = result["hours_billable"] > 0
    result.loc[mask, "Billable rate"] = result.loc[mask, "Fee"] / result.loc[mask, "hours_billable"]
    
    result["Effective rate"] = 0  # Default
    mask = result["hours_used"] > 0
    result.loc[mask, "Effective rate"] = result.loc[mask, "Fee"] / result.loc[mask, "hours_used"]
    
    # Determine sort column
    if metric == 'hours':
        sort_col = "hours_used"
    elif metric == 'billable':
        sort_col = "hours_billable"
    elif metric == 'fee':
        sort_col = "Fee"
    elif metric == 'cost':
        sort_col = "Total cost"
    elif metric == 'profit':
        sort_col = "Total profit"
    else:
        sort_col = "hours_used"  # Default
    
    return result.sort_values(sort_col, ascending=False).head(top_n)


def calculate_utilization_rates(df: pd.DataFrame, work_hours_per_day: float = 8.0) -> pd.DataFrame:
    """
    Calculate utilization rates for each person.
    
    Args:
        df: Validated and transformed dataframe
        work_hours_per_day: Standard work hours per day
        
    Returns:
        Dataframe with utilization rates
    """
    # Group by person and date to get hours per person per day
    person_daily = df.groupby(["person_name", "record_date"])["hours_used"].sum().reset_index()
    
    # Calculate days worked per person
    days_worked = person_daily.groupby("person_name")["record_date"].nunique()
    
    # Calculate total possible work hours (days worked * work hours per day)
    total_possible_hours = days_worked * work_hours_per_day
    
    # Calculate actual hours worked per person
    hours_worked = df.groupby("person_name")["hours_used"].sum()
    
    # Calculate billable hours per person
    billable_hours = df.groupby("person_name")["hours_billable"].sum()
    
    # Combine into a single dataframe
    util_df = pd.DataFrame({
        "Days worked": days_worked,
        "Potential hours": total_possible_hours,
        "Actual hours": hours_worked,
        "hours_billable": billable_hours
    }).reset_index()
    
    # Calculate utilization rates
    util_df["Utilization %"] = (util_df["Actual hours"] / util_df["Potential hours"] * 100).round(2)
    util_df["Billable utilization %"] = (util_df["hours_billable"] / util_df["Potential hours"] * 100).round(2)
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_person = df.groupby("person_name")["fee_record"].sum().reset_index(name="Fee")
        util_df = pd.merge(util_df, fee_by_person, on="person_name")
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_person = df.groupby("person_name").apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        util_df = pd.merge(util_df, fee_by_person, on="person_name")
    else:
        util_df["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_person = df.groupby("person_name")["cost_record"].sum().reset_index(name="Total cost")
        util_df = pd.merge(util_df, cost_by_person, on="person_name")
    else:
        util_df["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_person = df.groupby("person_name")["profit_record"].sum().reset_index(name="Total profit")
        util_df = pd.merge(util_df, profit_by_person, on="person_name")
    else:
        util_df["Total profit"] = 0
    
    # Calculate rates
    util_df["Billable rate"] = 0  # Default
    mask = util_df["hours_billable"] > 0
    util_df.loc[mask, "Billable rate"] = util_df.loc[mask, "Fee"] / util_df.loc[mask, "hours_billable"]
    
    util_df["Effective rate"] = 0  # Default
    mask = util_df["Actual hours"] > 0
    util_df.loc[mask, "Effective rate"] = util_df.loc[mask, "Fee"] / util_df.loc[mask, "Actual hours"]
    
    return util_df

def aggregate_by_month_year(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by month and year.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with month-year aggregations
    """
    # Ensure Date column exists and is datetime type
    if "record_date" not in df.columns:
        raise ValueError("record_date column not found in dataframe")
    
    # Create month and year columns
    month_year_df = df.copy()
    month_year_df['Year'] = month_year_df['record_date'].dt.year
    month_year_df['Month'] = month_year_df['record_date'].dt.month
    
    # Create month name for better display
    month_names = {
        1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
        7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
    }
    month_year_df['Month name'] = month_year_df['Month'].map(month_names)
    
    # Aggregate metrics by month and year
    month_year_agg = month_year_df.groupby(['Year', 'Month', 'Month name']).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "project_number": "nunique",
        "customer_number": "nunique",
        "person_name": "nunique"
    }).reset_index()
    
    # Add calculated columns
    month_year_agg["Non-billable hours"] = month_year_agg["hours_used"] - month_year_agg["hours_billable"]
    month_year_agg["Billability %"] = (month_year_agg["hours_billable"] / month_year_agg["hours_used"] * 100).round(2)
    month_year_agg.rename(columns={
        "project_number": "Number of projects",
        "customer_number": "Number of customers",
        "person_name": "Number of people"
    }, inplace=True)
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_month_year = month_year_df.groupby(['Year', 'Month'])["fee_record"].sum().reset_index(name="Fee")
        month_year_agg = pd.merge(month_year_agg, fee_by_month_year, on=['Year', 'Month'])
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_month_year = month_year_df.groupby(['Year', 'Month']).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        month_year_agg = pd.merge(month_year_agg, fee_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_month_year = month_year_df.groupby(['Year', 'Month'])["cost_record"].sum().reset_index(name="Total cost")
        month_year_agg = pd.merge(month_year_agg, cost_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_month_year = month_year_df.groupby(['Year', 'Month'])["profit_record"].sum().reset_index(name="Total profit")
        month_year_agg = pd.merge(month_year_agg, profit_by_month_year, on=['Year', 'Month'])
    else:
        month_year_agg["Total profit"] = 0
    
    # Calculate rates
    month_year_agg["Billable rate"] = 0  # Default
    mask = month_year_agg["hours_billable"] > 0
    month_year_agg.loc[mask, "Billable rate"] = month_year_agg.loc[mask, "Fee"] / month_year_agg.loc[mask, "hours_billable"]
    
    month_year_agg["Effective rate"] = 0  # Default
    mask = month_year_agg["hours_used"] > 0
    month_year_agg.loc[mask, "Effective rate"] = month_year_agg.loc[mask, "Fee"] / month_year_agg.loc[mask, "hours_used"]
    
    # Calculate profit margin
    month_year_agg["Profit margin %"] = 0.0
    mask = month_year_agg["Fee"] > 0
    month_year_agg.loc[mask, "Profit margin %"] = (month_year_agg.loc[mask, "Total profit"] / month_year_agg.loc[mask, "Fee"] * 100).round(2)

    # Add percentage columns for sum metrics
    month_year_agg = add_percentage_columns(month_year_agg, SUM_METRICS)

    return month_year_agg

def aggregate_customer_project_hierarchy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data by customer and project to create a hierarchical structure
    for treemap visualization.
    
    Args:
        df: Validated and transformed dataframe
        
    Returns:
        Dataframe with hierarchical customer-project aggregations
    """
    # Create a copy of the dataframe to avoid modifying the original
    hierarchy_df = df.copy()
    
    # First, get customer-level aggregations
    customer_agg = aggregate_by_customer(df)
    customer_agg['Level'] = 'Customer'  # Add level identifier
    
    # Next, get project-level aggregations with customer information
    project_with_customer = df.groupby([
        "customer_number", "customer_name", "project_number", "project_name"
    ]).agg({
        "hours_used": "sum",
        "hours_billable": "sum",
        "person_name": "nunique"
    }).reset_index()
    
    # Add calculated metrics for projects
    project_with_customer["Non-billable hours"] = (
        project_with_customer["hours_used"] - project_with_customer["hours_billable"]
    )
    project_with_customer["Billability %"] = (
        project_with_customer["hours_billable"] / project_with_customer["hours_used"] * 100
    ).round(2)
    project_with_customer.rename(columns={"person_name": "Number of people"}, inplace=True)
    project_with_customer['Level'] = 'project_name'  # Add level identifier
    
    # Add fee (new approach with fallback)
    if "fee_record" in df.columns:
        fee_by_project = df.groupby(["customer_number", "project_number"])["fee_record"].sum().reset_index(name="Fee")
        project_with_customer = pd.merge(
            project_with_customer, 
            fee_by_project, 
            on=["customer_number", "project_number"]
        )
    elif "billable_rate_record" in df.columns:
        # Fallback to old calculation
        fee_by_project = df.groupby(["customer_number", "project_number"]).apply(
            lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
        ).reset_index(name="Fee")
        project_with_customer = pd.merge(
            project_with_customer, 
            fee_by_project, 
            on=["customer_number", "project_number"]
        )
    else:
        project_with_customer["Fee"] = 0
    
    # Add cost
    if "cost_record" in df.columns:
        cost_by_project = df.groupby(["customer_number", "project_number"])["cost_record"].sum().reset_index(name="Total cost")
        project_with_customer = pd.merge(
            project_with_customer, 
            cost_by_project, 
            on=["customer_number", "project_number"]
        )
    else:
        project_with_customer["Total cost"] = 0
    
    # Add profit
    if "profit_record" in df.columns:
        profit_by_project = df.groupby(["customer_number", "project_number"])["profit_record"].sum().reset_index(name="Total profit")
        project_with_customer = pd.merge(
            project_with_customer, 
            profit_by_project, 
            on=["customer_number", "project_number"]
        )
    else:
        project_with_customer["Total profit"] = 0
    
    # Calculate rates for projects
    project_with_customer["Billable rate"] = 0  # Default
    mask = project_with_customer["hours_billable"] > 0
    project_with_customer.loc[mask, "Billable rate"] = (
        project_with_customer.loc[mask, "Fee"] / 
        project_with_customer.loc[mask, "hours_billable"]
    )
    
    project_with_customer["Effective rate"] = 0  # Default
    mask = project_with_customer["hours_used"] > 0
    project_with_customer.loc[mask, "Effective rate"] = (
        project_with_customer.loc[mask, "Fee"] / 
        project_with_customer.loc[mask, "hours_used"]
    )
    
    # Calculate profit margin for projects
    project_with_customer["Profit margin %"] = 0.0
    mask = project_with_customer["Fee"] > 0
    project_with_customer.loc[mask, "Profit margin %"] = (
        project_with_customer.loc[mask, "Total profit"] / 
        project_with_customer.loc[mask, "Fee"] * 100
    ).round(2)
    
    # Add a column to store parent ID for hierarchical relationships
    customer_agg["id"] = customer_agg["customer_number"]
    customer_agg["parent"] = None  # Customers are top level
    
    # For projects, parent is the customer
    project_with_customer["id"] = project_with_customer["customer_number"].astype(str) + "-" + project_with_customer["project_number"].astype(str)
    project_with_customer["parent"] = project_with_customer["customer_number"]
    
    # Select the same columns for both dataframes for consistent merging
    common_columns = [
        'id', 'parent', 'Level', 'Customer number', 'Customer name',
        'hours_used', 'hours_billable', 'Non-billable hours', 'Billability %',
        'Fee', 'Total cost', 'Total profit', 'Profit margin %',
        'Billable rate', 'Effective rate'
    ]
    
    # Add project-specific columns to project dataframe
    project_columns = common_columns + ['project_number', 'project_name', 'Number of people']
    
    # For customer dataframe, add placeholder columns for project-specific data
    customer_agg['project_number'] = None
    customer_agg['project_name'] = None
    customer_agg['Number of people'] = customer_agg['Number of projects']  # Use project count instead
    
    # Select final columns for both dataframes
    customer_df = customer_agg[project_columns].copy()
    project_df = project_with_customer[project_columns].copy()
    
    # Combine the two dataframes
    hierarchy_df = pd.concat([customer_df, project_df], ignore_index=True)
    
    return hierarchy_df

def aggregate_project_by_month_year(df: pd.DataFrame, project_numbers: list = None, planned_df: pd.DataFrame = None, filter_settings: dict = None) -> pd.DataFrame:
    """
    Aggregate data by month and year for specific projects, including planned hours if available.
    
    Args:
        df: Validated and transformed dataframe
        project_numbers: List of project numbers to include (None means all projects)
        planned_df: Optional planned hours dataframe (already filtered by Person type)
        filter_settings: Dictionary with filter settings, including date_filter_type
        
    Returns:
        Dataframe with month-year aggregations for specified projects
    """
    # Ensure Date column exists and is datetime type
    if "record_date" not in df.columns and (planned_df is None or "record_date" not in planned_df.columns):
        raise ValueError("record_date column not found in dataframe")
    
    # Filter by project if project_numbers provided
    filtered_df = df.copy()
    if project_numbers is not None and len(project_numbers) > 0:
        filtered_df = filtered_df[filtered_df['project_number'].isin(project_numbers)]
    
    # Handle case where filtered_df is empty but we have planned data
    if filtered_df.empty and (planned_df is None or planned_df.empty):
        return pd.DataFrame()
    
    # Initialize month_year_agg
    month_year_agg = pd.DataFrame()
    
    # Process actual data if not empty
    if not filtered_df.empty:
        # Create month and year columns
        filtered_df['Year'] = filtered_df['record_date'].dt.year
        filtered_df['Month'] = filtered_df['record_date'].dt.month
        
        # Create month name for better display
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        filtered_df['Month name'] = filtered_df['Month'].map(month_names)
        
        # Create date string for sorting (YYYY-MM)
        filtered_df['Date string'] = filtered_df['Year'].astype(str) + '-' + filtered_df['Month'].astype(str).str.zfill(2)
        
        # Aggregate metrics by month and year
        month_year_agg = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string']).agg({
            "hours_used": "sum",
            "hours_billable": "sum",
            "person_name": "nunique"
        }).reset_index()
        
        # Add calculated columns
        month_year_agg["Non-billable hours"] = month_year_agg["hours_used"] - month_year_agg["hours_billable"]
        month_year_agg["Billability %"] = (month_year_agg["hours_billable"] / month_year_agg["hours_used"] * 100).round(2)
        month_year_agg.rename(columns={"person_name": "Number of people"}, inplace=True)
    
    # Handle planned hours data if provided
    if planned_df is not None and not planned_df.empty:
        # Create month name mapping
        month_names = {
            1: 'Jan', 2: 'Feb', 3: 'Mar', 4: 'Apr', 5: 'May', 6: 'Jun',
            7: 'Jul', 8: 'Aug', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dec'
        }
        
        # Create month and year columns in planned data
        planned_df_agg = planned_df.copy()
        
        # Note: planned_df is already filtered by all criteria (including dates) at the dashboard layer
        # No need to re-apply filtering here - use the pre-filtered data directly
        
        planned_df_agg['Year'] = planned_df_agg['record_date'].dt.year
        planned_df_agg['Month'] = planned_df_agg['record_date'].dt.month
        
        # Filter by project if project_numbers provided
        if project_numbers is not None and len(project_numbers) > 0:
            planned_df_agg = planned_df_agg[planned_df_agg['project_number'].isin(project_numbers)]
        
        # Create month name for planned data too
        planned_df_agg['Month name'] = planned_df_agg['Month'].map(month_names)
        planned_df_agg['Date string'] = planned_df_agg['Year'].astype(str) + '-' + planned_df_agg['Month'].astype(str).str.zfill(2)
        
        # Create base aggregation for planned hours
        planned_agg_dict = {"planned_hours": "sum"}
        
        # Check if Planned rate exists and add to aggregation
        has_planned_rate = "planned_hourly_rate" in planned_df_agg.columns
        
        # Aggregate planned hours by month and year
        if not has_planned_rate:
            planned_month_year = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).agg(
                planned_agg_dict
            ).reset_index()
        else:
            # First aggregate just the hours
            planned_month_year = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).agg(
                planned_agg_dict
            ).reset_index()
            
            # Then calculate weighted average of planned rate by month/year
            planned_rate_by_month = planned_df_agg.groupby(['Year', 'Month', 'Month name', 'Date string']).apply(
                lambda x: (x["planned_hourly_rate"] * x["planned_hours"]).sum() / x["planned_hours"].sum() 
                if x["planned_hours"].sum() > 0 else 0
            ).reset_index()
            planned_rate_by_month.columns = ['Year', 'Month', 'Month name', 'Date string', 'planned_hourly_rate']
            
            # Merge planned rate into the planned hours dataframe
            planned_month_year = pd.merge(
                planned_month_year,
                planned_rate_by_month,
                on=['Year', 'Month', 'Month name', 'Date string']
            )
        
        # Calculate planned fee (planned hours * planned rate)
        if "planned_hourly_rate" in planned_month_year.columns:
            planned_month_year["planned_fee"] = planned_month_year["planned_hours"] * planned_month_year["planned_hourly_rate"]
        
        # Merge planned hours with actual hours
        if month_year_agg.empty:
            # No actual data, use planned data as base
            month_year_agg = planned_month_year.copy()
            # Add missing actual data columns with zeros
            month_year_agg["hours_used"] = 0
            month_year_agg["hours_billable"] = 0
            month_year_agg["Number of people"] = 0
            month_year_agg["Non-billable hours"] = 0
            month_year_agg["Billability %"] = 0
        else:
            # Merge planned with actual
            month_year_agg = pd.merge(
                month_year_agg,
                planned_month_year,
                on=['Year', 'Month', 'Month name', 'Date string'],
                how='outer'
            )
            
            # Fill missing values with 0
            month_year_agg["hours_used"] = month_year_agg["hours_used"].fillna(0)
            month_year_agg["hours_billable"] = month_year_agg["hours_billable"].fillna(0)
            month_year_agg["Number of people"] = month_year_agg["Number of people"].fillna(0)
            month_year_agg["Non-billable hours"] = month_year_agg["Non-billable hours"].fillna(0)
            month_year_agg["Billability %"] = month_year_agg["Billability %"].fillna(0)
            month_year_agg["planned_hours"] = month_year_agg["planned_hours"].fillna(0)
        
        # Calculate hours variance metrics
        if "planned_hours" in month_year_agg.columns:
            month_year_agg["Hours variance"] = month_year_agg["hours_used"] - month_year_agg["planned_hours"]
            
            # Calculate hours variance percentage (avoid division by zero)
            month_year_agg["Variance percentage"] = 0.0
            mask = month_year_agg["planned_hours"] > 0
            month_year_agg.loc[mask, "Variance percentage"] = (
                month_year_agg.loc[mask, "Hours variance"] / month_year_agg.loc[mask, "planned_hours"] * 100
            ).round(2)
        
        # Handle rate calculations if planned rate exists
        if has_planned_rate and "planned_hourly_rate" in month_year_agg.columns:
            month_year_agg["planned_hourly_rate"] = month_year_agg["planned_hourly_rate"].fillna(0)
            
            # Calculate effective rate from billable hours/fee if we have actual data
            if not filtered_df.empty:
                # Add fee calculations using new approach
                if "fee_record" in filtered_df.columns:
                    fee_by_month = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string'])["fee_record"].sum().reset_index(name="Fee")
                elif "billable_rate_record" in filtered_df.columns:
                    # Fallback calculation
                    fee_by_month = filtered_df.groupby(['Year', 'Month', 'Month name', 'Date string']).apply(
                        lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
                    ).reset_index()
                    fee_by_month.columns = ['Year', 'Month', 'Month name', 'Date string', 'Fee']
                else:
                    fee_by_month = pd.DataFrame(columns=['Year', 'Month', 'Month name', 'Date string', 'Fee'])
                
                # Merge fee into aggregated dataframe
                month_year_agg = pd.merge(
                    month_year_agg,
                    fee_by_month,
                    on=['Year', 'Month', 'Month name', 'Date string'],
                    how='left'
                )
                
                # Fill missing values
                month_year_agg["Fee"] = month_year_agg["Fee"].fillna(0)
                
                # Calculate effective rate (fee / billable hours)
                month_year_agg["Effective rate"] = 0.0
                mask = month_year_agg["hours_billable"] > 0
                month_year_agg.loc[mask, "Effective rate"] = (
                    month_year_agg.loc[mask, "Fee"] / month_year_agg.loc[mask, "hours_billable"]
                ).round(2)
                
                # Calculate rate variance metrics
                month_year_agg["Rate variance"] = month_year_agg["Effective rate"] - month_year_agg["planned_hourly_rate"]
                
                # Calculate rate variance percentage (avoid division by zero)
                month_year_agg["Rate variance percentage"] = 0.0
                mask = month_year_agg["planned_hourly_rate"] > 0
                month_year_agg.loc[mask, "Rate variance percentage"] = (
                    month_year_agg.loc[mask, "Rate variance"] / month_year_agg.loc[mask, "planned_hourly_rate"] * 100
                ).round(2)
                
                # Calculate fee variance if planned fee exists
                if "planned_fee" in month_year_agg.columns:
                    # Calculate fee variance metrics
                    month_year_agg["Fee variance"] = month_year_agg["Fee"] - month_year_agg["planned_fee"]
                    
                    # Calculate fee variance percentage (avoid division by zero)
                    month_year_agg["Fee variance percentage"] = 0.0
                    mask = month_year_agg["planned_fee"] > 0
                    month_year_agg.loc[mask, "Fee variance percentage"] = (
                        month_year_agg.loc[mask, "Fee variance"] / month_year_agg.loc[mask, "planned_fee"] * 100
                    ).round(2)
            else:
                # No actual data or hourly rate, set default values
                month_year_agg["Fee"] = 0
                month_year_agg["Effective rate"] = 0
                month_year_agg["Rate variance"] = 0 - month_year_agg["planned_hourly_rate"]
                month_year_agg["Rate variance percentage"] = -100.0  # 100% below planned
                
                if "planned_fee" in month_year_agg.columns:
                    month_year_agg["Fee variance"] = 0 - month_year_agg["planned_fee"]
                    month_year_agg["Fee variance percentage"] = -100.0  # 100% below planned
    
    # Add fee and hourly rates if not already added
    if not filtered_df.empty and "Fee" not in month_year_agg.columns:
        # Add fee (new approach with fallback)
        if "fee_record" in df.columns:
            fee_by_month_year = filtered_df.groupby(['Year', 'Month'])["fee_record"].sum().reset_index(name="Fee")
        elif "billable_rate_record" in df.columns:
            # Fallback to old calculation
            fee_by_month_year = filtered_df.groupby(['Year', 'Month']).apply(
                lambda x: (x["hours_billable"] * x["billable_rate_record"]).sum()
            ).reset_index()
            fee_by_month_year.columns = ['Year', 'Month', 'Fee']
        else:
            fee_by_month_year = pd.DataFrame(columns=['Year', 'Month', 'Fee'])
        
        # Merge fee into the aggregated dataframe
        month_year_agg = pd.merge(month_year_agg, fee_by_month_year, on=['Year', 'Month'], how='left')
        month_year_agg["Fee"] = month_year_agg["Fee"].fillna(0)
        
        # Calculate billable hourly rate (fee / billable hours)
        month_year_agg["Billable rate"] = 0  # Default
        mask = month_year_agg["hours_billable"] > 0
        month_year_agg.loc[mask, "Billable rate"] = month_year_agg.loc[mask, "Fee"] / month_year_agg.loc[mask, "hours_billable"]
        
        # Calculate effective hourly rate (fee / total hours)
        month_year_agg["Effective rate"] = 0  # Default
        mask = month_year_agg["hours_used"] > 0
        month_year_agg.loc[mask, "Effective rate"] = month_year_agg.loc[mask, "Fee"] / month_year_agg.loc[mask, "hours_used"]
    else:
        # Make sure these columns exist if not already added
        if "Fee" not in month_year_agg.columns:
            month_year_agg["Fee"] = 0
        if "Billable rate" not in month_year_agg.columns:
            month_year_agg["Billable rate"] = 0
        if "Effective rate" not in month_year_agg.columns:
            month_year_agg["Effective rate"] = 0
    
    # Add cost and profit calculations if not already added
    if not filtered_df.empty:
        # Add cost if not already present
        if "Total cost" not in month_year_agg.columns:
            if "cost_record" in filtered_df.columns:
                cost_by_month_year = filtered_df.groupby(['Year', 'Month'])["cost_record"].sum().reset_index(name="Total cost")
                month_year_agg = pd.merge(month_year_agg, cost_by_month_year, on=['Year', 'Month'], how='left')
                month_year_agg["Total cost"] = month_year_agg["Total cost"].fillna(0)
            else:
                month_year_agg["Total cost"] = 0
        
        # Add profit if not already present
        if "Total profit" not in month_year_agg.columns:
            if "profit_record" in filtered_df.columns:
                profit_by_month_year = filtered_df.groupby(['Year', 'Month'])["profit_record"].sum().reset_index(name="Total profit")
                month_year_agg = pd.merge(month_year_agg, profit_by_month_year, on=['Year', 'Month'], how='left')
                month_year_agg["Total profit"] = month_year_agg["Total profit"].fillna(0)
            else:
                month_year_agg["Total profit"] = 0
        
        # Calculate profit margin if not already present
        if "Profit margin %" not in month_year_agg.columns:
            month_year_agg["Profit margin %"] = 0.0
            mask = month_year_agg["Fee"] > 0
            month_year_agg.loc[mask, "Profit margin %"] = (month_year_agg.loc[mask, "Total profit"] / month_year_agg.loc[mask, "Fee"] * 100).round(2)
    
    # Sort by date if we have data
    if not month_year_agg.empty and 'Date string' in month_year_agg.columns:
        month_year_agg = month_year_agg.sort_values('Date string')
    
    return month_year_agg
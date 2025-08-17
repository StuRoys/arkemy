# planned_processors.py
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Any, Optional

def aggregate_by_project_planned(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate planned hours data by project using simple pandas operations.
    
    Args:
        df: DataFrame with planned hours data
        
    Returns:
        Dataframe with project aggregations of planned hours
    """
    # Basic validation
    if df is None or df.empty:
        # Return empty dataframe with expected columns
        return pd.DataFrame(columns=["project_number", "project_name", "planned_hours", "Number of people", "planned_hourly_rate", "planned_fee"])
        
    # Make a copy to avoid modifying original
    df = df.copy()
    
    # Convert Project number to string for consistent joining
    df["project_number"] = df["project_number"].astype(str)
    df["project_name"] = df["project_name"].fillna("Unknown Project")
    
    # Simple groupby aggregation by project
    project_agg = df.groupby(["project_number", "project_name"], as_index=False).agg({
        "planned_hours": "sum",
        "person_name": "nunique"
    })
    
    # Rename Person column to match expected format
    project_agg = project_agg.rename(columns={"person_name": "Number of people"})
    
    # Add planned rate calculation if available
    if "planned_hourly_rate" in df.columns:
        # Calculate weighted rate per project
        rate_df = df.copy()
        rate_df["weighted_rate"] = rate_df["planned_hourly_rate"] * rate_df["planned_hours"]
        
        # Group and calculate weighted average
        rate_agg = rate_df.groupby("project_number", as_index=False).agg({
            "weighted_rate": "sum",
            "planned_hours": "sum"
        })
        
        # Calculate the weighted average rate
        rate_agg["planned_hourly_rate"] = 0.0
        mask = rate_agg["planned_hours"] > 0
        rate_agg.loc[mask, "planned_hourly_rate"] = rate_agg.loc[mask, "weighted_rate"] / rate_agg.loc[mask, "planned_hours"]
        
        # Merge rate with main aggregation
        project_agg = pd.merge(
            project_agg, 
            rate_agg[["project_number", "planned_hourly_rate"]], 
            on="project_number",
            how="left"
        )
        
        # Calculate planned fee
        project_agg["planned_fee"] = project_agg["planned_hours"] * project_agg["planned_hourly_rate"]
    else:
        # Add placeholder columns
        project_agg["planned_hourly_rate"] = 0
        project_agg["planned_fee"] = 0
    
    return project_agg

def merge_actual_planned_projects(actual_df: pd.DataFrame, planned_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge actual and planned hours data at the project level.
    
    Args:
        actual_df: DataFrame with actual project aggregations
        planned_df: DataFrame with planned project aggregations
        
    Returns:
        Merged dataframe with both actual and planned metrics
    """
    # Ensure inputs are valid
    if actual_df is None or actual_df.empty:
        return planned_df
    
    if planned_df is None or planned_df.empty:
        return actual_df
    
    # Make copies to avoid modifying originals
    actual_df = actual_df.copy()
    planned_df = planned_df.copy()
    
    # Ensure Project number is string type
    actual_df["project_number"] = actual_df["project_number"].astype(str)
    planned_df["project_number"] = planned_df["project_number"].astype(str)
    
    # Get required columns from planned data
    planned_cols = ["project_number", "project_name", "planned_hours"]
    if "planned_hourly_rate" in planned_df.columns:
        planned_cols.append("planned_hourly_rate")
    if "planned_fee" in planned_df.columns:
        planned_cols.append("planned_fee")
    
    # Simple outer merge on Project number and name
    merged_df = pd.merge(
        actual_df,
        planned_df[planned_cols],
        on=["project_number", "project_name"],
        how="outer"  # Include all projects from both dataframes
    )
    
    # Fill missing values
    for col in merged_df.columns:
        if col in ["hours_used", "hours_billable", "planned_hours", "Fee", "planned_fee"]:
            merged_df[col] = merged_df[col].fillna(0)
    
    # Calculate variance metrics
    merged_df["Hours variance"] = merged_df["hours_used"] - merged_df["planned_hours"]
    
    # Calculate percentage variance (avoiding division by zero)
    merged_df["Variance percentage"] = 0.0
    mask = merged_df["planned_hours"] > 0
    merged_df.loc[mask, "Variance percentage"] = (
        merged_df.loc[mask, "Hours variance"] / merged_df.loc[mask, "planned_hours"] * 100
    ).round(2)
    
    # Handle rate variances if available
    if "planned_hourly_rate" in merged_df.columns:
        merged_df["planned_hourly_rate"] = merged_df["planned_hourly_rate"].fillna(0)
        merged_df["Effective rate"] = merged_df["Effective rate"].fillna(0)
        
        merged_df["Rate variance"] = merged_df["Effective rate"] - merged_df["planned_hourly_rate"]
        
        # Calculate rate variance percentage (avoiding division by zero)
        merged_df["Rate variance percentage"] = 0.0
        mask = merged_df["planned_hourly_rate"] > 0
        merged_df.loc[mask, "Rate variance percentage"] = (
            merged_df.loc[mask, "Rate variance"] / merged_df.loc[mask, "planned_hourly_rate"] * 100
        ).round(2)
    
    # Handle fee variances if available
    if "planned_fee" in merged_df.columns:
        merged_df["Fee variance"] = merged_df["Fee"] - merged_df["planned_fee"]
        
        # Calculate fee variance percentage (avoiding division by zero)
        merged_df["Fee variance percentage"] = 0.0
        mask = merged_df["planned_fee"] > 0
        merged_df.loc[mask, "Fee variance percentage"] = (
            merged_df.loc[mask, "Fee variance"] / merged_df.loc[mask, "planned_fee"] * 100
        ).round(2)
    
    return merged_df

def calculate_planned_summary_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate summary metrics for planned hours.
    
    Args:
        df: DataFrame with planned hours data
        
    Returns:
        Dictionary containing summary metrics
    """
    metrics = {}
    
    # Count metrics
    metrics["total_entries"] = len(df)
    metrics["unique_projects"] = df["project_number"].nunique()
    metrics["unique_people"] = df["person_name"].nunique()
    
    # Sum metrics
    metrics["total_planned_hours"] = df["planned_hours"].sum()
    
    # Date metrics
    if "record_date" in df.columns and not df.empty:
        metrics["first_planned_record"] = df["record_date"].min()
        metrics["last_planned_record"] = df["record_date"].max()
        # Calculate span in days between first and last record
        date_diff = metrics["last_planned_record"] - metrics["first_planned_record"]
        metrics["days_span"] = date_diff.days
    else:
        metrics["first_planned_record"] = None
        metrics["last_planned_record"] = None
        metrics["days_span"] = 0
    
    # Add planned rate metrics if available
    if "planned_hourly_rate" in df.columns:
        # Calculate weighted average planned rate
        total_planned_hours = df["planned_hours"].sum()
        if total_planned_hours > 0:
            metrics["average_planned_rate"] = (
                (df["planned_hourly_rate"] * df["planned_hours"]).sum() / total_planned_hours
            ).round(2)
        else:
            metrics["average_planned_rate"] = 0
            
        # Calculate total planned fee
        metrics["total_planned_fee"] = (df["planned_hourly_rate"] * df["planned_hours"]).sum()
    else:
        metrics["average_planned_rate"] = 0
        metrics["total_planned_fee"] = 0
        
    return metrics

def compare_actual_vs_planned(actual_df: pd.DataFrame, planned_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare actual vs planned hours at summary level.
    
    Args:
        actual_df: DataFrame with actual hours data
        planned_df: DataFrame with planned hours data
        
    Returns:
        Dictionary with comparison metrics
    """
    comparison = {}
    
    # Get totals
    total_actual = actual_df["hours_used"].sum() if "hours_used" in actual_df.columns else 0
    total_planned = planned_df["planned_hours"].sum() if "planned_hours" in planned_df.columns else 0
    
    # Calculate variance
    comparison["total_actual_hours"] = total_actual
    comparison["total_planned_hours"] = total_planned
    comparison["total_variance_hours"] = total_actual - total_planned
    
    # Calculate percentage variance
    if total_planned > 0:
        comparison["total_variance_percentage"] = (comparison["total_variance_hours"] / total_planned * 100).round(2)
    else:
        comparison["total_variance_percentage"] = 0
        
    # Count metrics
    comparison["actual_projects"] = actual_df["project_number"].nunique() if "project_number" in actual_df.columns else 0
    comparison["planned_projects"] = planned_df["project_number"].nunique() if "project_number" in planned_df.columns else 0
    
    # Projects in both datasets
    if "project_number" in actual_df.columns and "project_number" in planned_df.columns:
        actual_projects = set(actual_df["project_number"].unique())
        planned_projects = set(planned_df["project_number"].unique())
        
        comparison["common_projects"] = len(actual_projects.intersection(planned_projects))
        comparison["only_actual_projects"] = len(actual_projects - planned_projects)
        comparison["only_planned_projects"] = len(planned_projects - actual_projects)
    else:
        comparison["common_projects"] = 0
        comparison["only_actual_projects"] = 0
        comparison["only_planned_projects"] = 0
    
    # Add rate comparison if available
    if "Effective rate" in actual_df.columns and "planned_hourly_rate" in planned_df.columns:
        # Calculate weighted averages
        total_actual_billable = actual_df["hours_billable"].sum() if "hours_billable" in actual_df.columns else 0
        if total_actual_billable > 0:
            avg_effective_rate = actual_df["Fee"].sum() / total_actual_billable
        else:
            avg_effective_rate = 0
            
        total_planned_hours = planned_df["planned_hours"].sum()
        if total_planned_hours > 0:
            avg_planned_rate = (
                (planned_df["planned_hourly_rate"] * planned_df["planned_hours"]).sum() / total_planned_hours
            )
        else:
            avg_planned_rate = 0
            
        # Store rates and variances
        comparison["avg_effective_rate"] = avg_effective_rate
        comparison["avg_planned_rate"] = avg_planned_rate
        comparison["rate_variance"] = avg_effective_rate - avg_planned_rate
        
        # Calculate percentage variance
        if avg_planned_rate > 0:
            comparison["rate_variance_percentage"] = (
                comparison["rate_variance"] / avg_planned_rate * 100
            ).round(2)
        else:
            comparison["rate_variance_percentage"] = 0
            
    return comparison
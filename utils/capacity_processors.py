# utils/capacity_processors.py
"""
Simplified capacity analysis processors for ARKEMY.

This module contains basic aggregation functions for capacity analysis,
focusing on schedule and capacity calculations per person.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any

def calculate_person_capacity(capacity_df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate schedule and capacity metrics by person.
    
    Args:
        capacity_df: DataFrame with capacity summary data containing:
                    - Date, Person, Scheduled_Hours, Absence_Hours
        
    Returns:
        DataFrame with person-level capacity aggregations including:
        - Scheduled_Hours (total scheduled time)
        - Available_Capacity (scheduled minus absences)
        - Absence_Rate and Capacity_Utilization_Rate
    """
    if capacity_df.empty:
        return pd.DataFrame()
    
    # Group by person and aggregate
    person_agg = capacity_df.groupby("person_name").agg({
        "Scheduled_Hours": "sum",
        "Absence_Hours": "sum", 
        "record_date": ["min", "max", "count"]  # Period range and count
    }).round(2)
    
    # Flatten column names
    person_agg.columns = [
        "Scheduled_Hours", "Absence_Hours", 
        "Period_Start", "Period_End", "Period_Count"
    ]
    
    # Calculate available capacity
    person_agg["Available_Capacity"] = person_agg["Scheduled_Hours"] - person_agg["Absence_Hours"]
    
    # Calculate derived metrics
    person_agg["Absence_Rate"] = ((person_agg["Absence_Hours"] / person_agg["Scheduled_Hours"]) * 100).round(1)
    person_agg["Capacity_Utilization_Rate"] = ((person_agg["Available_Capacity"] / person_agg["Scheduled_Hours"]) * 100).round(1)
    
    # Reset index to make Person a column
    person_agg = person_agg.reset_index()
    
    return person_agg

def aggregate_time_records_to_weekly(time_records_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate time records to weekly periods matching capacity data structure.
    
    Args:
        time_records_df: DataFrame with time records (Date, Person, Hours worked, etc.)
        
    Returns:
        DataFrame with weekly aggregated time records
    """
    if time_records_df.empty:
        return pd.DataFrame()
    
    df = time_records_df.copy()
    
    # Ensure Date is datetime
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Create week starting date (Monday of each week)
    df['Week_Start'] = df['Date'].dt.to_period('W').dt.start_time
    
    # Aggregate by Person and Week_Start
    weekly_agg = df.groupby(['Person', 'Week_Start']).agg({
        'hours_used': 'sum',
        'hours_billable': 'sum'
    }).reset_index()
    
    # Rename Week_Start to Date to match capacity data structure
    weekly_agg = weekly_agg.rename(columns={'Week_Start': 'Date'})
    
    return weekly_agg

def calculate_capacity_summary(capacity_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate basic summary metrics for capacity data.
    
    Args:
        capacity_df: DataFrame with capacity data
        
    Returns:
        Dictionary with summary metrics
    """
    if capacity_df.empty:
        return {}
    
    metrics = {
        "total_people": capacity_df["person_name"].nunique(),
        "total_periods": len(capacity_df),
        "total_scheduled_hours": capacity_df["Scheduled_Hours"].sum(),
        "total_absence_hours": capacity_df["Absence_Hours"].sum(),
        "total_available_capacity": (capacity_df["Scheduled_Hours"] - capacity_df["Absence_Hours"]).sum(),
        "overall_absence_rate": round((capacity_df["Absence_Hours"].sum() / capacity_df["Scheduled_Hours"].sum() * 100), 1) if capacity_df["Scheduled_Hours"].sum() > 0 else 0
    }
    
    if "record_date" in capacity_df.columns:
        metrics["date_range"] = {
            "start": capacity_df["record_date"].min(),
            "end": capacity_df["record_date"].max()
        }
    
    return metrics
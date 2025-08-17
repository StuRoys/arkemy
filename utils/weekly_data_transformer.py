# utils/weekly_data_transformer.py
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
from utils.capacity_validation import (
    parse_capacity_config, 
    get_absence_columns_from_config,
    transform_schedule_data,
    transform_absence_data
)

def transform_weekly_to_schedule(weekly_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert weekly format data to ARKEMY schedule format.
    
    Args:
        weekly_df: DataFrame with weekly data from your system
        
    Returns:
        DataFrame in ARKEMY schedule format with columns:
        - Date (from Period from)
        - Person 
        - Scheduled_Hours (from Total agreed hours)
    """
    if weekly_df.empty:
        return pd.DataFrame()
    
    schedule_df = weekly_df.copy()
    
    # Convert Period from to Date
    schedule_df["record_date"] = pd.to_datetime(schedule_df["Period from"])
    
    # Map columns to ARKEMY format
    column_mapping = {
        "Total agreed hours": "Scheduled_Hours"
    }
    
    # Rename columns
    for old_col, new_col in column_mapping.items():
        if old_col in schedule_df.columns:
            schedule_df[new_col] = schedule_df[old_col]
    
    # Select only required columns
    required_columns = ["record_date", "person_name", "Scheduled_Hours"]
    available_columns = [col for col in required_columns if col in schedule_df.columns]
    
    schedule_df = schedule_df[available_columns].copy()
    
    # Apply data transformations
    schedule_df = transform_schedule_data(schedule_df)
    
    return schedule_df

def transform_weekly_to_absence(weekly_df: pd.DataFrame, capacity_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Convert weekly format data to ARKEMY absence format using capacity configuration.
    
    Args:
        weekly_df: DataFrame with weekly data from your system
        capacity_config: Parsed capacity configuration with absence rules
        
    Returns:
        DataFrame in ARKEMY absence format with columns:
        - Date (from Period from) 
        - Person
        - Absence_Hours (sum based on config rules)
        - Absence_Type (human-readable description)
    """
    if weekly_df.empty:
        return pd.DataFrame()
    
    absence_df = weekly_df.copy()
    
    # Convert Period from to Date
    absence_df["record_date"] = pd.to_datetime(absence_df["Period from"])
    
    # Get absence configuration
    absence_types = capacity_config.get("absence_types", {})
    absence_rules = capacity_config.get("absence_rules", {})
    include_in_capacity = absence_rules.get("include_in_capacity_reduction", [])
    exclude_from_capacity = absence_rules.get("exclude_from_capacity_reduction", [])
    
    # Find absence columns in the data
    absence_columns = [col for col in absence_df.columns if col.startswith('Absence ')]
    
    # Calculate total absence hours based on config rules
    total_absence_hours = 0.0
    included_types = []
    excluded_types = []
    
    for col in absence_columns:
        # Extract the absence type ID from column name (e.g., "illness_676657139" from "Absence illness_676657139 hours")
        absence_id = extract_absence_id_from_column(col)
        
        if absence_id:
            # Get human-readable name
            human_name = absence_types.get(absence_id, absence_id)
            
            # Check if this absence type should be included in capacity reduction
            if absence_id in include_in_capacity:
                total_absence_hours += absence_df[col].fillna(0)
                included_types.append(human_name)
            elif absence_id in exclude_from_capacity:
                excluded_types.append(human_name)
            else:
                # If not specified in config, include by default (conservative approach)
                total_absence_hours += absence_df[col].fillna(0)
                included_types.append(human_name)
    
    # Create absence type description
    if included_types:
        absence_type = f"Included: {', '.join(set(included_types))}"
        if excluded_types:
            absence_type += f" | Excluded: {', '.join(set(excluded_types))}"
    else:
        absence_type = "No absence affecting capacity"
    
    # Create the absence dataframe
    result_df = pd.DataFrame({
        "record_date": absence_df["record_date"],
        "person_name": absence_df["person_name"],
        "Absence_Hours": total_absence_hours,
        "Absence_Type": absence_type
    })
    
    # Apply data transformations
    result_df = transform_absence_data(result_df)
    
    return result_df

def extract_absence_id_from_column(column_name: str) -> Optional[str]:
    """
    Extract absence type ID from column name.
    
    Example: "Absence illness_676657139 hours" -> "illness_676657139"
    
    Args:
        column_name: The absence column name
        
    Returns:
        Absence type ID or None if not found
    """
    if not column_name.startswith('Absence '):
        return None
    
    # Remove "Absence " prefix and " hours" suffix
    middle_part = column_name[8:]  # Remove "Absence "
    if middle_part.endswith(' hours'):
        middle_part = middle_part[:-6]  # Remove " hours"
    
    return middle_part if middle_part else None

def load_capacity_config_from_dataframe(config_df: pd.DataFrame) -> Optional[Dict[str, Any]]:
    """
    Load and parse capacity configuration from dataframe.
    
    Args:
        config_df: DataFrame containing capacity configuration
        
    Returns:
        Parsed configuration dictionary or None if not available
    """
    if config_df.empty:
        return None
    
    try:
        # Get the config content from the first row
        config_content = config_df['config_content'].iloc[0]
        return parse_capacity_config(config_content)
    except Exception as e:
        st.error(f"Error parsing capacity configuration: {str(e)}")
        return None

def create_capacity_summary(schedule_df: pd.DataFrame, 
                          absence_df: pd.DataFrame, 
                          capacity_config: Dict[str, Any]) -> pd.DataFrame:
    """
    Create a summary dataframe combining schedule and absence data for capacity analysis.
    
    Args:
        schedule_df: Schedule data in ARKEMY format
        absence_df: Absence data in ARKEMY format  
        capacity_config: Capacity configuration
        
    Returns:
        DataFrame with combined capacity metrics per person per period
    """
    if schedule_df.empty:
        return pd.DataFrame()
    
    # Start with schedule data
    capacity_df = schedule_df.copy()
    
    # Merge with absence data if available
    if not absence_df.empty:
        # Merge on Date and Person
        capacity_df = pd.merge(
            capacity_df,
            absence_df[["record_date", "person_name", "Absence_Hours", "Absence_Type"]],
            on=["record_date", "person_name"],
            how="left"
        )
        
        # Fill missing absence hours with 0
        capacity_df["Absence_Hours"] = capacity_df["Absence_Hours"].fillna(0.0)
        capacity_df["Absence_Type"] = capacity_df["Absence_Type"].fillna("No absence")
    else:
        capacity_df["Absence_Hours"] = 0.0
        capacity_df["Absence_Type"] = "No absence data"
    
    # Calculate available capacity
    capacity_df["Available_Capacity"] = capacity_df["Scheduled_Hours"] - capacity_df["Absence_Hours"]
    
    # Ensure non-negative capacity
    capacity_df["Available_Capacity"] = capacity_df["Available_Capacity"].clip(lower=0)
    
    # Add configuration metadata
    capacity_df["Billable_Target"] = capacity_config.get("billable_target", 0.80)
    capacity_df["Target_Billable_Hours"] = capacity_df["Available_Capacity"] * capacity_df["Billable_Target"]
    
    return capacity_df

def validate_weekly_data_completeness(weekly_df: pd.DataFrame, capacity_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate that the weekly data contains all required columns based on the capacity configuration.
    
    Args:
        weekly_df: Weekly source data
        capacity_config: Capacity configuration
        
    Returns:
        Dictionary with validation results and warnings
    """
    validation_result = {
        "is_complete": True,
        "missing_absence_columns": [],
        "warnings": [],
        "suggestions": []
    }
    
    # Check for required schedule columns
    required_schedule_columns = ["Period from", "person_name", "Total agreed hours"]
    missing_schedule = [col for col in required_schedule_columns if col not in weekly_df.columns]
    
    if missing_schedule:
        validation_result["is_complete"] = False
        validation_result["warnings"].append(f"Missing schedule columns: {', '.join(missing_schedule)}")
    
    # Check for absence columns mentioned in config
    config_absence_ids = get_absence_columns_from_config(capacity_config)
    missing_absence = []
    
    for absence_id in config_absence_ids:
        # Look for columns containing this absence ID
        matching_columns = [col for col in weekly_df.columns if absence_id in col]
        if not matching_columns:
            missing_absence.append(absence_id)
    
    if missing_absence:
        validation_result["missing_absence_columns"] = missing_absence
        validation_result["warnings"].append(f"Configuration references absence types not found in data: {', '.join(missing_absence)}")
        validation_result["suggestions"].append("Check if absence column names match the configuration or update the configuration")
    
    # Check for unused absence columns
    data_absence_columns = [col for col in weekly_df.columns if col.startswith('Absence ')]
    unused_absence = []
    
    for col in data_absence_columns:
        absence_id = extract_absence_id_from_column(col)
        if absence_id and absence_id not in config_absence_ids:
            unused_absence.append(absence_id)
    
    if unused_absence:
        validation_result["suggestions"].append(f"Data contains absence types not in configuration: {', '.join(unused_absence[:5])}{'...' if len(unused_absence) > 5 else ''}")
    
    return validation_result

def get_capacity_processing_summary(schedule_df: pd.DataFrame, 
                                  absence_df: pd.DataFrame, 
                                  capacity_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a summary of the capacity data processing results.
    
    Args:
        schedule_df: Processed schedule data
        absence_df: Processed absence data
        capacity_config: Applied configuration
        
    Returns:
        Dictionary with processing summary
    """
    summary = {
        "schedule_records": len(schedule_df) if not schedule_df.empty else 0,
        "absence_records": len(absence_df) if not absence_df.empty else 0,
        "unique_persons": 0,
        "date_range": None,
        "total_scheduled_hours": 0.0,
        "total_absence_hours": 0.0,
        "config_applied": capacity_config is not None
    }
    
    if not schedule_df.empty:
        summary["unique_persons"] = schedule_df["person_name"].nunique()
        summary["date_range"] = {
            "start": schedule_df["record_date"].min(),
            "end": schedule_df["record_date"].max()
        }
        summary["total_scheduled_hours"] = schedule_df["Scheduled_Hours"].sum()
    
    if not absence_df.empty:
        summary["total_absence_hours"] = absence_df["Absence_Hours"].sum()
    
    return summary
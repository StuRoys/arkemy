# utils/capacity_validation.py
import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import streamlit as st
import yaml
import json

# Define schemas for capacity-related data

# Schema for transformed schedule data (ARKEMY format)
SCHEDULE_SCHEMA = {
    "record_date": "datetime",
    "person_name": "string",
    "Scheduled_Hours": "float"
}

# Schema for transformed absence data (ARKEMY format)
ABSENCE_SCHEMA = {
    "record_date": "datetime",
    "person_name": "string",
    "Absence_Hours": "float",
    "Absence_Type": "string"
}

# Schema for capacity configuration data
CAPACITY_CONFIG_SCHEMA = {
    "config_type": "string",
    "config_content": "string"
}

# Schema for weekly source data (raw format from your system)
WEEKLY_SOURCE_SCHEMA = {
    "Period from": "string",
    "Period to": "string",
    "person_name": "string",
    "Title": "string",
    "User account ID": "integer",
    "Total billable hours": "integer",
    "Total not billable hours": "integer", 
    "Total time records hours": "integer",
    "Total agreed hours": "float",
    "Working days": "integer",
    "Scheduled hours work day": "float",
    "Company code": "string"
    # Note: Absence columns are dynamic based on client config
}

# Optional columns for different schemas
SCHEDULE_OPTIONAL_COLUMNS = []
ABSENCE_OPTIONAL_COLUMNS = ["Absence_Type"]
WEEKLY_OPTIONAL_COLUMNS = ["Title", "Company code"]

def validate_schedule_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates if the schedule dataframe has the expected schema.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dict with validation results
    """
    return _validate_schema(df, SCHEDULE_SCHEMA, SCHEDULE_OPTIONAL_COLUMNS, "schedule")

def validate_absence_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates if the absence dataframe has the expected schema.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dict with validation results
    """
    return _validate_schema(df, ABSENCE_SCHEMA, ABSENCE_OPTIONAL_COLUMNS, "absence")

def load_client_absence_config(client_id):
    with open(f"configs/{client_id}_absence.yml", 'r') as f:
        return yaml.safe_load(f)

def validate_capacity_config_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates if the capacity config dataframe has the expected schema.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dict with validation results
    """
    result = _validate_schema(df, CAPACITY_CONFIG_SCHEMA, [], "capacity_config")
    
    # Additional validation for config content
    if result["is_valid"] and not df.empty:
        try:
            config_content = df['config_content'].iloc[0]
            # Try to parse as YAML first, then JSON
            try:
                parsed_config = yaml.safe_load(config_content)
            except:
                parsed_config = json.loads(config_content)
            
            # Validate config structure
            if not isinstance(parsed_config, dict):
                result["type_errors"].append("Config content must be a valid YAML/JSON object")
                result["is_valid"] = False
            
        except Exception as e:
            result["type_errors"].append(f"Config content is not valid YAML/JSON: {str(e)}")
            result["is_valid"] = False
    
    return result

def validate_weekly_source_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates if the weekly source dataframe has the expected schema.
    Handles dynamic absence columns based on what's present in the data.
    
    Args:
        df: The dataframe to validate
        
    Returns:
        Dict with validation results
    """
    # Create a dynamic schema that includes detected absence columns
    dynamic_schema = WEEKLY_SOURCE_SCHEMA.copy()
    
    # Find absence columns in the dataframe
    absence_columns = [col for col in df.columns if col.startswith('Absence ')]
    for col in absence_columns:
        # Absence columns can be integer or float
        if 'hours' in col.lower():
            dynamic_schema[col] = "float"
    
    return _validate_schema(df, dynamic_schema, WEEKLY_OPTIONAL_COLUMNS + absence_columns, "weekly_source")

def _validate_schema(df: pd.DataFrame, schema: Dict[str, str], optional_columns: List[str], data_type: str) -> Dict[str, Any]:
    """
    Generic schema validation function.
    
    Args:
        df: The dataframe to validate
        schema: Schema dictionary with column names and types
        optional_columns: List of optional column names
        data_type: String describing the data type for error messages
        
    Returns:
        Dict with validation results
    """
    result = {
        "is_valid": True,
        "missing_columns": [],
        "type_errors": [],
        "problematic_values": {}
    }
    
    if df is None or df.empty:
        result["is_valid"] = False
        result["missing_columns"] = ["DataFrame is empty"]
        return result
    
    # Check for missing required columns
    for column in schema:
        if column not in df.columns and column not in optional_columns:
            result["missing_columns"].append(column)
            result["is_valid"] = False
    
    if not result["is_valid"]:
        return result
    
    # Check data types for existing columns
    for column, expected_type in schema.items():
        if column in df.columns:
            if expected_type == "datetime":
                try:
                    pd.to_datetime(df[column])
                except Exception:
                    result["type_errors"].append(f"{column} is not a valid datetime")
                    result["is_valid"] = False
                    
                    # Store problematic values
                    problematic_rows = []
                    for idx, value in df[column].items():
                        try:
                            pd.to_datetime(value)
                        except:
                            problematic_rows.append((idx, value))
                    
                    if problematic_rows:
                        result["problematic_values"][column] = problematic_rows[:10]
                        
            elif expected_type in ["float", "integer"]:
                try:
                    if expected_type == "integer":
                        df[column].astype(int)
                    else:
                        df[column].astype(float)
                except Exception:
                    result["type_errors"].append(f"{column} contains non-numeric values")
                    result["is_valid"] = False
                    
                    # Store problematic values
                    problematic_rows = []
                    for idx, value in df[column].items():
                        try:
                            if expected_type == "integer":
                                int(value)
                            else:
                                float(value)
                        except:
                            problematic_rows.append((idx, value))
                    
                    if problematic_rows:
                        result["problematic_values"][column] = problematic_rows[:10]
    
    return result

def transform_schedule_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the schedule dataframe to match the expected schema.
    
    Args:
        df: The dataframe to transform
        
    Returns:
        Transformed dataframe
    """
    transformed_df = df.copy()
    
    # Convert columns to the correct types
    for column, expected_type in SCHEDULE_SCHEMA.items():
        if column in transformed_df.columns:
            if expected_type == "datetime":
                transformed_df[column] = pd.to_datetime(transformed_df[column])
            elif expected_type == "float":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
            elif expected_type == "integer":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce').astype('Int64')
            elif expected_type == "string":
                transformed_df[column] = transformed_df[column].astype(str)
    
    return transformed_df

def transform_absence_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the absence dataframe to match the expected schema.
    
    Args:
        df: The dataframe to transform
        
    Returns:
        Transformed dataframe
    """
    transformed_df = df.copy()
    
    # Convert columns to the correct types
    for column, expected_type in ABSENCE_SCHEMA.items():
        if column in transformed_df.columns:
            if expected_type == "datetime":
                transformed_df[column] = pd.to_datetime(transformed_df[column])
            elif expected_type == "float":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
            elif expected_type == "string":
                transformed_df[column] = transformed_df[column].astype(str)
        else:
            # Add missing optional columns with default values
            if column in ABSENCE_OPTIONAL_COLUMNS:
                if expected_type == "float":
                    transformed_df[column] = 0.0
                elif expected_type == "string":
                    transformed_df[column] = "Mixed"
    
    return transformed_df

def transform_weekly_source_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Transforms the weekly source dataframe to standardize data types.
    
    Args:
        df: The dataframe to transform
        
    Returns:
        Transformed dataframe
    """
    transformed_df = df.copy()
    
    # Convert basic columns
    basic_schema = {k: v for k, v in WEEKLY_SOURCE_SCHEMA.items() if not k.startswith('Absence ')}
    
    for column, expected_type in basic_schema.items():
        if column in transformed_df.columns:
            if expected_type == "datetime":
                transformed_df[column] = pd.to_datetime(transformed_df[column])
            elif expected_type == "float":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
            elif expected_type == "integer":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce').astype('Int64')
            elif expected_type == "string":
                transformed_df[column] = transformed_df[column].astype(str)
    
    # Convert absence columns to float
    absence_columns = [col for col in transformed_df.columns if col.startswith('Absence ')]
    for col in absence_columns:
        transformed_df[col] = pd.to_numeric(transformed_df[col], errors='coerce').fillna(0.0)
    
    return transformed_df

def display_schedule_validation_results(validation_results: Dict[str, Any]) -> None:
    """
    Displays validation results for schedule data in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
    """
    _display_validation_results(validation_results, "Schedule")

def display_absence_validation_results(validation_results: Dict[str, Any]) -> None:
    """
    Displays validation results for absence data in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
    """
    _display_validation_results(validation_results, "Absence")

def display_capacity_config_validation_results(validation_results: Dict[str, Any]) -> None:
    """
    Displays validation results for capacity config data in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
    """
    _display_validation_results(validation_results, "Capacity Configuration")

def display_weekly_source_validation_results(validation_results: Dict[str, Any]) -> None:
    """
    Displays validation results for weekly source data in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
    """
    _display_validation_results(validation_results, "Weekly Source")

def _display_validation_results(validation_results: Dict[str, Any], data_type: str) -> None:
    """
    Generic function to display validation results in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
        data_type: String describing the type of data being validated
    """
    if validation_results["is_valid"]:
        st.success(f"{data_type} data matches the expected schema!")
    else:
        st.error(f"{data_type} data does not match the expected schema.")
        
        if validation_results["missing_columns"]:
            st.warning(f"Missing columns: {', '.join(validation_results['missing_columns'])}")
        
        if validation_results["type_errors"]:
            st.warning(f"Type errors: {', '.join(validation_results['type_errors'])}")
        
        # Display problematic values
        if "problematic_values" in validation_results and validation_results["problematic_values"]:
            st.subheader("Problematic Values")
            for column, values in validation_results["problematic_values"].items():
                st.write(f"**{column}** - Problematic values:")
                for idx, value in values:
                    st.write(f"Row {idx}: '{value}' (type: {type(value).__name__})")

def parse_capacity_config(config_content: str) -> Dict[str, Any]:
    """
    Parse capacity configuration content from YAML or JSON.
    
    Args:
        config_content: String containing YAML or JSON configuration
        
    Returns:
        Parsed configuration dictionary
    """
    try:
        # Try YAML first
        return yaml.safe_load(config_content)
    except:
        try:
            # Fall back to JSON
            return json.loads(config_content)
        except Exception as e:
            raise ValueError(f"Configuration content is not valid YAML or JSON: {str(e)}")

def get_absence_columns_from_config(config: Dict[str, Any]) -> List[str]:
    """
    Extract absence column names from capacity configuration.
    
    Args:
        config: Parsed capacity configuration
        
    Returns:
        List of absence column names used in the configuration
    """
    absence_columns = []
    
    if 'absence_types' in config:
        absence_columns.extend(config['absence_types'].keys())
    
    if 'absence_rules' in config:
        rules = config['absence_rules']
        if 'include_in_capacity_reduction' in rules:
            absence_columns.extend(rules['include_in_capacity_reduction'])
        if 'exclude_from_capacity_reduction' in rules:
            absence_columns.extend(rules['exclude_from_capacity_reduction'])
    
    return list(set(absence_columns))  # Remove duplicates
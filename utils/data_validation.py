"""
ARKEMY Data Validation Module

This module validates data using the new snake_case schema format.
Legacy data with old column names (e.g., "hours_used", "customer_name") 
should be converted using the convert_legacy_data.py script before loading.

The schema now uses snake_case field names consistent with the YAML specification
in arkemy_schema_filtered.yaml.
"""

import pandas as pd
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
import streamlit as st
from pathlib import Path

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

# Define the expected schema for main data (snake_case format)
# Legacy data should be converted using convert_legacy_data.py script
MAIN_SCHEMA = {
    "record_date": "datetime",
    "customer_number": "string",
    "customer_name": "string", 
    "project_number": "string",
    "project_name": "string",
    "project_tag": "string",
    "price_model_type": "string",
    "phase_tag": "string",
    "activity_tag": "string",
    "person_name": "string",
    "person_type": "string",
    "hours_used": "float",
    "hours_billable": "float",
    "billable_rate_record": "float",
    "billable_rate_adjust": "float",
    "fee_record": "float", # "billable_rate_record" * "hours_billable"
    "fee_record_adjust": "float", # "billable_rate_adjust" * "hours_billable"
    "cost_hour": "float", # added from separate table in ETL
    "cost_record": "float", # "cost_hour" * "hours_used"
    "cost_hour_adjust": "float", #calculated in ETL using index
    "cost_record_adjust": "float", # "cost_hour_adjust" * "hours_used"
    "profit_hour": "float", # "billable_rate_record" - "cost_hour"
    "profit_record": "float", # "profit_hour" * "hours_used"
    "profit_hour_adjust": "float", # "billable_rate_adjust" - "cost_hour_adjust"
    "profit_record_adjust": "float", # "profit_hour_adjust" * "hours_used"
    "planned_hours": "float",
    "planned_billable": "float",
    "planned_hourly_rate": "float",
    "planned_fee": "float",
}

# Define the expected schema for planned data (snake_case format)
PLANNED_SCHEMA = {
    "record_date": "datetime",
    "person_name": "string", 
    "project_number": "string",
    "project_name": "string",
    "planned_hours": "float",
    "planned_hourly_rate": "float"
}

# Define optional columns (snake_case format)
MAIN_OPTIONAL_COLUMNS = ["billable_rate_adjust", "person_type", "customer_number", "customer_name",
                    "project_tag", "price_model_type", "phase_tag", "activity_tag",
                    "planned_hours", "planned_hourly_rate", "planned_fee",
                    "fee_record", "cost_hour", "cost_record",
                    "profit_per_record", "profit_per_hour", "planned_billable", "data_source",
                    "fee_record_adjust", "cost_hour_adjust", "cost_record_adjust", 
                    "profit_hour_adjust", "profit_record_adjust"]

PLANNED_OPTIONAL_COLUMNS = ["planned_hourly_rate"]

# Maintain backward compatibility
EXPECTED_SCHEMA = MAIN_SCHEMA  
OPTIONAL_COLUMNS = MAIN_OPTIONAL_COLUMNS

def validate_schema(df: pd.DataFrame, schema_type: str = "main") -> Dict[str, Any]:
    """
    Validates if the dataframe has the expected schema.
    
    Args:
        df: The dataframe to validate
        schema_type: Either "main" or "planned" to specify which schema to use
        
    Returns:
        Dict with validation results
    """
    # Select schema based on type
    if schema_type == "planned":
        schema = PLANNED_SCHEMA
        optional_cols = PLANNED_OPTIONAL_COLUMNS
    else:
        schema = MAIN_SCHEMA
        optional_cols = MAIN_OPTIONAL_COLUMNS
    result = {
        "is_valid": True,
        "missing_columns": [],
        "type_errors": [],
        "problematic_values": {}  # New field to store problematic values
    }
    
    # Check for missing columns (exclude optional ones)
    for column in schema:
        if column not in df.columns and column not in optional_cols:
            result["missing_columns"].append(column)
            result["is_valid"] = False
    
    if not result["is_valid"]:
        return result
    
    # Check data types
    for column, expected_type in schema.items():
        if column in df.columns:  # Only check columns that exist in the dataframe
            if expected_type == "datetime":
                try:
                    # Attempt to convert to datetime
                    pd.to_datetime(df[column])
                except Exception as e:
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
                        result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
                
            elif expected_type == "float":
                try:
                    # Check if values can be converted to float
                    df[column].astype(float)
                except Exception as e:
                    result["type_errors"].append(f"{column} contains non-numeric values")
                    result["is_valid"] = False
                    
                    # Store problematic values
                    problematic_rows = []
                    for idx, value in df[column].items():
                        try:
                            float(value)
                        except:
                            problematic_rows.append((idx, value))
                    
                    if problematic_rows:
                        result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
    
    return result
    
    # Check data types
    for column, expected_type in EXPECTED_SCHEMA.items():
        if expected_type == "datetime":
            try:
                # Attempt to convert to datetime
                pd.to_datetime(df[column])
            except Exception as e:
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
                    result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
                
        elif expected_type == "float":
            try:
                # Check if values can be converted to float
                df[column].astype(float)
            except Exception as e:
                result["type_errors"].append(f"{column} contains non-numeric values")
                result["is_valid"] = False
                
                # Store problematic values
                problematic_rows = []
                for idx, value in df[column].items():
                    try:
                        float(value)
                    except:
                        problematic_rows.append((idx, value))
                
                if problematic_rows:
                    result["problematic_values"][column] = problematic_rows[:10]  # Limit to first 10
    
    return result

def transform_data(df: pd.DataFrame, schema_type: str = "main") -> pd.DataFrame:
    """
    Transforms the dataframe to match the expected schema.
    
    Args:
        df: The dataframe to transform
        schema_type: Either "main" or "planned" to specify which schema to use
        
    Returns:
        Transformed dataframe
    """
    # Select schema based on type
    if schema_type == "planned":
        schema = PLANNED_SCHEMA
        optional_cols = PLANNED_OPTIONAL_COLUMNS
    else:
        schema = MAIN_SCHEMA
        optional_cols = MAIN_OPTIONAL_COLUMNS
    # Create a copy to avoid modifying the original
    transformed_df = df.copy()
    
    # Convert columns to the correct types
    for column, expected_type in schema.items():
        if column in transformed_df.columns:
            if expected_type == "datetime":
                # Ensure dates are properly converted to pandas datetime
                transformed_df[column] = pd.to_datetime(transformed_df[column])
            elif expected_type == "float":
                transformed_df[column] = pd.to_numeric(transformed_df[column], errors='coerce')
            elif expected_type == "string":
                transformed_df[column] = transformed_df[column].astype(str)
        else:
            # Add missing optional columns with default values
            if column in optional_cols:
                if expected_type == "float":
                    transformed_df[column] = 0.0
                elif expected_type == "string":
                    transformed_df[column] = ""
    
    return transformed_df

def display_validation_results(validation_results: Dict[str, Any], schema_type: str = "main") -> None:
    """
    Displays validation results in the Streamlit app.
    
    Args:
        validation_results: Dictionary with validation results
        schema_type: Type of schema being validated ("main" or "planned")
    """
    data_type = "Planned hours CSV" if schema_type == "planned" else "CSV"
    
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


def load_schema_from_yaml(yaml_file: str = "arkemy_schema_filtered.yaml") -> Optional[Dict[str, str]]:
    """
    Load schema from YAML file for future flexibility.
    
    Args:
        yaml_file: Path to YAML schema file
        
    Returns:
        Dictionary mapping field names to data types, or None if not available
    """
    if not YAML_AVAILABLE:
        return None
    
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        # Try looking in parent directory
        yaml_path = Path("..") / yaml_file
        if not yaml_path.exists():
            return None
    
    try:
        with open(yaml_path, 'r') as f:
            schema_data = yaml.safe_load(f)
        
        # Extract field types from YAML
        field_types = schema_data.get('field_types', {})
        
        # Convert YAML types to validation types
        type_mapping = {
            'date': 'datetime',
            'string': 'string', 
            'float': 'float',
            'integer': 'float'  # Treat integers as floats for validation
        }
        
        schema = {}
        for field, yaml_type in field_types.items():
            if yaml_type in type_mapping:
                schema[field] = type_mapping[yaml_type]
        
        return schema
        
    except Exception as e:
        print(f"Warning: Could not load schema from {yaml_file}: {e}")
        return None


def get_active_schema() -> Dict[str, str]:
    """
    Get the active schema, preferring YAML if available, falling back to hardcoded.
    
    Returns:
        Dictionary mapping field names to data types
    """
    yaml_schema = load_schema_from_yaml()
    if yaml_schema:
        return yaml_schema
    else:
        return EXPECTED_SCHEMA


# Backward compatibility aliases
def validate_csv_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Backward compatibility wrapper for main data validation."""
    return validate_schema(df, "main")

def transform_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Backward compatibility wrapper for main data transformation."""
    return transform_data(df, "main")

# New planned data functions matching old planned_validation.py interface
def validate_planned_schema(df: pd.DataFrame) -> Dict[str, Any]:
    """Validate planned data schema."""
    return validate_schema(df, "planned")

def transform_planned_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Transform planned data."""
    return transform_data(df, "planned")

def display_planned_validation_results(validation_results: Dict[str, Any]) -> None:
    """Display planned data validation results."""
    return display_validation_results(validation_results, "planned")
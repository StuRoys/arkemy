# utils/schema_manager.py
"""
Schema Manager for dynamic data validation and loading based on YAML configuration.

This module provides a centralized way to manage data schemas, validation rules,
and record type handling without hardcoding schemas in Python.
"""

import yaml
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

logger = logging.getLogger(__name__)

class SchemaManager:
    """
    Manages schema configuration, validation, and data type handling
    based on YAML schema definitions.
    """

    def __init__(self, schema_path: str = "utils/arkemy_schema.yaml"):
        """
        Initialize SchemaManager with YAML schema file.

        Args:
            schema_path: Path to YAML schema file
        """
        self.schema_path = schema_path
        self._schema = None
        self._load_schema()

    @staticmethod
    @st.cache_data
    def _load_schema_cached(schema_path: str, _file_mtime: float = None) -> Dict[str, Any]:
        """
        Load schema from YAML file with caching for performance.

        Args:
            schema_path: Path to schema file
            _file_mtime: File modification time for cache busting

        Returns:
            Parsed schema dictionary
        """
        try:
            schema_file = Path(schema_path)
            if not schema_file.exists():
                # Try relative to current working directory
                schema_file = Path.cwd() / schema_path
                if not schema_file.exists():
                    raise FileNotFoundError(f"Schema file not found: {schema_path}")

            with open(schema_file, 'r', encoding='utf-8') as f:
                schema = yaml.safe_load(f)

            # Validate basic schema structure
            required_sections = ['schema_version', 'settings', 'record_types', 'fields']
            for section in required_sections:
                if section not in schema:
                    raise ValueError(f"Schema missing required section: {section}")

            logger.info(f"Loaded schema version {schema.get('schema_version')} from {schema_file}")
            return schema

        except Exception as e:
            logger.error(f"Error loading schema from {schema_path}: {e}")
            raise

    def _load_schema(self):
        """Load schema with file modification time for cache busting."""
        try:
            schema_file = Path(self.schema_path)
            if not schema_file.exists():
                schema_file = Path.cwd() / self.schema_path

            file_mtime = schema_file.stat().st_mtime if schema_file.exists() else 0
            self._schema = self._load_schema_cached(str(schema_file), file_mtime)
        except Exception as e:
            logger.error(f"Failed to load schema: {e}")
            # Fallback to empty schema
            self._schema = {
                'schema_version': '0.0',
                'settings': {'record_type_column': 'record_type'},
                'record_types': {},
                'fields': {}
            }

    @property
    def schema(self) -> Dict[str, Any]:
        """Get the loaded schema."""
        return self._schema

    def get_record_types(self) -> List[str]:
        """Get list of available record types."""
        return list(self._schema.get('record_types', {}).keys())

    def get_record_type_config(self, record_type: str) -> Dict[str, Any]:
        """
        Get configuration for a specific record type.

        Args:
            record_type: Name of record type

        Returns:
            Record type configuration dictionary
        """
        return self._schema.get('record_types', {}).get(record_type, {})

    def get_field_config(self, field_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific field.

        Args:
            field_name: Name of field

        Returns:
            Field configuration dictionary
        """
        return self._schema.get('fields', {}).get(field_name, {})

    def get_required_fields(self, record_type: str) -> List[str]:
        """
        Get required fields for a record type.

        Args:
            record_type: Name of record type

        Returns:
            List of required field names
        """
        config = self.get_record_type_config(record_type)
        return config.get('required_fields', [])

    def get_optional_fields(self, record_type: str) -> List[str]:
        """
        Get optional fields for a record type.

        Args:
            record_type: Name of record type

        Returns:
            List of optional field names
        """
        config = self.get_record_type_config(record_type)
        return config.get('optional_fields', [])

    def get_all_fields(self, record_type: str) -> List[str]:
        """
        Get all fields (required + optional) for a record type.

        Args:
            record_type: Name of record type

        Returns:
            List of all field names
        """
        return self.get_required_fields(record_type) + self.get_optional_fields(record_type)

    def get_pandas_dtype(self, field_name: str) -> str:
        """
        Get pandas dtype for a field.

        Args:
            field_name: Name of field

        Returns:
            Pandas dtype string
        """
        field_config = self.get_field_config(field_name)
        field_type = field_config.get('type', 'string')

        # Map schema types to pandas types
        type_mapping = self._schema.get('pandas_type_mapping', {
            'string': 'string',
            'integer': 'Int64',
            'float': 'float64',
            'datetime': 'datetime64[ns]',
            'boolean': 'boolean'
        })

        return type_mapping.get(field_type, 'string')

    def validate_record_type_data(self, df: pd.DataFrame, record_type: str) -> Dict[str, Any]:
        """
        Validate dataframe against record type schema.

        Args:
            df: DataFrame to validate
            record_type: Record type to validate against

        Returns:
            Validation results dictionary
        """
        results = {
            'is_valid': True,
            'missing_required_fields': [],
            'type_errors': [],
            'value_errors': [],
            'warnings': []
        }

        if record_type not in self.get_record_types():
            results['is_valid'] = False
            results['type_errors'].append(f"Unknown record type: {record_type}")
            return results

        # Check required fields
        required_fields = self.get_required_fields(record_type)
        for field in required_fields:
            if field not in df.columns:
                results['missing_required_fields'].append(field)
                results['is_valid'] = False

        # Validate field types and constraints
        for field in df.columns:
            field_config = self.get_field_config(field)
            if not field_config:
                if not self._schema.get('validation', {}).get('allow_unknown_fields', True):
                    results['warnings'].append(f"Unknown field: {field}")
                continue

            # Type validation
            expected_type = field_config.get('type', 'string')
            if expected_type == 'datetime':
                try:
                    pd.to_datetime(df[field], errors='raise')
                except Exception:
                    results['type_errors'].append(f"{field}: Invalid datetime format")
                    results['is_valid'] = False
            elif expected_type in ['integer', 'float']:
                try:
                    pd.to_numeric(df[field], errors='raise')
                except Exception:
                    results['type_errors'].append(f"{field}: Non-numeric values found")
                    results['is_valid'] = False

            # Value constraints
            if expected_type in ['integer', 'float']:
                min_val = field_config.get('min_value')
                max_val = field_config.get('max_value')

                if min_val is not None:
                    invalid_count = (df[field] < min_val).sum()
                    if invalid_count > 0:
                        results['value_errors'].append(f"{field}: {invalid_count} values below minimum {min_val}")

                if max_val is not None:
                    invalid_count = (df[field] > max_val).sum()
                    if invalid_count > 0:
                        results['value_errors'].append(f"{field}: {invalid_count} values above maximum {max_val}")

        # Set overall validity
        if results['value_errors']:
            results['is_valid'] = False

        return results

    def transform_dataframe(self, df: pd.DataFrame, record_type: str) -> pd.DataFrame:
        """
        Transform dataframe to match schema requirements.

        Args:
            df: DataFrame to transform
            record_type: Record type to transform for

        Returns:
            Transformed DataFrame
        """
        transformed_df = df.copy()

        # Convert data types based on schema
        for field in transformed_df.columns:
            field_config = self.get_field_config(field)
            if not field_config:
                continue

            field_type = field_config.get('type', 'string')

            try:
                if field_type == 'datetime':
                    transformed_df[field] = pd.to_datetime(transformed_df[field], errors='coerce')
                elif field_type == 'integer':
                    transformed_df[field] = pd.to_numeric(transformed_df[field], errors='coerce').astype('Int64')
                elif field_type == 'float':
                    transformed_df[field] = pd.to_numeric(transformed_df[field], errors='coerce')
                elif field_type == 'string':
                    transformed_df[field] = transformed_df[field].astype('string')
                elif field_type == 'boolean':
                    transformed_df[field] = transformed_df[field].astype('boolean')
            except Exception as e:
                logger.warning(f"Could not convert {field} to {field_type}: {e}")

        # Apply legacy column mapping for backward compatibility
        transformed_df = self.apply_legacy_column_mapping(transformed_df, record_type)

        return transformed_df

    def apply_legacy_column_mapping(self, df: pd.DataFrame, record_type: str) -> pd.DataFrame:
        """
        Apply legacy column name mapping for backward compatibility.

        The current dashboard expects snake_case column names, so we keep those as-is.
        No column renaming needed - the data already has the correct names.

        Args:
            df: DataFrame to map
            record_type: Record type

        Returns:
            DataFrame with compatible column names
        """
        # No mapping needed - keep all column names as they are
        # The dashboard code expects: record_date, person_name, project_number, etc.
        # which matches what the data already has
        return df

    def filter_dataframe_by_record_type(self, df: pd.DataFrame, record_type: str) -> pd.DataFrame:
        """
        Filter dataframe to specific record type.

        Args:
            df: DataFrame to filter
            record_type: Record type to filter for

        Returns:
            Filtered DataFrame
        """
        record_type_column = self._schema.get('settings', {}).get('record_type_column', 'record_type')

        if record_type_column not in df.columns:
            logger.warning(f"Record type column '{record_type_column}' not found in data")
            return df

        return df[df[record_type_column] == record_type].copy()

    def get_session_state_target(self, record_type: str) -> str:
        """
        Get session state variable name for record type.

        Args:
            record_type: Record type name

        Returns:
            Session state variable name
        """
        config = self.get_record_type_config(record_type)
        return config.get('session_state_target', 'transformed_df')

    def display_validation_results(self, results: Dict[str, Any], record_type: str) -> None:
        """
        Display validation results in Streamlit UI.

        Args:
            results: Validation results dictionary
            record_type: Record type being validated
        """
        record_config = self.get_record_type_config(record_type)
        display_name = record_config.get('display_name', record_type)

        if results['is_valid']:
            st.success(f"✅ {display_name} data validation passed!")
        else:
            st.error(f"❌ {display_name} data validation failed")

            if results['missing_required_fields']:
                st.error("Missing required fields:")
                for field in results['missing_required_fields']:
                    field_config = self.get_field_config(field)
                    description = field_config.get('description', 'No description')
                    st.error(f"  • **{field}**: {description}")

            if results['type_errors']:
                st.error("Type errors:")
                for error in results['type_errors']:
                    st.error(f"  • {error}")

            if results['value_errors']:
                st.warning("Value constraint violations:")
                for error in results['value_errors']:
                    st.warning(f"  • {error}")

        if results['warnings']:
            with st.expander("Validation Warnings"):
                for warning in results['warnings']:
                    st.warning(warning)

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get summary information about the loaded schema.

        Returns:
            Schema summary dictionary
        """
        return {
            'version': self._schema.get('schema_version', 'Unknown'),
            'description': self._schema.get('description', ''),
            'record_types': list(self._schema.get('record_types', {}).keys()),
            'total_fields': len(self._schema.get('fields', {})),
            'schema_path': self.schema_path
        }
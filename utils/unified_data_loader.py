# utils/unified_data_loader.py
"""
Unified data loading system using schema-driven validation and record type filtering.

This module replaces the complex manifest system with a simple, schema-driven approach
that can handle unified parquet files with multiple record types.
"""

import pandas as pd
import streamlit as st
import os
import gc
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from utils.schema_manager import SchemaManager

logger = logging.getLogger(__name__)

class UnifiedDataLoader:
    """
    Loads and processes parquet files using schema-driven validation and record type filtering.
    """

    def __init__(self, schema_path: str = "utils/arkemy_schema.yaml"):
        """
        Initialize UnifiedDataLoader with schema manager.

        Args:
            schema_path: Path to YAML schema file
        """
        self.schema_manager = SchemaManager(schema_path)

    def detect_file_currency(self, file_path: str) -> str:
        """
        Extract currency from filename.

        Args:
            file_path: Path to data file

        Returns:
            Currency code (lowercase)
        """
        filename = os.path.basename(file_path).upper()
        supported_currencies = ['NOK', 'USD', 'EUR', 'GBP', 'SEK', 'DKK']

        for currency in supported_currencies:
            if currency in filename:
                return currency.lower()

        return 'nok'  # Default fallback

    @staticmethod
    @st.cache_data
    def load_parquet_file_cached(file_path: str, _file_mtime: float = None) -> pd.DataFrame:
        """
        Load parquet file with caching.

        Args:
            file_path: Path to parquet file
            _file_mtime: File modification time for cache busting

        Returns:
            Loaded DataFrame
        """
        try:
            df = pd.read_parquet(file_path, engine='pyarrow')
            logger.info(f"Loaded parquet file: {file_path} ({df.shape[0]} rows, {df.shape[1]} columns)")
            return df
        except Exception as e:
            logger.error(f"Error loading parquet file {file_path}: {e}")
            raise

    def analyze_data_structure(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze data structure to determine loading strategy.

        Args:
            df: DataFrame to analyze

        Returns:
            Analysis results dictionary
        """
        analysis = {
            'has_record_type': False,
            'record_types': [],
            'record_type_counts': {},
            'loading_strategy': 'single_type',
            'total_rows': len(df),
            'columns': list(df.columns)
        }

        # Check for record type column
        record_type_column = self.schema_manager.schema.get('settings', {}).get('record_type_column', 'record_type')

        if record_type_column in df.columns:
            analysis['has_record_type'] = True
            analysis['record_types'] = df[record_type_column].unique().tolist()
            analysis['record_type_counts'] = df[record_type_column].value_counts().to_dict()
            analysis['loading_strategy'] = 'multi_type'

        return analysis

    def process_record_type(self, df: pd.DataFrame, record_type: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
        """
        Process data for a specific record type.

        Args:
            df: Full DataFrame
            record_type: Record type to process

        Returns:
            Tuple of (processed_dataframe, validation_results)
        """
        # Filter data for this record type
        filtered_df = self.schema_manager.filter_dataframe_by_record_type(df, record_type)

        if filtered_df.empty:
            return filtered_df, {'is_valid': True, 'warnings': [f'No data found for record type: {record_type}']}

        # Validate against schema
        validation_results = self.schema_manager.validate_record_type_data(filtered_df, record_type)

        # Transform data types
        if validation_results['is_valid']:
            transformed_df = self.schema_manager.transform_dataframe(filtered_df, record_type)
        else:
            transformed_df = filtered_df

        return transformed_df, validation_results

    def load_unified_data(self, file_path: str, show_debug: bool = False, silent_mode: bool = False) -> Dict[str, Any]:
        """
        Main function to load and process unified parquet data.

        Args:
            file_path: Path to parquet file
            show_debug: Whether to show debug information
            silent_mode: Whether to suppress user-facing messages

        Returns:
            Loading results dictionary
        """
        results = {
            'success': False,
            'currency': 'nok',
            'analysis': {},
            'processed_data': {},
            'validation_results': {},
            'error': None
        }

        try:
            # Validate file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")

            # Extract currency from filename
            results['currency'] = self.detect_file_currency(file_path)

            # Load file with cache busting
            file_mtime = os.path.getmtime(file_path)
            df = self.load_parquet_file_cached(file_path, file_mtime)

            # Analyze data structure
            analysis = self.analyze_data_structure(df)
            results['analysis'] = analysis

            if show_debug:
                st.info("📊 **Data Analysis Results**")
                st.json(analysis)

            # Process data based on analysis
            if analysis['loading_strategy'] == 'multi_type':
                # Multi-record-type file
                if not silent_mode:
                    st.info(f"🔍 Detected unified file with {len(analysis['record_types'])} record types")

                for record_type in analysis['record_types']:
                    if record_type in self.schema_manager.get_record_types():
                        processed_df, validation_results = self.process_record_type(df, record_type)

                        results['processed_data'][record_type] = processed_df
                        results['validation_results'][record_type] = validation_results

                        # Display validation results (only if not in silent mode)
                        if not silent_mode:
                            self.schema_manager.display_validation_results(validation_results, record_type)

                        # Store in session state
                        session_target = self.schema_manager.get_session_state_target(record_type)
                        st.session_state[session_target] = processed_df

                        # Set loading flags
                        if record_type == 'time_record':
                            st.session_state.csv_loaded = True
                        elif record_type == 'planned_record':
                            st.session_state.planned_csv_loaded = True

                        if show_debug and not silent_mode:
                            st.success(f"✅ Processed {record_type}: {len(processed_df)} records → `session_state.{session_target}`")

            else:
                # Single-record-type file (fallback to default)
                default_type = self.schema_manager.schema.get('settings', {}).get('default_record_type', 'time_record')
                if not silent_mode:
                    st.info(f"📁 Processing as single-type file (assumed: {default_type})")

                processed_df, validation_results = self.process_record_type(df, default_type)
                results['processed_data'][default_type] = processed_df
                results['validation_results'][default_type] = validation_results

                # Display validation results (only if not in silent mode)
                if not silent_mode:
                    self.schema_manager.display_validation_results(validation_results, default_type)

                # Store in session state
                session_target = self.schema_manager.get_session_state_target(default_type)
                st.session_state[session_target] = processed_df
                st.session_state.csv_loaded = True

            # Set global session state
            st.session_state.currency = results['currency']
            st.session_state.currency_selected = True

            # Clean up memory
            del df
            gc.collect()

            results['success'] = True

        except Exception as e:
            logger.error(f"Error loading unified data: {e}")
            results['error'] = str(e)
            st.error(f"❌ Error loading data: {e}")

        return results

    def get_schema_info(self) -> None:
        """Display schema information in Streamlit UI."""
        schema_info = self.schema_manager.get_schema_info()

        with st.expander("📋 Schema Information"):
            col1, col2 = st.columns(2)

            with col1:
                st.metric("Schema Version", schema_info['version'])
                st.metric("Total Fields", schema_info['total_fields'])

            with col2:
                st.metric("Record Types", len(schema_info['record_types']))
                st.info(f"**Path**: `{schema_info['schema_path']}`")

            st.write("**Available Record Types:**")
            for record_type in schema_info['record_types']:
                config = self.schema_manager.get_record_type_config(record_type)
                required_count = len(config.get('required_fields', []))
                optional_count = len(config.get('optional_fields', []))

                st.write(f"• **{record_type}**: {config.get('description', 'No description')}")
                st.write(f"  - Required fields: {required_count}, Optional fields: {optional_count}")

def scan_volume_for_parquet_files(volume_paths: List[str] = None) -> Tuple[List[Dict[str, Any]], str]:
    """
    Scan volume directories for parquet files with metadata.

    Args:
        volume_paths: List of paths to scan (defaults to ["/data", "./data"])

    Returns:
        Tuple of (file info list, successful path used)
    """
    if volume_paths is None:
        volume_paths = ["/data", "./data"]

    for volume_path in volume_paths:
        files_info = []

        if not os.path.exists(volume_path):
            continue

        try:
            for filename in os.listdir(volume_path):
                file_path = os.path.join(volume_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith(('.parquet', '.pq')):
                    stat = os.stat(file_path)
                    files_info.append({
                        'filename': filename,
                        'path': file_path,
                        'size': stat.st_size,
                        'modified': stat.st_mtime,
                        'size_mb': round(stat.st_size / (1024 * 1024), 2),
                        'source_path': volume_path,
                    })

            if files_info:
                # Sort by modification time (newest first)
                files_info.sort(key=lambda x: x['modified'], reverse=True)
                logger.info(f"Found {len(files_info)} parquet file(s) in {volume_path}")
                return files_info, volume_path

        except Exception as e:
            logger.error(f"Error scanning volume {volume_path}: {e}")
            continue

    return [], ""

def load_data_hybrid(volume_paths: List[str] = None, show_debug: bool = False, silent_mode: bool = False) -> Dict[str, Any]:
    """
    Hybrid data loading: check volume paths first, then allow manual upload.

    Args:
        volume_paths: List of paths to scan (defaults to ["/data", "./data"])
        show_debug: Whether to show debug information
        silent_mode: Whether to suppress user-facing messages

    Returns:
        Loading results dictionary with volume_files info
    """
    if volume_paths is None:
        volume_paths = ["/data", "./data"]

    results = {
        'success': False,
        'loading_method': 'none',
        'volume_files': [],
        'auto_loaded_file': None,
        'data_source_path': '',
        'currency': 'nok',
        'analysis': {},
        'processed_data': {},
        'validation_results': {},
        'error': None
    }

    # Scan volume paths for parquet files
    volume_files, successful_path = scan_volume_for_parquet_files(volume_paths)
    results['volume_files'] = volume_files
    results['data_source_path'] = successful_path

    if volume_files:
        # Auto-load the newest file
        newest_file = volume_files[0]
        results['loading_method'] = 'auto_volume'
        results['auto_loaded_file'] = newest_file

        # Display source information (only if not in silent mode)
        if not silent_mode:
            source_type = "production volume" if successful_path == "/data" else "local directory"
            st.info(f"🔍 **Auto-Loading Data**: Found {len(volume_files)} parquet file(s) in {source_type} (`{successful_path}`)")
            st.info(f"📁 **Loading**: `{newest_file['filename']}` ({newest_file['size_mb']} MB)")

            if len(volume_files) > 1:
                with st.expander(f"ℹ️ Other files available ({len(volume_files)-1})"):
                    for file_info in volume_files[1:]:
                        st.write(f"• `{file_info['filename']}` ({file_info['size_mb']} MB)")

        # Load the file using unified loader
        loader = UnifiedDataLoader()
        if show_debug and not silent_mode:
            loader.get_schema_info()

        load_results = loader.load_unified_data(newest_file['path'], show_debug, silent_mode)

        # Merge results
        results.update(load_results)
        results['loading_method'] = 'auto_volume'

    else:
        results['loading_method'] = 'upload_required'
        if not silent_mode:
            attempted_paths = ", ".join([f"`{path}`" for path in volume_paths])
            st.info(f"📂 **No parquet files found** in {attempted_paths}. Please upload your data file below.")

    return results

def load_data_from_upload(uploaded_file, show_debug: bool = False) -> Dict[str, Any]:
    """
    Load data from uploaded file using unified loader.

    Args:
        uploaded_file: Streamlit uploaded file object
        show_debug: Whether to show debug information

    Returns:
        Loading results dictionary
    """
    import tempfile

    # Save uploaded file to temporary location
    with tempfile.NamedTemporaryFile(delete=False, suffix='.parquet') as tmp_file:
        tmp_file.write(uploaded_file.getvalue())
        tmp_path = tmp_file.name

    try:
        # Load using unified loader
        loader = UnifiedDataLoader()
        if show_debug:
            loader.get_schema_info()

        results = loader.load_unified_data(tmp_path, show_debug)
        results['loading_method'] = 'upload'
        results['uploaded_filename'] = uploaded_file.name

        return results

    finally:
        # Clean up temporary file
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

def load_data_with_schema(file_path: str, show_debug: bool = False) -> Dict[str, Any]:
    """
    Convenience function to load data using the unified loader.

    Args:
        file_path: Path to parquet file
        show_debug: Whether to show debug information

    Returns:
        Loading results dictionary
    """
    loader = UnifiedDataLoader()

    # Display schema info if debug mode
    if show_debug:
        loader.get_schema_info()

    return loader.load_unified_data(file_path, show_debug)
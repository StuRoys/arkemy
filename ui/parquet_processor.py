# ui/parquet_processor.py
import streamlit as st
import pandas as pd
import gc
import os
import re
import yaml
import glob
import time
import logging
from utils.data_validation import (
    validate_csv_schema, transform_csv, display_validation_results,
    validate_planned_schema, transform_planned_csv, display_planned_validation_results
)
from utils.person_reference import enrich_person_data
from utils.project_reference import enrich_project_data

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def is_debug_mode():
    """Check if debug mode is enabled via environment variable or session state."""
    # Check environment variable first (production override)
    if os.getenv('ARKEMY_DEBUG', '').lower() in ('true', '1', 'yes'):
        return True
    # Fall back to session state for development
    return st.session_state.get('debug_mode', False)
from utils.planned_processors import calculate_planned_summary_metrics

# Import capacity-related functions
from utils.capacity_validation import (
    validate_schedule_schema, validate_absence_schema, validate_capacity_config_schema, validate_weekly_source_schema,
    display_schedule_validation_results, display_absence_validation_results, 
    display_capacity_config_validation_results, display_weekly_source_validation_results,
    load_client_absence_config
)
from utils.weekly_data_transformer import (
    transform_weekly_to_schedule, transform_weekly_to_absence, load_capacity_config_from_dataframe,
    create_capacity_summary, validate_weekly_data_completeness, get_capacity_processing_summary
)

# Cache management utilities
def get_file_mtime(file_path):
    """Get file modification time, return 0 if file doesn't exist"""
    try:
        return os.path.getmtime(file_path)
    except OSError:
        return 0

def clear_manifest_cache():
    """Clear all manifest-related cached data"""
    # Clear the specific cached functions
    load_data_manifest.clear()
    get_manifest_data_sources.clear()
    read_parquet_from_manifest.clear()
    
    # Also clear session state cache info if it exists
    if 'manifest_debug_info' in st.session_state:
        st.session_state.manifest_debug_info['cache_cleared'] = time.time()

# Add a cached function for reading Parquet data by source
@st.cache_data
def read_parquet_data_from_path(parquet_path, data_source, columns=None):
    """
    Reads data from a Parquet file for a specific data source with optional column selection.
    
    Args:
        parquet_path: Path to the Parquet file
        data_source: The data source to filter by ('main', 'planned', etc.)
        columns: Optional list of columns to load
        
    Returns:
        DataFrame containing the requested data
    """
    # Default columns to load for each data source if not specified
    if columns is None:
        # Always include data_source column for filtering
        if data_source == 'main':
            # Main data requires most columns
            columns = None  # Load all columns for main data to be safe
        elif data_source == 'planned':
            # Planned data needs fewer columns (using snake_case column names)
            columns = ['data_source', 'record_date', 'person_name', 'project_number', 'project_name', 'planned_hours', 'planned_hourly_rate']
        elif data_source == 'person_reference':
            # Person reference data needs minimal columns
            columns = ['data_source', 'Person', 'Person type']
        elif data_source == 'project_reference':
            # Project reference data - load all columns as we don't know which metadata is needed
            columns = None
        elif data_source in ['schedule', 'absence', 'capacity_config', 'weekly_source']:
            # Capacity-related data sources - load all columns to handle dynamic schemas
            columns = None
    
    try:
        # Use PyArrow engine for better performance
        if columns is None:
            # Read all columns
            df = pd.read_parquet(parquet_path, engine='pyarrow')
        else:
            # Read only specified columns
            df = pd.read_parquet(parquet_path, engine='pyarrow', columns=columns)
        
        # Filter by data source
        if 'data_source' in df.columns:
            filtered_df = df[df['data_source'] == data_source]
            
            # Drop the data_source column as it's no longer needed
            if 'data_source' in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=['data_source'])
                
            return filtered_df
        else:
            # If data_source column doesn't exist, return empty DataFrame
            return pd.DataFrame()
    except Exception as e:
        # Return empty DataFrame on error
        logger.error(f"Error reading Parquet data for {data_source}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_data_sources_from_path(parquet_path):
    """
    Get available data sources from Parquet file.
    
    Args:
        parquet_path: Path to the Parquet file
        
    Returns:
        List of data sources
    """
    try:
        # Read just the data_source column for efficiency
        df = pd.read_parquet(parquet_path, engine='pyarrow', columns=['data_source'])
        return df['data_source'].unique().tolist()
    except Exception as e:
        logger.error(f"Error getting data sources: {str(e)}")
        return []

# Apply caching to data transformation functions to improve performance
@st.cache_data
def cached_transform_csv(df):
    """Cached wrapper for transform_csv function"""
    return transform_csv(df)

@st.cache_data
def cached_transform_planned_csv(df):
    """Cached wrapper for transform_planned_csv function"""
    return transform_planned_csv(df)

@st.cache_data
def cached_enrich_person_data(df, reference_df):
    """Cached wrapper for enrich_person_data function"""
    return enrich_person_data(df, reference_df)

@st.cache_data
def cached_enrich_project_data(df, reference_df):
    """Cached wrapper for enrich_project_data function"""
    return enrich_project_data(df, reference_df)

# Add cached wrappers for capacity functions
@st.cache_data
def cached_transform_weekly_to_schedule(weekly_df):
    """Cached wrapper for transform_weekly_to_schedule function"""
    return transform_weekly_to_schedule(weekly_df)

@st.cache_data
def cached_transform_weekly_to_absence(weekly_df, capacity_config):
    """Cached wrapper for transform_weekly_to_absence function"""
    return transform_weekly_to_absence(weekly_df, capacity_config)

@st.cache_data
def cached_create_capacity_summary(schedule_df, absence_df, capacity_config):
    """Cached wrapper for create_capacity_summary function"""
    return create_capacity_summary(schedule_df, absence_df, capacity_config)

def extract_currency_from_filename(filepath):
    """Extract currency from filename like 'data_NOK.parquet'"""
    filename = os.path.basename(filepath)
    # Look for currency pattern: 3 letters after underscore or dash, before extension or end of filename
    # Try multiple patterns to find currency codes
    patterns = [
        r'[_-]([A-Z]{3})(?:\.[^.]+)?$',  # 3 letters after underscore/dash at end or before extension
        r'[_-]([A-Z]{3})[_-]',           # 3 letters between underscores/dashes
    ]
    
    filename_upper = filename.upper()
    supported = ['nok', 'usd', 'eur', 'gbp', 'sek', 'dkk']
    
    for pattern in patterns:
        match = re.search(pattern, filename_upper)
        if match:
            currency = match.group(1).lower()
            if currency in supported:
                return currency
    
    return None

def extract_client_from_filename(filepath):
    """Extract client ID from filename"""
    filename = os.path.basename(filepath).lower()
    if 'nuno' in filename:
        return 'nuno'
    # Add other clients here as needed
    return None

def process_parquet_data_from_path(parquet_path):
    """
    Processes a Parquet file from file system path that contains combined datasets.
    
    Args:
        parquet_path: Path to the Parquet file
    """
    try:
        # Extract and set currency from filename first
        currency = extract_currency_from_filename(parquet_path)
        if currency:
            st.session_state.currency = currency
            st.session_state.currency_selected = True
        else:
            st.session_state.currency = 'nok'  # fallback
            st.session_state.currency_selected = True
        
        # Validate file exists
        if not os.path.exists(parquet_path):
            st.error(f"File not found: {parquet_path}")
            return
        
        # Extract client ID from filename
        client_id = extract_client_from_filename(parquet_path)
        
        # Skip capacity config loading for simple parquet loading
        print("🔍 TERMINAL: Skipping capacity config loading for simplified loading")
        
        # Skip data_source column requirement for simple loading
        print("🔍 TERMINAL: Loading parquet file without data_source column requirement")
        
        # Store debug information in session state  
        st.session_state.data_loading_method = "single_file"
        st.session_state.manifest_debug_info = {
            'parquet_path': parquet_path,
            'data_sources': ['main'],  # Simple loading assumes main data source
            'currency': currency,
            'client_id': client_id
        }
        
        # Load parquet file directly without data_source filtering
        print("🔍 TERMINAL: Loading parquet file directly")
        
        try:
            main_data = pd.read_parquet(parquet_path, engine='pyarrow')
            print(f"🔍 TERMINAL: Loaded {main_data.shape[0]} rows, {main_data.shape[1]} columns")
        except Exception as e:
            st.error(f"❌ Error loading parquet file: {str(e)}")
            return
        
        # Process main data
        if main_data.empty:
            st.error("No main project data found in the Parquet file.")
            return
        
        # Validate main data schema (silent for clean UI)
        validation_results = validate_csv_schema(main_data)
        print(f"🔍 TERMINAL: Schema validation - Valid: {validation_results['is_valid']}")
        # display_validation_results(validation_results)  # Commented out for clean UI
        
        # If the data is valid, proceed with transformation and store in session state
        if validation_results["is_valid"]:
            transformed_df = cached_transform_csv(main_data)
            st.session_state.transformed_df = transformed_df
            st.session_state.csv_loaded = True
            
            # Clean up memory
            del main_data
            gc.collect()
            
            # End processing here for simplified loading - skip all optional data
            print(f"🔍 TERMINAL: Main data loaded successfully!")
            print(f"🔍 TERMINAL: Loaded {transformed_df.shape[0]} rows, {transformed_df.shape[1]} columns into session state")
            print(f"🔍 TERMINAL: Session state - csv_loaded: {st.session_state.csv_loaded}")
            print(f"🔍 TERMINAL: Currency: {st.session_state.currency}")
            return
            
    except Exception as e:
        st.error(f"Error processing the Parquet file: {str(e)}")
        # Store error in debug info
        st.session_state.data_loading_method = "single_file_failed"
        st.session_state.manifest_debug_info = {
            'error': str(e),
            'parquet_path': parquet_path
        }

def process_capacity_data_sources(parquet_path, data_sources, capacity_config):
    """
    Process all capacity-related data sources.
    
    Args:
        parquet_path: Path to the parquet file
        data_sources: List of available data sources
        capacity_config: Parsed capacity configuration (can be None)
    """
    
    # Check for capacity data sources
    has_schedule = 'schedule' in data_sources
    has_absence = 'absence' in data_sources  
    has_weekly_source = 'weekly_source' in data_sources
    
    if not (has_schedule or has_absence or has_weekly_source):
        # No capacity data sources found
        return
    
    st.subheader("Capacity Data Processing")
    
    # Initialize capacity dataframes
    schedule_df = pd.DataFrame()
    absence_df = pd.DataFrame()
    
    # Process weekly source data (your raw format)
    if has_weekly_source:
        weekly_data = read_parquet_data_from_path(parquet_path, 'weekly_source')
        st.session_state.weekly_source_df = weekly_data  # Add this line

        
        if not weekly_data.empty:
            # Validate weekly source data
            weekly_validation_results = validate_weekly_source_schema(weekly_data)
            display_weekly_source_validation_results(weekly_validation_results)
            
            if weekly_validation_results["is_valid"]:
                # Validate data completeness against config if available
                if capacity_config:
                    completeness_results = validate_weekly_data_completeness(weekly_data, capacity_config)
                    
                    if not completeness_results["is_complete"]:
                        st.warning("Weekly data validation warnings:")
                        for warning in completeness_results["warnings"]:
                            st.warning(f"• {warning}")
                        
                        if completeness_results["suggestions"]:
                            st.info("Suggestions:")
                            for suggestion in completeness_results["suggestions"]:
                                st.info(f"• {suggestion}")
                
                # Transform weekly data to schedule format
                schedule_df = cached_transform_weekly_to_schedule(weekly_data)
                st.success(f"Transformed weekly data to schedule format: {len(schedule_df)} records")
                
                # Transform weekly data to absence format (if config available)
                if capacity_config:
                    absence_df = cached_transform_weekly_to_absence(weekly_data, capacity_config)
                    st.success(f"Transformed weekly data to absence format: {len(absence_df)} records")
                else:
                    st.warning("Capacity configuration not available - absence data not processed")
        
        # Clean up memory
        del weekly_data
        gc.collect()
    
    # Process direct schedule data source (if separate from weekly)
    elif has_schedule:
        schedule_data = read_parquet_data_from_path(parquet_path, 'schedule')
        
        if not schedule_data.empty:
            schedule_validation_results = validate_schedule_schema(schedule_data)
            display_schedule_validation_results(schedule_validation_results)
            
            if schedule_validation_results["is_valid"]:
                schedule_df = schedule_data
                st.success(f"Loaded schedule data: {len(schedule_df)} records")
        
        # Clean up memory
        del schedule_data
        gc.collect()
    
    # Process direct absence data source (if separate from weekly)
    if has_absence and absence_df.empty:  # Only if not already processed from weekly
        absence_data = read_parquet_data_from_path(parquet_path, 'absence')
        
        if not absence_data.empty:
            absence_validation_results = validate_absence_schema(absence_data)
            display_absence_validation_results(absence_validation_results)
            
            if absence_validation_results["is_valid"]:
                absence_df = absence_data
                st.success(f"Loaded absence data: {len(absence_df)} records")
        
        # Clean up memory
        del absence_data
        gc.collect()
    
    # Store capacity data in session state and create summary
    if not schedule_df.empty:
        st.session_state.schedule_df = schedule_df
        st.session_state.schedule_loaded = True
        
        if not absence_df.empty:
            st.session_state.absence_df = absence_df
            st.session_state.absence_loaded = True
        
        # Create capacity summary if we have required data
        if capacity_config:
            capacity_summary_df = cached_create_capacity_summary(schedule_df, absence_df, capacity_config)
            st.session_state.capacity_summary_df = capacity_summary_df
            st.session_state.capacity_summary_loaded = True
            
            # Display processing summary
            processing_summary = get_capacity_processing_summary(schedule_df, absence_df, capacity_config)
            
            with st.expander("Capacity Processing Summary"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Schedule Records", processing_summary["schedule_records"])
                    st.metric("Unique Persons", processing_summary["unique_persons"])
                
                with col2:
                    st.metric("Absence Records", processing_summary["absence_records"]) 
                    st.metric("Total Scheduled Hours", f"{processing_summary['total_scheduled_hours']:,.0f}")
                
                with col3:
                    st.metric("Total Absence Hours", f"{processing_summary['total_absence_hours']:,.0f}")
                    if processing_summary["date_range"]:
                        date_range = processing_summary["date_range"]
                        st.info(f"Period: {date_range['start'].strftime('%Y-%m-%d')} to {date_range['end'].strftime('%Y-%m-%d')}")
            
            st.success("Capacity analysis data is ready for dashboard use.")

@st.cache_data
def load_data_manifest(manifest_path, _file_mtime=None):
    """
    Load and validate data manifest YAML file with cache busting.
    
    Args:
        manifest_path: Path to the data_manifest.yaml file
        _file_mtime: File modification time for cache busting (passed as hidden param)
        
    Returns:
        Dict containing parsed manifest data or None if invalid
    """
    try:
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = yaml.safe_load(f)
        
        # Basic validation
        if not isinstance(manifest, dict):
            st.error("Manifest file must contain a YAML dictionary")
            return None
            
        if 'data_sources' not in manifest:
            st.error("Manifest file must contain 'data_sources' section")
            return None
            
        if 'main' not in manifest['data_sources']:
            st.error("Manifest file must contain 'main' data source")
            return None
            
        return manifest
    except yaml.YAMLError as e:
        st.error(f"Error parsing manifest YAML: {str(e)}")
        return None
    except FileNotFoundError:
        st.error(f"Manifest file not found: {manifest_path}")
        return None
    except Exception as e:
        st.error(f"Error loading manifest: {str(e)}")
        return None

def substitute_version_in_path(file_path, version="adjusted"):
    """
    Substitute {version} placeholder in file path with actual version.
    
    Args:
        file_path: File path potentially containing {version} placeholder
        version: Version string to substitute ("regular" or "adjusted")
        
    Returns:
        File path with version substituted
    """
    # Add underscore prefix to version for file naming convention
    versioned_suffix = f"_{version}"
    result = file_path.replace('{version}', versioned_suffix)
    
    # Debug logging
    if is_debug_mode():
        st.info(f"🐛 Debug - Version substitution: '{file_path}' → '{result}' (version: {version})")
    
    return result

def resolve_file_path(file_path, manifest_dir, allow_absolute=True, fallback_path=None):
    """
    Resolve file path relative to manifest directory, with glob pattern support and fallback.
    
    Args:
        file_path: File path from manifest (can include glob patterns like *.parquet)
        manifest_dir: Directory containing the manifest file
        allow_absolute: Whether to allow absolute paths
        fallback_path: Optional fallback path to try if primary path has no matches
        
    Returns:
        Resolved absolute file path (first match for glob patterns) or None if no matches
    """
    # Force debug output for troubleshooting
    st.info(f"🐛 DEBUG: Resolving file path: '{file_path}' in dir '{manifest_dir}'")
    if fallback_path:
        st.info(f"🐛 DEBUG: Fallback path available: '{fallback_path}'")
    
    # Expand ~ first, before any other processing
    expanded_path = os.path.expanduser(file_path)
    
    if os.path.isabs(expanded_path):
        if allow_absolute:
            resolved_path = expanded_path
        else:
            raise ValueError(f"Absolute paths not allowed: {file_path}")
    else:
        resolved_path = os.path.join(manifest_dir, expanded_path)
    st.info(f"🐛 DEBUG: Resolved to: '{resolved_path}'")
    
    # Check if path contains glob patterns
    if '*' in resolved_path or '?' in resolved_path or '[' in resolved_path:
        st.info(f"🐛 DEBUG: Using glob pattern matching on: '{resolved_path}'")
        
        # Use glob to find matching files
        matches = glob.glob(resolved_path)
        
        st.info(f"🐛 DEBUG: Glob matches found: {len(matches)}")
        for i, match in enumerate(matches[:5]):  # Show first 5 matches
            st.info(f"🐛 DEBUG: Match {i+1}: '{match}'")
        if len(matches) > 5:
            st.info(f"🐛 DEBUG: ... and {len(matches) - 5} more matches")
        
        if matches:
            # Return first match, sorted for consistency
            result = sorted(matches)[0]
            st.info(f"🐛 DEBUG: Selected first match: '{result}'")
            return result
        else:
            st.warning(f"🐛 DEBUG: No files match glob pattern: '{resolved_path}'")
            # Try fallback path if provided
            if fallback_path:
                st.info(f"🐛 DEBUG: Trying fallback path: '{fallback_path}'")
                return resolve_file_path(fallback_path, manifest_dir, allow_absolute, fallback_path=None)
            return None
    else:
        # Regular file path
        exists = os.path.exists(resolved_path)
        if is_debug_mode():
            st.info(f"🐛 Debug - Regular file path, exists: {exists}")
        
        # If primary path doesn't exist, try fallback
        if not exists and fallback_path:
            if is_debug_mode():
                st.info(f"🐛 Debug - Primary path doesn't exist, trying fallback: '{fallback_path}'")
            return resolve_file_path(fallback_path, manifest_dir, allow_absolute, fallback_path=None)
        
        return resolved_path

@st.cache_data
def read_parquet_from_manifest(manifest_path, data_source, data_version, _file_mtime=None):
    """
    Read Parquet data for a specific data source using manifest configuration.
    
    Args:
        manifest_path: Path to the manifest file
        data_source: Data source name to load
        data_version: Version to load ('regular' or 'adjusted')
        _file_mtime: File modification time for cache busting
        
    Returns:
        DataFrame containing the data or empty DataFrame if not found/error
    """
    if is_debug_mode():
        st.info(f"🐛 Debug - Reading '{data_source}' from manifest: '{manifest_path}' (version: {data_version})")
    
    manifest = load_data_manifest(manifest_path, _file_mtime)
    if not manifest:
        if is_debug_mode():
            st.error(f"🐛 Debug - Cannot load manifest for data source '{data_source}'")
        return pd.DataFrame()
        
    data_sources = manifest.get('data_sources', {})
    if data_source not in data_sources:
        if is_debug_mode():
            st.warning(f"🐛 Debug - Data source '{data_source}' not found in manifest")
        return pd.DataFrame()
        
    source_config = data_sources[data_source]
    
    if is_debug_mode():
        st.info(f"🐛 Debug - Source config for '{data_source}': {source_config}")
    
    # Check if source is required
    if source_config.get('required', False):
        # Required sources must exist
        pass
    
    # Resolve file path with version substitution
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
    
    if is_debug_mode():
        st.info(f"🐛 Debug - Original file path: '{source_config['file_path']}'")
    
    # Substitute version in file path
    versioned_file_path = substitute_version_in_path(source_config['file_path'], data_version)
    
    fallback_path = source_config.get('fallback_path')
    if fallback_path:
        fallback_path = substitute_version_in_path(fallback_path, data_version)
    
    file_path = resolve_file_path(
        versioned_file_path, 
        manifest_dir,
        manifest.get('path_settings', {}).get('allow_absolute_paths', True),
        fallback_path
    )
    
    if is_debug_mode():
        st.info(f"🐛 Debug - Final resolved file path: '{file_path}'")
    
    # Check if file exists
    if not file_path or not os.path.exists(file_path):
        if is_debug_mode():
            st.warning(f"🐛 Debug - File does not exist: '{file_path}'")
        if source_config.get('required', False):
            st.error(f"Required data file not found: {file_path}")
        return pd.DataFrame()
    
    try:
        # Get columns to load
        columns = source_config.get('columns', None)
        
        if is_debug_mode():
            st.info(f"🐛 Debug - Loading columns: {columns if columns else 'ALL'}")
        
        # Show which exact file is being loaded (always show for troubleshooting)
        st.info(f"📁 Reading file: {os.path.basename(file_path)}")
        
        # Load the Parquet file
        if columns is None:
            df = pd.read_parquet(file_path, engine='pyarrow')
        else:
            df = pd.read_parquet(file_path, engine='pyarrow', columns=columns)
        
        if is_debug_mode():
            st.info(f"🐛 Debug - Loaded file with {df.shape[0]} rows, {df.shape[1]} columns")
            st.info(f"🐛 Debug - Columns: {list(df.columns)}")
        
        # Check if this is a multi-source file (has data_source column) or single-source file
        if 'data_source' in df.columns:
            # Multi-source file - filter by data source
            filtered_df = df[df['data_source'] == data_source]
            
            if is_debug_mode():
                st.info(f"🐛 Debug - Multi-source file: filtered to {filtered_df.shape[0]} rows for '{data_source}'")
            
            # Drop the data_source column as it's no longer needed
            if 'data_source' in filtered_df.columns:
                filtered_df = filtered_df.drop(columns=['data_source'])
                
            return filtered_df
        else:
            # Single-source file - return the data as-is for its designated source
            # IMPORTANT: Don't filter by data_source here! Single-source files contain only 
            # their designated data type (e.g., planned.parquet contains only planned data,
            # main.parquet contains only main data). The file path already determines the source.
            # See claude_docs/planned_data_loading_fix.md for details on why this matters.
            if is_debug_mode():
                st.info(f"🐛 Debug - Single-source file: returning data for '{data_source}' ({df.shape[0]} rows)")
            return df
    except Exception as e:
        if is_debug_mode():
            st.error(f"🐛 Debug - Error reading '{data_source}' from '{file_path}': {str(e)}")
        st.error(f"Error reading {data_source} data from {file_path}: {str(e)}")
        return pd.DataFrame()

@st.cache_data
def get_manifest_data_sources(manifest_path, data_version, _file_mtime=None):
    """
    Get list of available data sources from manifest with detailed status.
    
    Args:
        manifest_path: Path to the manifest file
        data_version: Version to load ('regular' or 'adjusted')
        _file_mtime: File modification time for cache busting
        
    Returns:
        Tuple of (available_sources_list, detailed_status_dict)
    """
    manifest = load_data_manifest(manifest_path, _file_mtime)
    if not manifest:
        return [], {}
        
    available_sources = []
    detailed_status = {}
    data_sources = manifest.get('data_sources', {})
    manifest_dir = os.path.dirname(os.path.abspath(manifest_path))
    
    for source_name, source_config in data_sources.items():
        # Apply version substitution to the file path
        raw_file_path = source_config['file_path']
        versioned_file_path = substitute_version_in_path(raw_file_path, data_version)
        
        status = {
            'configured_path': raw_file_path,
            'resolved_path': None,
            'exists': False,
            'error': None
        }
        
        try:
            fallback_path = source_config.get('fallback_path')
            if fallback_path:
                fallback_path = substitute_version_in_path(fallback_path, data_version)
            
            resolved_path = resolve_file_path(
                versioned_file_path, 
                manifest_dir,
                manifest.get('path_settings', {}).get('allow_absolute_paths', True),
                fallback_path
            )
            status['resolved_path'] = resolved_path
            
            if resolved_path and os.path.exists(resolved_path):
                status['exists'] = True
                available_sources.append(source_name)
            else:
                if resolved_path is None:
                    status['error'] = "No files match glob pattern"
                else:
                    status['error'] = "File does not exist"
                    
        except Exception as e:
            status['error'] = str(e)
            
        detailed_status[source_name] = status
            
    return available_sources, detailed_status

def process_manifest_data(manifest_path):
    """
    Process data using manifest file configuration.
    
    Args:
        manifest_path: Path to the data_manifest.yaml file
    """
    try:
        # Force debug output for troubleshooting
        st.info(f"🐛 DEBUG: Starting manifest processing: '{manifest_path}'")
        
        # Load and validate manifest
        manifest = load_data_manifest(manifest_path)
        if not manifest:
            st.error(f"❌ Failed to load manifest from: '{manifest_path}'")
            return
        
        st.info("🐛 DEBUG: Manifest loaded successfully")
            
        # Extract currency and client info from manifest
        currency = manifest.get('currency', 'nok')
        client_id = manifest.get('client_id')
        
        if is_debug_mode():
            st.info(f"🐛 Debug - Manifest currency: '{currency}', client_id: '{client_id}'")
        
        # Set currency in session state
        st.session_state.currency = currency
        st.session_state.currency_selected = True
        
        # Load capacity configuration if client specified
        capacity_config = None
        if client_id:
            try:
                capacity_config = load_client_absence_config(client_id)
                st.session_state.capacity_config = capacity_config
                st.success(f"Loaded capacity configuration for client: {client_id}")
                
                with st.expander("Capacity Configuration Details"):
                    st.json(capacity_config)
            except Exception as e:
                st.warning(f"Could not load capacity config for {client_id}: {str(e)}")
        
        # Get available data sources with detailed status (with cache busting)
        file_mtime = get_file_mtime(manifest_path)
        current_version = st.session_state.get('data_version', 'adjusted')
        
        if is_debug_mode():
            st.info(f"🐛 Debug - Checking data sources with file mtime: {file_mtime}")
        
        available_sources, detailed_status = get_manifest_data_sources(manifest_path, current_version, file_mtime)
        
        st.info(f"🐛 DEBUG: Found {len(available_sources)} available sources: {available_sources}")
        st.info(f"🐛 DEBUG: Detailed status for {len(detailed_status)} configured sources")
        
        # Store debug information in session state
        st.session_state.data_loading_method = "manifest"
        st.session_state.manifest_debug_info = {
            'manifest_path': manifest_path,
            'available_sources': available_sources,
            'detailed_status': detailed_status,
            'currency': currency,
            'client_id': client_id
        }
        
        # Force show detailed status for troubleshooting
        st.info("🐛 DEBUG: File Resolution Status:")
        for source_name, status in detailed_status.items():
            icon = "✅" if status['exists'] else "❌"
            st.info(f"{icon} **{source_name}**")
            st.info(f"  - Configured: `{status['configured_path']}`")
            st.info(f"  - Resolved: `{status['resolved_path']}`")
            st.info(f"  - Exists: {status['exists']}")
            if status['error']:
                st.error(f"  - Error: {status['error']}")
        
        if not available_sources:
            st.error("No data files found for any configured data sources.")
            return
            
        # Check for required main data source
        if 'main' not in available_sources:
            st.error("Required 'main' data source file not found.")
            st.error(f"Available sources: {available_sources}")
            return
            
        st.success(f"Successfully loaded manifest with {len(available_sources)} data sources.")
        st.info(f"📁 Using manifest-based loading")
        st.info(f"Available data sources: {', '.join(available_sources)}")
        
        # Load and process main data
        current_version = st.session_state.get('data_version', 'adjusted')
        st.info(f"🔄 Loading main data with version: {current_version}")
        
        main_data = read_parquet_from_manifest(manifest_path, 'main', current_version, file_mtime)
        
        if main_data.empty:
            st.error("No main project data found.")
            return
        
        st.success(f"📊 Loaded main data: {main_data.shape[0]} rows, {main_data.shape[1]} columns")
            
        # Validate main data schema
        validation_results = validate_csv_schema(main_data)
        display_validation_results(validation_results)
        
        if validation_results["is_valid"]:
            transformed_df = cached_transform_csv(main_data)
            st.session_state.transformed_df = transformed_df
            st.session_state.csv_loaded = True
            
            del main_data
            gc.collect()
            
            # Process planned data if available
            if 'planned' in available_sources:
                planned_data = read_parquet_from_manifest(manifest_path, 'planned', current_version, file_mtime)
                
                if not planned_data.empty:
                    planned_validation_results = validate_planned_schema(planned_data)
                    st.subheader("Planned Hours Validation")
                    display_planned_validation_results(planned_validation_results)
                    
                    if planned_validation_results["is_valid"]:
                        transformed_planned_df = cached_transform_planned_csv(planned_data)
                        st.session_state.transformed_planned_df = transformed_planned_df
                        st.session_state.planned_csv_loaded = True
                        st.success(f"Loaded planned hours data with {planned_data.shape[0]} rows.")
                        
                        planned_metrics = calculate_planned_summary_metrics(transformed_planned_df)
                        st.info(
                            f"Total planned hours: {int(planned_metrics['total_planned_hours']):,}\n"
                            f"Projects: {planned_metrics['unique_projects']}\n"
                            f"People: {planned_metrics['unique_people']}"
                        )
                        
                        if 'Date' in transformed_planned_df.columns and not transformed_planned_df.empty:
                            st.session_state.planned_max_date = transformed_planned_df['Date'].max().date()
                            st.info(f"Planned hours extend to: {st.session_state.planned_max_date}")
                
                del planned_data
                gc.collect()
            
            # Process capacity data sources using manifest
            process_capacity_data_sources_from_manifest(manifest_path, available_sources, capacity_config, current_version, file_mtime)
            
            # Process person reference data
            if 'person_reference' in available_sources:
                person_ref_data = read_parquet_from_manifest(manifest_path, 'person_reference', current_version, file_mtime)
                
                if not person_ref_data.empty:
                    if "person_name" not in person_ref_data.columns or "person_type" not in person_ref_data.columns:
                        st.error("Person reference data must contain 'Person' and 'Person type' columns")
                    else:
                        person_ref_data['Person type'] = person_ref_data['Person type'].str.lower()
                        st.session_state.person_reference_df = person_ref_data
                        st.success(f"Loaded person reference data with {person_ref_data.shape[0]} entries.")
                        
                        if 'transformed_df' in st.session_state and st.session_state.transformed_df is not None:
                            st.session_state.transformed_df = cached_enrich_person_data(
                                st.session_state.transformed_df, 
                                person_ref_data
                            )
                
                del person_ref_data
                gc.collect()
            
            # Process project reference data
            if 'project_reference' in available_sources:
                project_ref_data = read_parquet_from_manifest(manifest_path, 'project_reference', current_version, file_mtime)
                
                if not project_ref_data.empty:
                    if "project_number" not in project_ref_data.columns:
                        st.error("Project reference data must contain 'Project number' column")
                    else:
                        st.session_state.project_reference_df = project_ref_data
                        st.success(f"Loaded project reference data with {project_ref_data.shape[0]} entries.")
                        
                        if 'transformed_df' in st.session_state and st.session_state.transformed_df is not None:
                            st.session_state.transformed_df = cached_enrich_project_data(
                                st.session_state.transformed_df, 
                                project_ref_data
                            )
                            st.success("Applied project reference data to main dataset.")
                        
                        with st.expander("Project Reference Data"):
                            st.write(project_ref_data.head())
                            metadata_columns = [col for col in project_ref_data.columns if col != 'Project number']
                            if metadata_columns:
                                st.info(f"Metadata columns: {', '.join(metadata_columns)}")
                            else:
                                st.warning("No metadata columns found besides 'Project number'")
                
                del project_ref_data
                gc.collect()
            
            gc.collect()
            st.session_state.data_loading_attempted = False
            st.rerun()
            
    except Exception as e:
        st.error(f"Error processing manifest data: {str(e)}")
        # Store error in debug info
        st.session_state.data_loading_method = "manifest_failed"
        st.session_state.manifest_debug_info = {
            'error': str(e),
            'manifest_path': manifest_path
        }

def process_capacity_data_sources_from_manifest(manifest_path, available_sources, capacity_config, current_version, file_mtime=None):
    """
    Process capacity-related data sources using manifest configuration.
    
    Args:
        manifest_path: Path to the manifest file
        available_sources: List of available data source names
        capacity_config: Parsed capacity configuration (can be None)
        current_version: Version to load ('regular' or 'adjusted')
        file_mtime: File modification time for cache busting
    """
    # Check for capacity data sources
    has_schedule = 'schedule' in available_sources
    has_absence = 'absence' in available_sources  
    has_weekly_source = 'weekly_source' in available_sources
    
    if not (has_schedule or has_absence or has_weekly_source):
        return
    
    st.subheader("Capacity Data Processing")
    
    # Initialize capacity dataframes
    schedule_df = pd.DataFrame()
    absence_df = pd.DataFrame()
    
    # Process weekly source data
    if has_weekly_source:
        weekly_data = read_parquet_from_manifest(manifest_path, 'weekly_source', current_version, file_mtime)
        st.session_state.weekly_source_df = weekly_data
        
        if not weekly_data.empty:
            weekly_validation_results = validate_weekly_source_schema(weekly_data)
            display_weekly_source_validation_results(weekly_validation_results)
            
            if weekly_validation_results["is_valid"]:
                if capacity_config:
                    completeness_results = validate_weekly_data_completeness(weekly_data, capacity_config)
                    
                    if not completeness_results["is_complete"]:
                        st.warning("Weekly data validation warnings:")
                        for warning in completeness_results["warnings"]:
                            st.warning(f"• {warning}")
                        
                        if completeness_results["suggestions"]:
                            st.info("Suggestions:")
                            for suggestion in completeness_results["suggestions"]:
                                st.info(f"• {suggestion}")
                
                schedule_df = cached_transform_weekly_to_schedule(weekly_data)
                st.success(f"Transformed weekly data to schedule format: {len(schedule_df)} records")
                
                if capacity_config:
                    absence_df = cached_transform_weekly_to_absence(weekly_data, capacity_config)
                    st.success(f"Transformed weekly data to absence format: {len(absence_df)} records")
                else:
                    st.warning("Capacity configuration not available - absence data not processed")
        
        del weekly_data
        gc.collect()
    
    # Process direct schedule data
    elif has_schedule:
        schedule_data = read_parquet_from_manifest(manifest_path, 'schedule', current_version, file_mtime)
        
        if not schedule_data.empty:
            schedule_validation_results = validate_schedule_schema(schedule_data)
            display_schedule_validation_results(schedule_validation_results)
            
            if schedule_validation_results["is_valid"]:
                schedule_df = schedule_data
                st.success(f"Loaded schedule data: {len(schedule_df)} records")
        
        del schedule_data
        gc.collect()
    
    # Process direct absence data
    if has_absence and absence_df.empty:
        absence_data = read_parquet_from_manifest(manifest_path, 'absence', current_version, file_mtime)
        
        if not absence_data.empty:
            absence_validation_results = validate_absence_schema(absence_data)
            display_absence_validation_results(absence_validation_results)
            
            if absence_validation_results["is_valid"]:
                absence_df = absence_data
                st.success(f"Loaded absence data: {len(absence_df)} records")
        
        del absence_data
        gc.collect()
    
    # Store capacity data and create summary
    if not schedule_df.empty:
        st.session_state.schedule_df = schedule_df
        st.session_state.schedule_loaded = True
        
        if not absence_df.empty:
            st.session_state.absence_df = absence_df
            st.session_state.absence_loaded = True
        
        if capacity_config:
            capacity_summary_df = cached_create_capacity_summary(schedule_df, absence_df, capacity_config)
            st.session_state.capacity_summary_df = capacity_summary_df
            st.session_state.capacity_summary_loaded = True
            
            processing_summary = get_capacity_processing_summary(schedule_df, absence_df, capacity_config)
            
            with st.expander("Capacity Processing Summary"):
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Schedule Records", processing_summary["schedule_records"])
                    st.metric("Unique Persons", processing_summary["unique_persons"])
                
                with col2:
                    st.metric("Absence Records", processing_summary["absence_records"]) 
                    st.metric("Total Scheduled Hours", f"{processing_summary['total_scheduled_hours']:,.0f}")
                
                with col3:
                    st.metric("Total Absence Hours", f"{processing_summary['total_absence_hours']:,.0f}")
                    if processing_summary["date_range"]:
                        date_range = processing_summary["date_range"]
                        st.info(f"Period: {date_range['start'].strftime('%Y-%m-%d')} to {date_range['end'].strftime('%Y-%m-%d')}")
            
            st.success("Capacity analysis data is ready for dashboard use.")

# Keep original function for backward compatibility (if needed elsewhere)
def process_parquet_data(parquet_file):
    """
    Legacy function for processing uploaded Parquet files.
    Kept for backward compatibility.
    """
    # This would need to handle the uploaded file object differently
    # For now, just raise an error suggesting the new approach
    st.error("Upload-based processing is deprecated. Please use file-based loading instead.")
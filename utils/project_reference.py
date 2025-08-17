# utils/project_reference.py
import pandas as pd
import streamlit as st
from datetime import datetime, date

def load_project_reference(file_path=None):
    """
    Load project reference data from a file or provide UI to upload one.
    
    Args:
        file_path: Optional path to reference file
        
    Returns:
        DataFrame with project reference data
    """
    if 'project_reference_df' not in st.session_state:
        if file_path:
            # Load from predefined path
            try:
                df = pd.read_csv(file_path)
                st.session_state.project_reference_df = df
                return df
            except Exception as e:
                st.warning(f"Error loading project reference file: {e}")
                st.session_state.project_reference_df = None
        else:
            # Let user upload reference file
            st.session_state.project_reference_df = None
    
    return st.session_state.project_reference_df

def enrich_project_data(df, reference_df):
    """
    Add project attributes from reference data to dataframe.
    
    Args:
        df: DataFrame with Project number column
        reference_df: Reference DataFrame with project attributes
        
    Returns:
        Enriched DataFrame
    """
    if df is None or reference_df is None:
        return df
        
    # Create a copy to avoid modifying original
    enriched_df = df.copy()
    
    # Get all metadata columns except Project number (which is used for joining)
    metadata_columns = [col for col in reference_df.columns if col != 'Project number']
    
    if not metadata_columns:
        return enriched_df
    
    # Merge all available metadata columns
    enriched_df = pd.merge(
        enriched_df,
        reference_df[['Project number'] + metadata_columns],
        on='Project number',
        how='left',
        suffixes=('', '_ref')  # In case of column name conflicts
    )
    
    # Resolve any duplicate columns (prefer original if exists)
    for col in metadata_columns:
        ref_col = f"{col}_ref"
        
        # If the column exists in both dataframes
        if ref_col in enriched_df.columns:
            # If original column has a value, keep it, otherwise use reference value
            enriched_df[col] = enriched_df[col].fillna(enriched_df[ref_col])
            # Drop the duplicate column
            enriched_df = enriched_df.drop(columns=[ref_col])
    
    return enriched_df

def detect_column_type(df, column):
    """
    Detect the data type of a column for filtering purposes.
    
    Args:
        df: DataFrame containing the column
        column: Column name to check
        
    Returns:
        String indicating the column type ('categorical', 'numeric', 'date', or 'other')
    """
    # Skip columns with all null values
    if df[column].isna().all():
        return 'other'
    
    # Check if it's already a datetime column
    if pd.api.types.is_datetime64_any_dtype(df[column]):
        return 'date'
    
    # Check if column name suggests a date (case insensitive)
    date_indicators = ['date', 'created', 'modified', 'updated', 'start', 'end', 
                       'birth', 'deadline', 'due', 'completed', 'timestamp']
    
    if any(indicator in column.lower() for indicator in date_indicators):
        # Try to convert to datetime with multiple formats
        non_null_values = df[column].dropna()
        if len(non_null_values) > 0:
            try:
                # Try European format specifically (DD.MM.YYYY)
                pd.to_datetime(non_null_values, format='%d.%m.%Y', errors='raise')
                return 'date'
            except (ValueError, TypeError):
                # Try automatic format detection
                try:
                    pd.to_datetime(non_null_values, errors='raise')
                    return 'date'
                except (ValueError, TypeError):
                    # Not a date despite the name suggesting it
                    pass
    
    # For string/object columns, try to detect if they're dates regardless of column name
    if pd.api.types.is_string_dtype(df[column]) or pd.api.types.is_object_dtype(df[column]):
        non_null_values = df[column].dropna()
        if len(non_null_values) > 0:
            # Try common date formats, especially European format
            date_formats = ['%d.%m.%Y', '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y']
            
            for fmt in date_formats:
                try:
                    # Sample test - try first 5 values with this format
                    samples = non_null_values.iloc[:5] if len(non_null_values) >= 5 else non_null_values
                    success = True
                    
                    for sample in samples:
                        try:
                            pd.to_datetime(sample, format=fmt)
                        except:
                            success = False
                            break
                    
                    if success:
                        # If sample test passed, try the whole column
                        pd.to_datetime(non_null_values, format=fmt)
                        return 'date'
                except:
                    continue
            
            # If no specific format worked, try pandas' automatic detection
            try:
                sample = non_null_values.iloc[0]
                pd.to_datetime(sample)
                pd.to_datetime(non_null_values)
                return 'date'
            except (ValueError, TypeError):
                pass
    
    # Check if it's a numeric column (int or float)
    if pd.api.types.is_numeric_dtype(df[column]):
        # If all values are integers, check if it's more like a category
        if pd.api.types.is_integer_dtype(df[column]) or df[column].dropna().apply(lambda x: x.is_integer() if isinstance(x, float) else True).all():
            # If there are only a few unique values, treat as categorical
            if df[column].nunique() <= 20:
                return 'categorical'
        # Otherwise treat all numeric columns as numeric
        return 'numeric'
    
    # Try to convert to numeric if possible
    try:
        # Check if column can be converted to numeric
        numeric_column = pd.to_numeric(df[column], errors='coerce')
        # If we have valid numeric values and not many NaNs were introduced
        if not numeric_column.isna().all() and numeric_column.isna().sum() / len(numeric_column) < 0.5:
            # If there are only a few unique values, treat as categorical
            if numeric_column.nunique() <= 20:
                return 'categorical'
            return 'numeric'
    except (ValueError, TypeError):
        pass
    
    # If the column has few unique values, treat as categorical 
    if df[column].nunique() <= 20:
        return 'categorical'
    
    # Default to categorical for any other type
    return 'categorical'

def get_dynamic_project_filters(df, reference_df):
    """
    Create dynamic filters based on project reference metadata columns.
    
    Args:
        df: Main dataframe with project data
        reference_df: Reference dataframe with project metadata
        
    Returns:
        Tuple of (filtered_dataframe, filter_settings_dict, handled_columns)
    """
    if df is None or reference_df is None:
        return df, {}, []
        
    filtered_df = df.copy()
    filter_settings = {}
    handled_columns = []
    
    # Get metadata columns (excluding Project number which is used for joining)
    metadata_columns = [col for col in reference_df.columns if col != 'Project number']
    
    # Skip if no metadata columns found
    if not metadata_columns:
        return filtered_df, filter_settings, handled_columns
    
    # Create a single expander for all detailed project data filters
    with st.sidebar.expander("Detailed Project Data"):
        # Create filters for each metadata column inside the expander
        for column in metadata_columns:
            # Skip if column doesn't exist in the dataframe
            if column not in filtered_df.columns:
                continue
                
            # Mark this column as handled
            handled_columns.append(column)
            
            # Detect column type for appropriate filtering
            column_type = detect_column_type(filtered_df, column)
            
            if column_type == 'categorical':
                # Get unique values for this column
                unique_values = filtered_df[column].dropna().unique().tolist()
                
                # Use the column name as the filter title
                selected_values = st.multiselect(
                    f"Select {column}",
                    options=sorted(unique_values),
                    key=f"filter_{column}"
                )
                
                # Apply filter if values selected
                if selected_values:
                    filtered_df = filtered_df[filtered_df[column].isin(selected_values)]
                    filter_settings[f"selected_{column}"] = selected_values
            
            elif column_type == 'numeric':
                # For numeric columns, first convert to numeric if not already
                if not pd.api.types.is_numeric_dtype(filtered_df[column]):
                    # Try to convert to numeric
                    try:
                        # Create a temporary numeric column
                        filtered_df[f'{column}_numeric'] = pd.to_numeric(filtered_df[column], errors='coerce')
                        numeric_column = f'{column}_numeric'
                    except Exception as e:
                        st.warning(f"Error converting {column} to numeric: {e}")
                        continue
                else:
                    numeric_column = column
                
                # Get min and max values
                min_val = filtered_df[numeric_column].min()
                max_val = filtered_df[numeric_column].max()
                
                # Skip if all NaN
                if pd.isna(min_val) or pd.isna(max_val):
                    if numeric_column != column:
                        filtered_df = filtered_df.drop(columns=[numeric_column])
                    continue
                    
                # Convert to float to handle both int and float types
                min_val = float(min_val)
                max_val = float(max_val)
                
                # Handle case where min equals max
                if min_val == max_val:
                    st.info(f"{column}: All values are {min_val}")
                    if numeric_column != column:
                        filtered_df = filtered_df.drop(columns=[numeric_column])
                    continue
                    
                # Add a little padding for float values to ensure the max value is included
                if min_val != max_val:
                    range_padding = (max_val - min_val) * 0.001
                    max_val += range_padding
                
                # Determine step size based on the range
                range_size = max_val - min_val
                if range_size <= 1:
                    step = 0.01  # Small step for small ranges
                elif range_size <= 10:
                    step = 0.1
                elif range_size <= 100:
                    step = 1.0
                else:
                    step = float(round(range_size / 100))  # Dynamic step size, convert to float
                    
                value_range = st.slider(
                    f"{column} range",
                    min_value=min_val,
                    max_value=max_val,
                    value=(min_val, max_val),
                    step=step,
                    key=f"slider_{column}"
                )
                
                # Apply filter if range is changed
                if value_range != (min_val, max_val):
                    if numeric_column == column:
                        # Apply filter to original column
                        filtered_df = filtered_df[(filtered_df[column] >= value_range[0]) & 
                                             (filtered_df[column] <= value_range[1])]
                    else:
                        # Apply filter to temporary numeric column
                        filtered_df = filtered_df[(filtered_df[numeric_column] >= value_range[0]) & 
                                             (filtered_df[numeric_column] <= value_range[1])]
                    
                    filter_settings[f"{column}_range"] = value_range
                    
                # Clean up temp column if created
                if numeric_column != column and numeric_column in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=[numeric_column])
            
            elif column_type == 'date':
                # For date columns, always prioritize European date format (DD.MM.YYYY)
                
                # First convert to datetime if not already
                if not pd.api.types.is_datetime64_any_dtype(filtered_df[column]):
                    try:
                        # Try European format first (DD.MM.YYYY)
                        try:
                            filtered_df[f'{column}_datetime'] = pd.to_datetime(filtered_df[column], 
                                                                              format='%d.%m.%Y', 
                                                                              errors='coerce')
                        except:
                            # If that fails, use automatic detection with dayfirst=True
                            filtered_df[f'{column}_datetime'] = pd.to_datetime(filtered_df[column], 
                                                                              dayfirst=True, 
                                                                              errors='coerce')
                        date_column = f'{column}_datetime'
                    except Exception as e:
                        st.warning(f"Error converting {column} to date: {e}")
                        continue
                else:
                    date_column = column
                
                # Get min and max dates
                min_date = filtered_df[date_column].min()
                max_date = filtered_df[date_column].max()
                
                # Skip if we couldn't get valid dates
                if pd.isna(min_date) or pd.isna(max_date):
                    if date_column != column and date_column in filtered_df.columns:
                        filtered_df = filtered_df.drop(columns=[date_column])
                    continue
                    
                # Convert to date objects for date_input
                min_date = min_date.date() if hasattr(min_date, 'date') else datetime(2000, 1, 1).date()
                max_date = max_date.date() if hasattr(max_date, 'date') else date.today()
                
                # Create date range selector
                col1, col2 = st.columns(2)
                
                with col1:
                    start_date = st.date_input(
                        f"{column} start",
                        value=min_date,
                        key=f"date_start_{column}"
                    )
                    
                with col2:
                    end_date = st.date_input(
                        f"{column} end",
                        value=max_date,
                        key=f"date_end_{column}"
                    )
                
                # Apply date filter if range is changed
                if start_date != min_date or end_date != max_date:
                    # Convert Python date objects to pandas Timestamp for comparison
                    start_timestamp = pd.Timestamp(start_date)
                    end_timestamp = pd.Timestamp(end_date) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
                    
                    # Apply the filter
                    filtered_df = filtered_df[(filtered_df[date_column] >= start_timestamp) & 
                                            (filtered_df[date_column] <= end_timestamp)]
                    
                    filter_settings[f"{column}_date_range"] = (start_date, end_date)
                
                # Clean up temp column if created
                if date_column != column and date_column in filtered_df.columns:
                    filtered_df = filtered_df.drop(columns=[date_column])
    
    return filtered_df, filter_settings, handled_columns
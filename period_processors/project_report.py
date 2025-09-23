import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
from period_translations.translations import t
from period_charts.project_hours import render_project_hours_chart
from period_charts.project_fees import render_project_fees_chart
from period_charts.project_rate import render_project_rate_chart

def transform_parquet_to_project_report(parquet_path):
    """
    Transform unified parquet data to Project Report CSV format.

    Args:
        parquet_path: Path to the unified parquet file

    Returns:
        DataFrame in Project Report format with columns:
        - Project ID, Project Name, Period, Period Hours, Planned Hours, Period Fees, Planned Income
    """
    try:
        # Import the existing aggregation function
        from utils.processors import aggregate_project_by_month_year

        # Load parquet data
        df = pd.read_parquet(parquet_path)

        # Ensure we have the required columns
        required_cols = ['record_type', 'project_number', 'project_name', 'record_date']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            st.error(f"Missing required columns in parquet file: {missing_cols}")
            return None

        # Separate time_record and planned_record data
        time_records = df[df['record_type'] == 'time_record'].copy()
        planned_records = df[df['record_type'] == 'planned_record'].copy()

        # Check if we have data
        if time_records.empty and planned_records.empty:
            st.warning("No time_record or planned_record data found in parquet file")
            return None

        # Create project + month aggregation manually (aggregate_project_by_month_year doesn't group by project)
        project_month_data = []

        # Process time_records (actual work)
        if not time_records.empty:
            time_records_copy = time_records.copy()
            time_records_copy['Year'] = time_records_copy['record_date'].dt.year
            time_records_copy['Month'] = time_records_copy['record_date'].dt.month

            # Group by project + month + year
            actual_agg = time_records_copy.groupby(['project_number', 'project_name', 'Year', 'Month']).agg({
                'hours_used': 'sum',
                'hours_billable': 'sum',
                'fee_record': 'sum'
            }).reset_index()

            # Add period date
            actual_agg['Period'] = pd.to_datetime(actual_agg[['Year', 'Month']].assign(day=1))

            project_month_data.append(actual_agg)

        # Process planned_records (planned work)
        if not planned_records.empty:
            planned_records_copy = planned_records.copy()
            planned_records_copy['Year'] = planned_records_copy['record_date'].dt.year
            planned_records_copy['Month'] = planned_records_copy['record_date'].dt.month

            # Group by project + month + year
            planned_agg = planned_records_copy.groupby(['project_number', 'project_name', 'Year', 'Month']).agg({
                'planned_hours': 'sum',
                'planned_fee': 'sum'
            }).reset_index()

            # Add period date
            planned_agg['Period'] = pd.to_datetime(planned_agg[['Year', 'Month']].assign(day=1))

            project_month_data.append(planned_agg)

        if not project_month_data:
            st.warning("No project+month data generated")
            return None

        # Merge actual and planned data
        if len(project_month_data) == 2:
            # Both actual and planned data exist - merge them
            actual_df, planned_df_agg = project_month_data
            monthly_data = pd.merge(
                actual_df,
                planned_df_agg,
                on=['project_number', 'project_name', 'Year', 'Month', 'Period'],
                how='outer'
            )
        else:
            # Only one type exists
            monthly_data = project_month_data[0]

        # Fill NaN values with 0
        numeric_cols = ['hours_used', 'hours_billable', 'fee_record', 'planned_hours', 'planned_fee']
        for col in numeric_cols:
            if col in monthly_data.columns:
                monthly_data[col] = monthly_data[col].fillna(0)

        if monthly_data.empty:
            st.warning("No aggregated data generated from parquet file")
            return None

        # Transform to Project Report expected format
        project_report_df = monthly_data.copy()

        # Create Period column from Year and Month
        if 'Year' in project_report_df.columns and 'Month' in project_report_df.columns:
            # Create datetime from Year and Month, then format as YYYY-MM-DD
            project_report_df['Period'] = pd.to_datetime(
                project_report_df[['Year', 'Month']].assign(day=1)
            )
        elif 'record_date' in project_report_df.columns:
            project_report_df['Period'] = pd.to_datetime(project_report_df['record_date'])
        else:
            st.error("Cannot create Period column - missing Year/Month or record_date")
            return None

        # Rename columns to Project Report expected format
        column_mapping = {
            'project_number': 'Project ID',
            'project_name': 'Project Name',
            'hours_used': 'Period Hours',
            'planned_hours': 'Planned Hours',
            'fee_record': 'Period Fees Adjusted',  # Charts expect "Period Fees Adjusted"
            'planned_fee': 'Planned Income'
        }

        # Apply renaming only for columns that exist
        existing_mapping = {k: v for k, v in column_mapping.items() if k in project_report_df.columns}
        project_report_df = project_report_df.rename(columns=existing_mapping)

        # Select only the columns Project Report expects
        expected_columns = ['Project ID', 'Project Name', 'Period', 'Period Hours', 'Planned Hours', 'Period Fees Adjusted', 'Planned Income']

        # Fill missing columns with 0 or appropriate defaults
        for col in expected_columns:
            if col not in project_report_df.columns:
                if col in ['Period Hours', 'Planned Hours']:
                    project_report_df[col] = 0.0
                elif col in ['Period Fees Adjusted', 'Planned Income']:
                    project_report_df[col] = 0.0
                else:
                    project_report_df[col] = ""

        # Select and reorder columns
        project_report_df = project_report_df[expected_columns]

        # Sort by Project Name and Period for better readability
        project_report_df = project_report_df.sort_values(['Project Name', 'Period'])

        return project_report_df

    except Exception as e:
        st.error(f"Error transforming parquet to project report format: {str(e)}")
        return None

def get_data_directory():
    """Get the appropriate data directory - prioritize project data over temp"""
    # First priority: Railway volume (production environment)
    if os.path.exists("/data"):
        return "/data"

    # Second priority: Project data directory (preferred for development)
    project_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    if os.path.exists(project_data_dir):
        return project_data_dir

    # Third priority: Local temp directory (fallback)
    temp_data_dir = os.path.expanduser("~/temp_data")
    if os.path.exists(temp_data_dir):
        return temp_data_dir

    # Final fallback: Create project data directory
    return project_data_dir

def try_autoload_project_data():
    """Try to autoload project data from data directory."""
    data_dir = get_data_directory()

    # First, try to find and transform parquet files (preferred method)
    parquet_files = glob.glob(os.path.join(data_dir, '*.parquet'))
    for parquet_path in parquet_files:
        try:
            # Try to transform parquet to project report format
            transformed_df = transform_parquet_to_project_report(parquet_path)
            if transformed_df is not None and not transformed_df.empty:
                return transformed_df
        except Exception as e:
            st.warning(f"Could not transform {os.path.basename(parquet_path)}: {str(e)}")
            continue

    # Fallback: Look for CSV files that might contain project data
    # Common patterns: project*.csv, prosjekt*.csv (Norwegian)
    patterns = ['*project_report*.csv', 'project*.csv', 'prosjekt*.csv']

    for pattern in patterns:
        files = glob.glob(os.path.join(data_dir, pattern))
        if files:
            # Use the first matching file
            filepath = files[0]
            try:
                df = pd.read_csv(filepath)
                return df
            except Exception as e:
                st.warning(f"Could not load {os.path.basename(filepath)}: {str(e)}")
                continue

    # If no pattern matches, try to load any CSV and check if it has project-like columns
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath)
            # Check if it has typical project columns
            project_columns = ['Project ID', 'Project Name', 'Period Hours', 'Period Fees Adjusted']
            if any(col in df.columns for col in project_columns):
                return df
        except Exception as e:
            continue

    return None

def create_project_per_month_table(df):
    """Create project per month view - shows all projects organized by month."""
    if df.empty:
        return pd.DataFrame()
    
    # Simply return the original dataframe with proper sorting
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper sorting
    if not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Sort by Period and Project Name to group by month
    df_sorted = df_copy.sort_values(["Period", "Project Name"])
    
    return df_sorted

def render_project_table(df):
    """Render a table showing project data with translated headers."""
    # Check required columns
    required_columns = [
        "Project ID", "Project Name", "Period", "Period Hours",
        "Planned Hours", "Period Fees Adjusted", "Planned Income"
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"{t('missing_required_columns')}: {', '.join(missing_columns)}")
        return
    
    # Translation mapping for columns
    translation_mapping = {
        "Project ID": t("project_id"),
        "Project Name": t("project_name"),
        "Period": t("period_label"),
        "Period Hours": t("period_hours"),
        "Planned Hours": t("planned_hours"),
        "Period Fees Adjusted": t("period_fees"),
        "Planned Income": t("planned_income"),
   }
    
    # Create a display copy with translated column names
    display_df = df.copy()
    display_df = display_df.rename(columns=translation_mapping)
    
    # Create column config for special formatting
    column_config = {}
    
    # Add number formatting for currency columns
    fees_translated = translation_mapping["Period Fees Adjusted"]
    income_translated = translation_mapping["Planned Income"]
    
    column_config[fees_translated] = st.column_config.NumberColumn(format="%.2f")
    column_config[income_translated] = st.column_config.NumberColumn(format="%.2f")
    
    # Display the dataframe with translated headers
    st.dataframe(display_df, column_config=column_config, use_container_width=True)

def render_project_period_filters(df):
    """Render period filter controls (Month/Quarter/Year) and return filter parameters."""
    
    # Ensure Period is datetime FIRST before any processing
    if "Period" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Period"]):
        df["Period"] = pd.to_datetime(df["Period"], errors='coerce')
    
    # Remove any rows where Period conversion failed (NaT values)
    df = df.dropna(subset=["Period"])
    
    # Period filter options
    period_filter = st.sidebar.radio(
        t('period'), 
        [t('month'), t('quarters'), t('year_so_far'), t('year')],
        key='project_period_filter',
    )
    
    filter_params = {'type': period_filter}
    
    if period_filter == t('month'):
        from datetime import datetime
        
        # Year selection (like quarters filter)
        years = sorted(df["Period"].dt.year.unique(), reverse=True)
        current_year = datetime.now().year
        
        # Default to current year if available, otherwise most recent year
        year_default_index = 0
        if current_year in years:
            year_default_index = years.index(current_year)
        
        # Create two columns for year and month selection
        year_col, month_col = st.sidebar.columns(2)
        
        # Year selection
        with year_col:
            selected_year = st.selectbox(
                t('select_year'), 
                years,
                index=year_default_index,
                key='month_year'
            )
        
        # Get available months for the selected year only
        year_data = df[df["Period"].dt.year == selected_year]
        available_months = sorted(year_data["Period"].dt.month.unique())
        
        # Create month names only for available months
        month_keys = ['january', 'february', 'march', 'april', 'may', 'june', 
                     'july', 'august', 'september', 'october', 'november', 'december']
        
        available_month_names = []
        available_month_numbers = []
        for month_num in available_months:
            month_key = month_keys[month_num - 1]  # Convert to 0-based index
            month_name = t(month_key)
            available_month_names.append(month_name)
            available_month_numbers.append(month_num)
        
        # Calculate previous month as default, but only if it exists in available months
        current_date = datetime.now()
        if current_date.month == 1:  # January
            default_month_num = 12  # December
        else:
            default_month_num = current_date.month - 1
        
        # Find default index among available months
        default_month_index = 0  # fallback to first available month
        if default_month_num in available_month_numbers:
            default_month_index = available_month_numbers.index(default_month_num)
        
        # Month selection
        with month_col:
            selected_month_name = st.selectbox(
                t('select_month'),
                available_month_names,
                index=default_month_index,
                key='month_month'
            )
        
        # Convert month name back to number for filtering
        selected_month_num = available_month_numbers[available_month_names.index(selected_month_name)]
        
        filter_params['year'] = selected_year
        filter_params['month'] = selected_month_num
    
    elif period_filter == t('quarters'):
        # Get list of years in the data
        years = sorted(df["Period"].dt.year.unique(), reverse=True)
        
        # Create two columns for year and quarter selection
        year_col, quarter_col = st.sidebar.columns(2)
        
        # Year selection
        with year_col:
            selected_year = st.selectbox(t('select_year'), years, key='quarter_year')
        
        # Quarter selection
        with quarter_col:
            quarters = [t('q1'), t('q2'), t('q3'), t('q4')]
            selected_quarter = st.selectbox(t('select_quarter'), quarters, key='quarter_quarter')
        
        # Determine quarter number
        quarter_num = quarters.index(selected_quarter) + 1
        
        filter_params['year'] = selected_year
        filter_params['quarter'] = quarter_num
    
    elif period_filter == t('year'):
        # Get list of years in the data
        years = sorted(df["Period"].dt.year.unique(), reverse=True)
        
        # Default to 2025
        default_index = 0
        if 2025 in years:
            default_index = years.index(2025)
        
        selected_year = st.sidebar.selectbox(
            t('select_year'), 
            years,
            index=default_index
        )
        filter_params['year'] = selected_year
    
    elif period_filter == t('year_so_far'):
        from datetime import datetime
        
        # Always use current year for "Year so far"
        current_year = datetime.now().year
        selected_year = current_year
        
        # Get available months for the selected year (months with any data)
        year_data = df[df["Period"].dt.year == selected_year]
        available_months = sorted(year_data["Period"].dt.month.unique())
        
        # Find the last month with actual worked data for default
        if "Period Hours" in year_data.columns:
            actual_work_data = year_data[year_data["Period Hours"] > 0]
            if not actual_work_data.empty:
                default_to_month = actual_work_data["Period"].dt.month.max()
            else:
                default_to_month = available_months[-1] if available_months else 12
        else:
            default_to_month = available_months[-1] if available_months else 12
        
        # Create month names for available months
        month_keys = ['january', 'february', 'march', 'april', 'may', 'june', 
                     'july', 'august', 'september', 'october', 'november', 'december']
        
        available_month_names = []
        available_month_numbers = []
        for month_num in available_months:
            month_key = month_keys[month_num - 1]
            month_name = t(month_key)
            available_month_names.append(month_name)
            available_month_numbers.append(month_num)
        
        # Create two columns for from/to month selection
        from_col, to_col = st.sidebar.columns(2)
        
        # From month dropdown
        with from_col:
            from_month_index = 0  # Default to first available month (typically January)
            from_month_name = st.selectbox(
                t('from_month'),
                available_month_names,
                index=from_month_index,
                key='ysf_from_month'
            )
            from_month_num = available_month_numbers[available_month_names.index(from_month_name)]
        
        # To month dropdown  
        with to_col:
            # Default to last month with actual data
            to_month_index = len(available_month_names) - 1
            if default_to_month in available_month_numbers:
                to_month_index = available_month_numbers.index(default_to_month)
            
            to_month_name = st.selectbox(
                t('to_month'),
                available_month_names,
                index=to_month_index,
                key='ysf_to_month'
            )
            to_month_num = available_month_numbers[available_month_names.index(to_month_name)]
        
        filter_params['year'] = selected_year
        filter_params['from_month'] = from_month_num
        filter_params['to_month'] = to_month_num
    
    return filter_params

def apply_project_period_filter(df, filter_params):
    """Apply period filtering to project dataframe based on filter parameters."""
    filtered_df = df.copy()
    filter_type = filter_params.get('type')
    filtered_period_info = {'filter_type': filter_type}
    
    # Ensure Period is datetime
    if "Period" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Period"]):
        filtered_df["Period"] = pd.to_datetime(filtered_df["Period"], errors='coerce')
    
    if filter_type == t('month'):
        selected_year = filter_params.get('year')
        selected_month = filter_params.get('month')
        if selected_year and selected_month:
            # Filter for selected year and month
            year_filter = filtered_df["Period"].dt.year == selected_year
            month_filter = filtered_df["Period"].dt.month == selected_month
            filtered_df = filtered_df[year_filter & month_filter]
            filtered_period_info['year'] = selected_year
            filtered_period_info['month'] = selected_month
    
    elif filter_type == t('quarters'):
        selected_year = filter_params.get('year')
        quarter_num = filter_params.get('quarter')

        # Debug: Check available quarters in the data for the selected year
        year_data = filtered_df[filtered_df["Period"].dt.year == selected_year]
        if not year_data.empty:
            available_quarters = sorted(year_data["Period"].dt.quarter.unique())

            # Filter for selected year and quarter
            year_filter = filtered_df["Period"].dt.year == selected_year
            quarter_filter = filtered_df["Period"].dt.quarter == quarter_num
            filtered_df = filtered_df[year_filter & quarter_filter]

            # Show helpful message if no data exists for selected quarter
            if filtered_df.empty:
                quarter_names = {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
                available_quarter_names = [quarter_names[q] for q in available_quarters]
                st.warning(f"No data found for Q{quarter_num} {selected_year}. Available quarters: {', '.join(available_quarter_names)}")
        else:
            filtered_df = filtered_df.iloc[0:0]  # Empty dataframe
            st.warning(f"No data found for year {selected_year}")

        filtered_period_info['year'] = selected_year
        filtered_period_info['quarter'] = quarter_num
    
    elif filter_type == t('year'):
        selected_year = filter_params.get('year')
        if selected_year:
            # Filter for selected year
            filtered_df = filtered_df[filtered_df["Period"].dt.year == selected_year]
            filtered_period_info['year'] = selected_year
    
    elif filter_type == t('year_so_far'):
        selected_year = filter_params.get('year')
        from_month = filter_params.get('from_month')
        to_month = filter_params.get('to_month')
        if selected_year and from_month and to_month:
            # Filter for selected year and month range
            year_filter = filtered_df["Period"].dt.year == selected_year
            month_filter = (filtered_df["Period"].dt.month >= from_month) & (filtered_df["Period"].dt.month <= to_month)
            filtered_df = filtered_df[year_filter & month_filter]
            filtered_period_info['year'] = selected_year
            filtered_period_info['from_month'] = from_month
            filtered_period_info['to_month'] = to_month
    
    return filtered_df, filtered_period_info

def render_project_sidebar_filters(df):
    """Render filter controls in the sidebar and return filter parameters.
    
    Parameters:
    df (DataFrame): DataFrame containing the project data
    
    Returns:
    tuple: (filtered_df, filtered_period_info, selected_project)
    """
    filtered_df = df.copy()
    filtered_period_info = {}
    
    # Create a container for filter controls
    
    # Period filter (renders directly to sidebar)
    period_filter_params = render_project_period_filters(filtered_df)
    filtered_df, filtered_period_info = apply_project_period_filter(filtered_df, period_filter_params)
    
    # Project selection (1st filter)
    with st.sidebar.expander(t('filter_project_name_header'), expanded=True):
        # Initialize session state
        all_projects_option = t('filter_all_projects')
        if 'selected_project' not in st.session_state:
            st.session_state.selected_project = all_projects_option
        
        unique_projects = filtered_df["Project Name"].unique()
        # Convert all project names to strings to avoid comparison errors
        unique_projects_str = sorted([str(p) for p in unique_projects])
        
        # Project inclusion filter (multiselect for multiple projects)
        included_projects = st.multiselect(
            t("filter_select_project"),
            options=unique_projects_str,
            help="Select specific projects to include in visualization",
            key="included_projects"
        )
        
        # Project exclusion filter
        excluded_projects = st.multiselect(
            t("filter_exclude_projects"),
            options=unique_projects_str,
            help=t("filter_exclude_projects_help"),
            key="excluded_projects"
        )

        # Apply filtering logic
        if included_projects:
            # If specific projects are included, filter to only those
            filtered_df = filtered_df[filtered_df["Project Name"].astype(str).isin(included_projects)]
        
        if excluded_projects:
            # Remove excluded projects
            filtered_df = filtered_df[~filtered_df["Project Name"].astype(str).isin(excluded_projects)]
        
        # For compatibility with existing code, return the "All Projects" option if no specific projects selected
        selected_project = all_projects_option if not included_projects else included_projects[0] if len(included_projects) == 1 else "Multiple Projects"
    
    # Project type filtering (2nd filter)
    if "Project type" in filtered_df.columns:
        with st.sidebar.expander(t('filter_project_type_header')):
            # Get unique project types
            unique_project_types = sorted(filtered_df["Project type"].dropna().unique().tolist())
            
            # Include dropdown (single column layout)
            include_types = st.multiselect(
                t('filter_include_types'),
                options=unique_project_types,
                help=t('filter_include_types_help')
            )
            
            # Exclude dropdown (single column layout)
            # Filter out types that are already in the include list to avoid conflicts
            exclude_options = [t for t in unique_project_types if t not in include_types]
            exclude_types = st.multiselect(
                t('filter_exclude_types'),
                options=exclude_options,
                help=t('filter_exclude_types_help')
            )
            
            # Apply filters
            if include_types:
                # Include only selected project types
                filtered_df = filtered_df[filtered_df["Project type"].isin(include_types)]
            
            if exclude_types:
                # Exclude selected project types
                filtered_df = filtered_df[~filtered_df["Project type"].isin(exclude_types)]
            
            # Show how many projects match the filters
            if include_types or exclude_types:
                st.info(f"{len(filtered_df['Project Name'].unique())} {t('filter_projects_match')}")
    
    # Created date filtering (3rd filter)
    if "Created" in filtered_df.columns:
        with st.sidebar.expander(t('filter_created_header')):
            try:
                # Convert Created column to datetime
                filtered_df["Created"] = pd.to_datetime(filtered_df["Created"], errors='coerce')
                
                # Get min and max creation dates
                min_creation_date = filtered_df["Created"].min().date()
                max_creation_date = filtered_df["Created"].max().date()
                
                # Create two columns for start and end date
                start_col, end_col = st.columns(2)
                
                # Start date picker
                with start_col:
                    start_date = st.date_input(
                        t('filter_start_date'),
                        value=min_creation_date
                    )
                
                # End date picker
                with end_col:
                    end_date = st.date_input(
                        t('filter_end_date'),
                        value=max_creation_date
                    )
                
                # Filter to only include projects created within the selected date range
                valid_projects = filtered_df[
                    (filtered_df["Created"].dt.date >= start_date) & 
                    (filtered_df["Created"].dt.date <= end_date)
                ]["Project Name"].unique()
                
                # Filter the dataframe to only include these projects
                filtered_df = filtered_df[filtered_df["Project Name"].isin(valid_projects)]
                
                st.info(f"{t('filter_showing_projects')} {len(valid_projects)} {t('filter_projects_created_between')} {start_date} {t('filter_and')} {end_date}")
            except Exception as e:
                st.warning(f"{t('filter_creation_date_error')} {str(e)}")
    
    return filtered_df, filtered_period_info, selected_project


def handle_project_upload():
    """Handle the upload of project CSV data and render charts and table."""
    # Check if data already exists in session state
    if st.session_state.project_data is None:
        # Try to autoload data first
        autoloaded_data = try_autoload_project_data()
        
        if autoloaded_data is not None:
            # Store autoloaded data in session state
            st.session_state.project_data = autoloaded_data
            project_df = autoloaded_data
        else:
            # No data found - show error message
            st.error("📂 No project data found in /data directory")
            st.markdown("""
            **To view project reports, place a CSV file in the `/data` directory with one of these naming patterns:**
            - `*project_report*.csv`
            - `project*.csv`
            - `prosjekt*.csv`
            
            **Expected CSV structure:**
            - Period
            - Project ID
            - Project Name
            - Period Hours
            - Planned Hours
            - Period Fees
            - Planned Income
            """)
            return
    else:
        # Use existing data from session state
        project_df = st.session_state.project_data
            
    # Check required columns
    project_columns = [
        "Project ID", "Project Name", "Period", "Period Hours",
        "Planned Hours", "Period Fees Adjusted", "Planned Income"
    ]
            
    missing_columns = [col for col in project_columns if col not in project_df.columns]
    
    if missing_columns:
        st.warning(f"{t('filter_missing_columns')} {', '.join(missing_columns)}")
        st.info(t('filter_upload_correct_csv') if 'filter_upload_correct_csv' in st.session_state.translations 
               else "Please upload a CSV with the correct data structure.")
        return
    
    # Create Period column from Period if needed
    if "Period" in project_df.columns:
        try:
            project_df["Period"] = pd.to_datetime(project_df["Period"], errors='coerce')
            # Check if conversion was successful
            if project_df["Period"].isna().all():
                st.warning(t('filter_period_conversion_error') if 'filter_period_conversion_error' in st.session_state.translations 
                          else "Could not convert any Period values to datetime format")
                # Create a dummy Period column with the current date to avoid errors
                project_df["Period"] = pd.Timestamp.now()
        except Exception as e:
            st.warning(f"{t('filter_period_error')} {str(e)}")
            # Create a dummy Period column with the current date to avoid errors
            project_df["Period"] = pd.Timestamp.now()

    # Apply sidebar filters
    filtered_df, filtered_period_info, selected_project = render_project_sidebar_filters(project_df)
    
    # Create tabs for different views
    hours_tab, fees_tab, rate_tab = st.tabs([
        t("hours_project"),
        t("fees_project"),
        t("rate_project")
    ])
    
    # Get the translated "All Projects" option once
    all_projects_option = t('filter_all_projects')
    
    with hours_tab:
        # Header removed - tab name already indicates content
        render_project_hours_chart(filtered_df, selected_project, all_projects_option)

    with fees_tab:
        # Header removed - tab name already indicates content
        render_project_fees_chart(filtered_df, selected_project, all_projects_option)

    with rate_tab:
        # Header removed - tab name already indicates content
        render_project_rate_chart(filtered_df, selected_project, all_projects_option)

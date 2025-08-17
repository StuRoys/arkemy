import streamlit as st
import pandas as pd
import numpy as np
import os
import glob
from period_translations.translations import t
from period_charts.project_hours import render_project_hours_chart
from period_charts.project_fees import render_project_fees_chart
from period_charts.project_rate import render_project_rate_chart

def try_autoload_project_data():
    """Try to autoload project data from /data directory."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    # Look for CSV files that might contain project data
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
            project_columns = ['Project ID', 'Project Name', 'Period Hours', 'Period Fees']
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
        "Planned Hours", "Period Fees", "Planned Income"
    ]
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        st.error(f"{t('missing_required_columns')}: {', '.join(missing_columns)}")
        return
    
    # Translation mapping for columns
    translation_mapping = {
        "Project ID": t("project_id") if "project_id" in st.session_state.translations else "Project ID",
        "Project Name": t("project_name") if "project_name" in st.session_state.translations else "Project Name",
        "Period": t("period_label") if "period_label" in st.session_state.translations else "Period",
        "Period Hours": t("period_hours") if "period_hours" in st.session_state.translations else "Period Hours",
        "Planned Hours": t("planned_hours"),
        "Period Fees": t("period_fees") if "period_fees" in st.session_state.translations else "Period Fees",
        "Planned Income": t("planned_income") if "planned_income" in st.session_state.translations else "Planned Income",
   }
    
    # Create a display copy with translated column names
    display_df = df.copy()
    display_df = display_df.rename(columns=translation_mapping)
    
    # Create column config for special formatting
    column_config = {}
    
    # Add number formatting for currency columns
    fees_translated = translation_mapping["Period Fees"]
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
        [t('month'), t('quarters'), t('year')],
        horizontal=True,
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
        
        selected_year = st.sidebar.selectbox(
            t('select_year'), 
            years,
            index=year_default_index
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
        
        selected_month_name = st.sidebar.selectbox(
            t('select_month'),
            available_month_names,
            index=default_month_index
        )
        
        # Convert month name back to number for filtering
        selected_month_num = available_month_numbers[available_month_names.index(selected_month_name)]
        
        filter_params['year'] = selected_year
        filter_params['month'] = selected_month_num
    
    elif period_filter == t('quarters'):
        # Get list of years in the data
        years = sorted(df["Period"].dt.year.unique())
        selected_year = st.sidebar.selectbox(t('select_year'), years)
        
        # Quarter selection
        quarters = [t('q1'), t('q2'), t('q3'), t('q4')]
        selected_quarter = st.sidebar.selectbox(t('select_quarter'), quarters)
        
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
        
        # Filter for selected year and quarter
        year_filter = filtered_df["Period"].dt.year == selected_year
        quarter_filter = filtered_df["Period"].dt.quarter == quarter_num
        filtered_df = filtered_df[year_filter & quarter_filter]
        
        filtered_period_info['year'] = selected_year
        filtered_period_info['quarter'] = quarter_num
    
    elif filter_type == t('year'):
        selected_year = filter_params.get('year')
        if selected_year:
            # Filter for selected year
            filtered_df = filtered_df[filtered_df["Period"].dt.year == selected_year]
            filtered_period_info['year'] = selected_year
    
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
    st.sidebar.header(t('filter_data') if 'filter_data' in st.session_state.translations else "Filter Data")
    
    # Period filter in an expander
    with st.sidebar.expander(t('filter_period_header') if 'filter_period_header' in st.session_state.translations else "Period Filter", expanded=True):
        # Use the new clean period filter function
        period_filter_params = render_project_period_filters(filtered_df)
        filtered_df, filtered_period_info = apply_project_period_filter(filtered_df, period_filter_params)
    
    # Created date filtering
    if "Created" in filtered_df.columns:
        with st.sidebar.expander(t('filter_created_header') if 'filter_created_header' in st.session_state.translations else "Project Created"):
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
                        t('filter_start_date') if 'filter_start_date' in st.session_state.translations else "Start Date",
                        value=min_creation_date
                    )
                
                # End date picker
                with end_col:
                    end_date = st.date_input(
                        t('filter_end_date') if 'filter_end_date' in st.session_state.translations else "End Date",
                        value=max_creation_date
                    )
                
                # Filter to only include projects created within the selected date range
                valid_projects = filtered_df[
                    (filtered_df["Created"].dt.date >= start_date) & 
                    (filtered_df["Created"].dt.date <= end_date)
                ]["Project Name"].unique()
                
                # Filter the dataframe to only include these projects
                filtered_df = filtered_df[filtered_df["Project Name"].isin(valid_projects)]
                
                st.info(f"{t('filter_showing_projects') if 'filter_showing_projects' in st.session_state.translations else 'Showing'} {len(valid_projects)} {t('filter_projects_created_between') if 'filter_projects_created_between' in st.session_state.translations else 'projects created between'} {start_date} {t('filter_and') if 'filter_and' in st.session_state.translations else 'and'} {end_date}")
            except Exception as e:
                st.warning(f"{t('filter_creation_date_error') if 'filter_creation_date_error' in st.session_state.translations else 'Error applying creation date filter:'} {str(e)}")
    
    # Project type filtering
    if "Project type" in filtered_df.columns:
        with st.sidebar.expander(t('filter_project_type_header') if 'filter_project_type_header' in st.session_state.translations else "Project Type"):
            # Get unique project types
            unique_project_types = sorted(filtered_df["Project type"].dropna().unique().tolist())
            
            # Create two columns for include and exclude
            include_col, exclude_col = st.columns(2)
            
            # Include dropdown
            with include_col:
                include_types = st.multiselect(
                    t('filter_include_types') if 'filter_include_types' in st.session_state.translations else "Include Types",
                    options=unique_project_types,
                    help=t('filter_include_types_help') if 'filter_include_types_help' in st.session_state.translations else "Only show projects of these types"
                )
            
            # Exclude dropdown
            with exclude_col:
                # Filter out types that are already in the include list to avoid conflicts
                exclude_options = [t for t in unique_project_types if t not in include_types]
                exclude_types = st.multiselect(
                    t('filter_exclude_types') if 'filter_exclude_types' in st.session_state.translations else "Exclude Types",
                    options=exclude_options,
                    help=t('filter_exclude_types_help') if 'filter_exclude_types_help' in st.session_state.translations else "Hide projects of these types"
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
                st.info(f"{len(filtered_df['Project Name'].unique())} {t('filter_projects_match') if 'filter_projects_match' in st.session_state.translations else 'projects match your filters'}")
    
    # Project selection
    with st.sidebar.expander(t('filter_project_name_header') if 'filter_project_name_header' in st.session_state.translations else "Project Name", expanded=True):
        # Initialize session state
        all_projects_option = t('filter_all_projects') if 'filter_all_projects' in st.session_state.translations else "All Projects"
        if 'selected_project' not in st.session_state:
            st.session_state.selected_project = all_projects_option
        
        unique_projects = filtered_df["Project Name"].unique()
        # Convert all project names to strings to avoid comparison errors
        unique_projects_str = sorted([str(p) for p in unique_projects])
        
        # Create two columns for selection and exclusion
        select_col, exclude_col = st.columns(2)
        
        # Project exclusion filter (handle this FIRST)
        with exclude_col:
            excluded_projects = st.multiselect(
                t("filter_exclude_projects") if "filter_exclude_projects" in st.session_state.translations else "Exclude",
                options=unique_projects_str,
                help=t("filter_exclude_projects_help") if "filter_exclude_projects_help" in st.session_state.translations else "Projects to exclude from visualization",
                key="excluded_projects"
            )

        # Apply exclusion filtering to dataframe
        if excluded_projects:
            filtered_df = filtered_df[~filtered_df["Project Name"].astype(str).isin(excluded_projects)]
            # Update available projects after exclusion
            remaining_projects = filtered_df["Project Name"].unique()
            remaining_projects_str = sorted([str(p) for p in remaining_projects])
        else:
            remaining_projects_str = unique_projects_str

        # Create project list for selectbox (after exclusions applied)
        project_list = [all_projects_option] + remaining_projects_str

        # Validate current selection - if selected project was excluded, reset to All Projects
        if st.session_state.selected_project not in project_list:
            st.session_state.selected_project = all_projects_option
            
        # Find the proper index for the selectbox
        selected_index = 0
        if st.session_state.selected_project in project_list:
            selected_index = project_list.index(st.session_state.selected_project)

        # Create project selection dropdown
        with select_col:
            selected_project = st.selectbox(
                t("filter_select_project") if "filter_select_project" in st.session_state.translations else "Select Project",
                project_list,
                index=selected_index,
                key="selected_project"  # Use same key as session state
            )
    
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
            # Create file uploader for project data as fallback
            project_file = st.file_uploader(
                t('filter_upload_project_csv') if 'filter_upload_project_csv' in st.session_state.translations 
                else "Upload your project CSV file here",
                type=["csv"],
                key="project_csv_uploader"
            )
            
            if project_file is None:
                # Show only upload instruction
                st.info("📂 No project data found in /data directory. " + 
                       (t('filter_upload_instruction') if 'filter_upload_instruction' in st.session_state.translations 
                        else "Please upload a CSV file with project data to view charts and tables."))
                
                # Display expected CSV structure
                with st.expander(t('filter_expected_structure') if 'filter_expected_structure' in st.session_state.translations 
                                else "Expected CSV structure"):
                    st.markdown(t('filter_csv_structure') if 'filter_csv_structure' in st.session_state.translations else """
                    Your CSV file should have the following columns:
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
                # Read the uploaded CSV file
                project_df = pd.read_csv(project_file)
                # Store in session state
                st.session_state.project_data = project_df
                st.rerun()
    else:
        # Use existing data from session state
        project_df = st.session_state.project_data
            
    # Check required columns
    project_columns = [
        "Project ID", "Project Name", "Period", "Period Hours",
        "Planned Hours", "Period Fees", "Planned Income"
    ]
            
    missing_columns = [col for col in project_columns if col not in project_df.columns]
    
    if missing_columns:
        st.warning(f"{t('filter_missing_columns') if 'filter_missing_columns' in st.session_state.translations else 'Missing columns:'} {', '.join(missing_columns)}")
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
            st.warning(f"{t('filter_period_error') if 'filter_period_error' in st.session_state.translations else 'Could not convert Period to datetime:'} {str(e)}")
            # Create a dummy Period column with the current date to avoid errors
            project_df["Period"] = pd.Timestamp.now()

    # Apply sidebar filters
    filtered_df, filtered_period_info, selected_project = render_project_sidebar_filters(project_df)
    
    # Create tabs for different views
    hours_tab, fees_tab, rate_tab, data_tab = st.tabs([
        t("hours_project") if "hours_project" in st.session_state.translations else "Project Hours",
        t("fees_project") if "fees_project" in st.session_state.translations else "Project fees",
        t("rate_project") if "rate_project" in st.session_state.translations else "Project rate",
        t("data")
    ])
    
    # Get the translated "All Projects" option once
    all_projects_option = t('filter_all_projects') if 'filter_all_projects' in st.session_state.translations else "All Projects"
    
    with hours_tab:
        st.header(t("project_hours_chart") if "project_hours_chart" in st.session_state.translations 
                else "Project Hours")
        render_project_hours_chart(filtered_df, selected_project, all_projects_option)
    
    with fees_tab:
        st.header(t("project_fees_chart") if "project_fees_chart" in st.session_state.translations 
                else "Project Fees")
        render_project_fees_chart(filtered_df, selected_project, all_projects_option)
    
    with rate_tab:
        st.header(t("project_rate_chart") if "project_rate_chart" in st.session_state.translations 
                else "Project Rate")
        render_project_rate_chart(filtered_df, selected_project, all_projects_option)
    
    with data_tab:
        st.header(t("project_data") if "project_data" in st.session_state.translations else "Project Data")
        
        # Filter the dataframe by selected project if not "All Projects"
        all_projects_option = t('filter_all_projects') if 'filter_all_projects' in st.session_state.translations else "All Projects"
        if selected_project != all_projects_option:
            display_df = filtered_df[filtered_df["Project Name"].astype(str) == selected_project]
        else:
            display_df = filtered_df
        
        # Create three dataframe displays
        st.subheader("Monthly")
        monthly_df = display_df.groupby(pd.to_datetime(display_df["Period"]).dt.to_period('M')).agg({
            "Period Hours": "sum",
            "Planned Hours": "sum", 
            "Period Fees": "sum",
            "Planned Income": "sum"
        }).reset_index()
        monthly_df["Period"] = monthly_df["Period"].dt.to_timestamp()
        render_project_table(monthly_df)
        
        st.subheader("Project")
        project_df = display_df.groupby(["Project ID", "Project Name"]).agg({
            "Period Hours": "sum",
            "Planned Hours": "sum",
            "Period Fees": "sum", 
            "Planned Income": "sum"
        }).reset_index()
        # Add Period column for consistency
        project_df["Period"] = "All Periods"
        render_project_table(project_df)
        
        st.subheader("Project per Month")
        project_per_month_df = create_project_per_month_table(display_df)
        render_project_table(project_per_month_df)
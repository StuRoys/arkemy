import streamlit as st
import pandas as pd
import datetime
import os
import glob
from period_charts.coworker_forecast import render_person_chart
from period_charts.coworker_comparison import render_comparison_chart
from period_charts.coworker_hours_flow import render_hours_flow_chart
from period_charts.coworker_utils import render_details_section, render_data_section
from period_translations.translations import t

def try_autoload_coworker_data():
    """Try to autoload coworker data from /data directory."""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    
    # Look for CSV files that might contain coworker data
    # Common patterns: coworker*.csv, person*.csv, employee*.csv, medarbeider*.csv (Norwegian)
    patterns = ['*coworker_report*.csv', 'coworker*.csv', 'person*.csv', 'employee*.csv', 'medarbeider*.csv', 'people*.csv']
    
    for pattern in patterns:
        files = glob.glob(os.path.join(data_dir, pattern))
        if files:
            # Use the first matching file
            filepath = files[0]
            try:
                df = pd.read_csv(filepath, usecols=lambda x: x != 'Unnamed: 0')
                return df
            except Exception as e:
                st.warning(f"Could not load {os.path.basename(filepath)}: {str(e)}")
                continue
    
    # If no pattern matches, try to load any CSV and check if it has coworker-like columns
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    for filepath in csv_files:
        try:
            df = pd.read_csv(filepath, usecols=lambda x: x != 'Unnamed: 0')
            # Check if it has typical coworker columns
            coworker_columns = ['Person', 'Hours/Period', 'Capacity/Period', 'Period']
            if any(col in df.columns for col in coworker_columns):
                return df
        except Exception as e:
            continue
    
    return None

def apply_period_filter(df, filter_type, filter_params):
    """
    Apply period filtering based on parameters.
    
    Parameters:
    df (DataFrame): The input DataFrame to filter
    filter_type (str): Type of filter ('month', 'quarters', 'year')
    filter_params (dict): Parameters for the filter
    
    Returns:
    tuple: (filtered_df, filtered_period_info)
    """
    filtered_df = df.copy()
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

def render_sidebar_filters(df=None):
    """
    Render filter controls in the sidebar and return filter parameters.
    
    Parameters:
    df (DataFrame, optional): DataFrame containing the data
    
    Returns:
    tuple: (filter_params, selected_person)
    """
    if df is None or df.empty:
        return None, None
    
    # Ensure Period is datetime
    if "Period" in df.columns and not pd.api.types.is_datetime64_any_dtype(df["Period"]):
        df["Period"] = pd.to_datetime(df["Period"], errors='coerce')
    
    # Get min and max dates from the data
    min_date = df["Period"].min()
    max_date = df["Period"].max()
    
    # Create a container for filter controls
    st.sidebar.header(t('filter_data'))
    
    # Period filter options
    period_filter = st.sidebar.radio(
        t('period'), 
        [t('month'), t('quarters'), t('year')],
        horizontal=True,
        key='coworker_period',
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
        
        # Default to most recent year
        default_index = 0 if years else 0
        
        selected_year = st.sidebar.selectbox(
            t('select_year'), 
            years,
            index=default_index
        )
        filter_params['year'] = selected_year
    
    # Person selection
    if "Person" in df.columns:
        st.sidebar.markdown("---")  # Divider
        
        # Get unique persons for dropdown
        persons = df["Person"].unique().tolist()
        
        # Reorder to put "All coworkers" first if it exists
        if "All coworkers" in persons:
            persons.remove("All coworkers")
            persons = ["All coworkers"] + persons
        
        # Dropdown for person selection
        selected_person = st.sidebar.selectbox(t('select_person'), persons, index=0)
    else:
        selected_person = None
    
    return filter_params, selected_person

def handle_coworker_upload(filter_params=None, selected_person=None):
    """
    Handle the upload of coworker CSV data and render charts and table.
    
    Parameters:
    filter_params (dict, optional): Parameters for filtering periods
    selected_person (str, optional): Selected person for filtering
    
    Returns:
    tuple: (filtered_period_info, selected_person)
    """
    # Initialize period filter info
    filtered_period_info = None
    
    # Check if data already exists in session state
    if st.session_state.coworker_data is None:
        # Try to autoload data first
        autoloaded_data = try_autoload_coworker_data()
        
        if autoloaded_data is not None:
            # Store autoloaded data in session state
            st.session_state.coworker_data = autoloaded_data
            df = autoloaded_data
        else:
            # No data found - show error message
            st.error("📂 No coworker data found in /data directory")
            st.markdown("""
            **To view coworker reports, place a CSV file in the `/data` directory with one of these naming patterns:**
            - `*coworker_report*.csv`
            - `coworker*.csv`
            - `person*.csv`
            - `employee*.csv`
            - `medarbeider*.csv`
            - `people*.csv`
            
            **Expected CSV structure:**
            - Period (in datetime format)
            - Person
            - Hours/Period
            - Capacity/Period
            - Absence/Period
            - Hours/Registered
            - Project hours
            - Planned hours
            - Unpaid work
            """)
            return filtered_period_info, selected_person
    else:
        # Use existing data from session state
        df = st.session_state.coworker_data
    
    # Ensure Period is in datetime format
    if "Period" in df.columns:
        df["Period"] = pd.to_datetime(df["Period"], errors='coerce')

    # Fill empty values in Capacity/Period with values from Hours/Period
    if "Capacity/Period" in df.columns and "Hours/Period" in df.columns:
        df["Capacity/Period"] = df["Capacity/Period"].fillna(df["Hours/Period"])

    # Create aggregated "All coworkers" data
    if "Person" in df.columns and "Period" in df.columns:
        # Identify all numeric columns in the dataframe for aggregation
        agg_columns = df.select_dtypes(include=['number']).columns.tolist()
        # Exclude any 'Person' or 'Period' columns if they happen to be numeric
        agg_columns = [col for col in agg_columns if col not in ['Person', 'Period']]
        
        # Only use columns that exist in the dataframe
        agg_columns = [col for col in agg_columns if col in df.columns]
        
        if agg_columns:
            # Group by Period and aggregate the numeric columns
            hele_kontoret_df = df.groupby("Period", as_index=False)[agg_columns].sum()
            
            # Add the Person column with value "All coworkers"
            hele_kontoret_df["Person"] = "All coworkers"
            
            # Add any other columns that might be in the original dataframe but not aggregated
            for col in df.columns:
                if col not in hele_kontoret_df.columns and col != "Person":
                    hele_kontoret_df[col] = None
            
            # Combine the original and aggregated dataframes
            df = pd.concat([df, hele_kontoret_df], ignore_index=True)

    # Render filters in sidebar and CSV is uploaded
    filter_params, selected_person = render_sidebar_filters(df)

    # Apply period filtering if parameters provided
    filtered_df = df.copy()
    if filter_params and "Period" in df.columns:
        filter_type = filter_params.get('type')
        filtered_df, filtered_period_info = apply_period_filter(df, filter_type, filter_params)
    elif "Period" not in df.columns:
        st.warning(t('no_period_column'))

    # If no person is selected (from sidebar), show warning
    if selected_person is None and "Person" in filtered_df.columns:
        st.warning(t('no_person_selected'))
    elif "Person" not in filtered_df.columns:
        st.warning(t('no_person_column'))
        
    # Create top-level tabs with the new order: Hours Flow, Comparison, Forecast, Help
    hours_flow_tab, comparison_tab, forecast_tab = st.tabs(["Hours Flow", "Comparison", t('forecast')])
    
    # Only proceed if a person is selected
    if selected_person:
        # Hours Flow tab (Sankey Diagram)
        with hours_flow_tab:
            person_filtered_df = render_hours_flow_chart(filtered_df, selected_person)
            render_details_section(person_filtered_df)
            render_data_section(person_filtered_df)
        
        # Comparison tab (Bar Chart)
        with comparison_tab:
            person_filtered_df = render_comparison_chart(filtered_df, selected_person)
            render_details_section(person_filtered_df)
            render_data_section(person_filtered_df)
        
        # Forecast tab
        with forecast_tab:
            person_filtered_df = render_person_chart(filtered_df, selected_person)
            render_details_section(person_filtered_df)
            render_data_section(person_filtered_df)
    else:
        with hours_flow_tab:
            st.warning(t('no_person_selected'))
        with comparison_tab:
            st.warning(t('no_person_selected'))
        with forecast_tab:
            st.warning(t('no_person_selected'))
    
    # Help tab removed - no longer needed
    
    return filtered_period_info, selected_person
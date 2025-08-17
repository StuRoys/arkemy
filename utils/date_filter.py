#file_date_filter.py
import streamlit as st
from datetime import datetime, date, timedelta
from typing import Tuple, Dict, Any
import calendar

def get_years_list(min_year: int = None, max_year: int = None) -> list:
    """Generate a list of years from dataset range, descending order (latest first)."""
    if min_year is None or max_year is None:
        current_year = datetime.now().year
        return list(range(current_year, current_year - 10, -1))
    
    # Create descending list from max to min year
    return list(range(max_year, min_year - 1, -1))

def get_quarters_list() -> list:
    """Get list of quarters."""
    return ['Q1', 'Q2', 'Q3', 'Q4']

def get_months_list() -> list:
    """Get list of months."""
    return [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]

def get_weeks_list(year: int) -> list:
    """Get list of weeks with date ranges for the given year."""
    weeks = []
    jan_first = date(year, 1, 1)
    
    # Find first Monday of the year
    days_after_monday = jan_first.weekday()
    if days_after_monday == 0:  # If Jan 1 is Monday
        first_monday = jan_first
    else:
        first_monday = jan_first + timedelta(days=(7 - days_after_monday))
    
    for week_num in range(1, 53):
        week_start = first_monday + timedelta(weeks=(week_num - 1))
        week_end = week_start + timedelta(days=6)
        
        # Stop if we've gone into the next year
        if week_start.year != year:
            break
            
        # Format: "Week 1 (Jan 2 - Jan 8)"
        start_str = week_start.strftime("%b %d")
        end_str = week_end.strftime("%b %d")
        weeks.append(f"Week {week_num} ({start_str} - {end_str})")
    
    return weeks

def get_previous_week_info(current_date: date = None) -> tuple:
    """Get previous week number and year."""
    if current_date is None:
        current_date = date.today()
    
    # Get previous week's date
    prev_week_date = current_date - timedelta(days=7)
    
    # Calculate week number
    jan_first = date(prev_week_date.year, 1, 1)
    days_after_monday = jan_first.weekday()
    if days_after_monday == 0:
        first_monday = jan_first
    else:
        first_monday = jan_first + timedelta(days=(7 - days_after_monday))
    
    # Calculate week number
    days_diff = (prev_week_date - first_monday).days
    week_num = (days_diff // 7) + 1
    
    return max(1, week_num), prev_week_date.year

def render_date_filter_ui(df_min_date: date = None, df_max_date: date = None) -> Dict[str, Any]:
    """
    Render the new date filter UI and return the selected configuration.
    
    Args:
        df_min_date: Minimum date from dataset
        df_max_date: Maximum date from dataset
    
    Returns:
        Dict containing the selected period type and specific selections
    """
    st.sidebar.markdown("### 🗓️ Date Range")
    
    # Period type selection
    period_types = ['Years', 'Quarters', 'Months', 'Weeks', 'Days']
    selected_period = st.sidebar.radio(
        "Select time period:",
        options=period_types,
        key='date_period_type'
    )
    
    current_year = datetime.now().year
    current_date = date.today()
    
    # Use dataset years if available, otherwise default range
    if df_min_date and df_max_date:
        min_year = df_min_date.year
        max_year = df_max_date.year
        years_list = get_years_list(min_year, max_year)
    else:
        years_list = get_years_list()
    
    result = {
        'period_type': selected_period,
        'current_year': current_year
    }
    
    if selected_period == 'Years':
        # Simple start/end year dropdowns
        col1, col2 = st.sidebar.columns(2)
        with col1:
            start_year = st.sidebar.selectbox(
                "Start year:",
                options=years_list,
                index=years_list.index(current_year) if current_year in years_list else 0,
                key='year_start'
            )
        with col2:
            end_year = st.sidebar.selectbox(
                "End year:",
                options=years_list,
                index=years_list.index(current_year) if current_year in years_list else 0,
                key='year_end'
            )
        result['year_start'] = start_year
        result['year_end'] = end_year
    
    elif selected_period == 'Quarters':
        col1, col2 = st.sidebar.columns(2)
        with col1:
            quarter_year = st.sidebar.selectbox(
                "Year:",
                options=years_list,
                index=years_list.index(current_year) if current_year in years_list else 0,
                key='quarter_year'
            )
        with col2:
            selected_quarter = st.sidebar.selectbox(
                "Quarter:",
                options=get_quarters_list(),
                key='selected_quarter'
            )
        result['selected_quarter'] = selected_quarter
        result['quarter_year'] = quarter_year
    
    elif selected_period == 'Months':
        col1, col2 = st.sidebar.columns(2)
        with col1:
            month_year = st.sidebar.selectbox(
                "Year:",
                options=years_list,
                index=years_list.index(current_year) if current_year in years_list else 0,
                key='month_year'
            )
        with col2:
            # Default to previous month
            prev_month = current_date.replace(day=1) - timedelta(days=1)
            default_month_index = prev_month.month - 1
            
            selected_month = st.sidebar.selectbox(
                "Month:",
                options=get_months_list(),
                index=default_month_index,
                key='selected_month'
            )
        result['selected_month'] = selected_month
        result['month_year'] = month_year
    
    elif selected_period == 'Weeks':
        col1, col2 = st.sidebar.columns(2)
        with col1:
            week_year = st.sidebar.selectbox(
                "Year:",
                options=years_list,
                index=years_list.index(current_year) if current_year in years_list else 0,
                key='week_year'
            )
        with col2:
            # Get weeks for the selected year with date ranges
            weeks_list = get_weeks_list(week_year)
            
            # Default to previous week
            prev_week_num, prev_week_year = get_previous_week_info(current_date)
            default_week_index = max(0, prev_week_num - 1) if week_year == prev_week_year else 0
            default_week_index = min(default_week_index, len(weeks_list) - 1)
            
            selected_week = st.sidebar.selectbox(
                "Week:",
                options=weeks_list,
                index=default_week_index,
                key='selected_week'
            )
        result['selected_week'] = selected_week
        result['week_year'] = week_year
    
    elif selected_period == 'Days':
        col1, col2 = st.sidebar.columns(2)
        
        # Set date range limits based on dataset
        min_date_limit = df_min_date if df_min_date else date(2020, 1, 1)
        max_date_limit = df_max_date if df_max_date else date(2030, 12, 31)
        
        # Smart defaults that respect dataset boundaries
        default_end = min(current_date, max_date_limit)  # Today or dataset max, whichever is smaller
        default_start_candidate = default_end - timedelta(days=30)  # 30 days before end
        default_start = max(default_start_candidate, min_date_limit)  # But not before dataset min
        
        with col1:
            start_date = st.sidebar.date_input(
                "Start date:",
                value=default_start,
                min_value=min_date_limit,
                max_value=max_date_limit,
                key='day_start'
            )
        with col2:
            end_date = st.sidebar.date_input(
                "End date:",
                value=default_end,
                min_value=min_date_limit,
                max_value=max_date_limit,
                key='day_end'
            )
        result['start_date'] = start_date
        result['end_date'] = end_date
    
    return result

def calculate_date_range(filter_config: Dict[str, Any]) -> Tuple[date, date]:
    """
    Calculate start and end dates based on the filter configuration.
    
    Args:
        filter_config: Dictionary containing the selected period type and specific selections
        
    Returns:
        Tuple of (start_date, end_date) as date objects
    """
    period_type = filter_config['period_type']
    
    if period_type == 'Years':
        return _calculate_year_range(filter_config)
    elif period_type == 'Quarters':
        return _calculate_quarter_range(filter_config)
    elif period_type == 'Months':
        return _calculate_month_range(filter_config)
    elif period_type == 'Weeks':
        return _calculate_week_range(filter_config)
    elif period_type == 'Days':
        return _calculate_day_range(filter_config)
    else:
        raise ValueError(f"Unknown period type: {period_type}")

def _calculate_year_range(config: Dict[str, Any]) -> Tuple[date, date]:
    """Calculate date range for year selections."""
    start_year = config['year_start']
    end_year = config['year_end']
    
    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    
    return start_date, end_date

def _calculate_quarter_range(config: Dict[str, Any]) -> Tuple[date, date]:
    """Calculate date range for quarter selections."""
    quarter = config['selected_quarter']
    year = config['quarter_year']
    
    quarter_num = int(quarter[1])  # Extract number from 'Q1', 'Q2', etc.
    
    # Calculate start month of quarter
    start_month = (quarter_num - 1) * 3 + 1
    
    # Start date is first day of first month in quarter
    start_date = date(year, start_month, 1)
    
    # End date is last day of last month in quarter
    end_month = start_month + 2
    _, last_day = calendar.monthrange(year, end_month)
    end_date = date(year, end_month, last_day)
    
    return start_date, end_date

def _calculate_month_range(config: Dict[str, Any]) -> Tuple[date, date]:
    """Calculate date range for month selections."""
    month_name = config['selected_month']
    year = config['month_year']
    
    # Convert month name to number
    month_names = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December'
    ]
    month_num = month_names.index(month_name) + 1
    
    # Start date is first day of month
    start_date = date(year, month_num, 1)
    
    # End date is last day of month
    _, last_day = calendar.monthrange(year, month_num)
    end_date = date(year, month_num, last_day)
    
    return start_date, end_date

def _calculate_week_range(config: Dict[str, Any]) -> Tuple[date, date]:
    """Calculate date range for week selections."""
    week_str = config['selected_week']
    year = config['week_year']
    
    # Extract week number from 'Week N (date range)'
    week_num = int(week_str.split()[1])
    
    # Find the first Monday of the year (ISO week calculation)
    jan_first = date(year, 1, 1)
    
    # Find first Monday
    days_after_monday = jan_first.weekday()
    if days_after_monday == 0:  # If Jan 1 is Monday
        first_monday = jan_first
    else:
        first_monday = jan_first + timedelta(days=(7 - days_after_monday))
    
    # Calculate start date of the requested week
    start_date = first_monday + timedelta(weeks=(week_num - 1))
    
    # End date is 6 days later (Sunday)
    end_date = start_date + timedelta(days=6)
    
    return start_date, end_date

def _calculate_day_range(config: Dict[str, Any]) -> Tuple[date, date]:
    """Calculate date range for day selections."""
    start_date = config['start_date']
    end_date = config['end_date']
    
    return start_date, end_date

def get_date_range_description(filter_config: Dict[str, Any]) -> str:
    """
    Get a human-readable description of the selected date range.
    
    Args:
        filter_config: Dictionary containing the selected period type and specific selections
        
    Returns:
        String description of the date range
    """
    period_type = filter_config['period_type']
    
    if period_type == 'Years':
        start_year = filter_config['year_start']
        end_year = filter_config['year_end']
        if start_year == end_year:
            return f"{start_year}"
        else:
            return f"{start_year} - {end_year}"
    
    elif period_type == 'Quarters':
        return f"{filter_config['selected_quarter']} {filter_config['quarter_year']}"
    
    elif period_type == 'Months':
        return f"{filter_config['selected_month']} {filter_config['month_year']}"
    
    elif period_type == 'Weeks':
        week_str = filter_config['selected_week']
        year = filter_config['week_year']
        return f"{week_str}, {year}"
    
    elif period_type == 'Days':
        start_date = filter_config['start_date']
        end_date = filter_config['end_date']
        if start_date == end_date:
            return start_date.strftime("%Y-%m-%d")
        else:
            return f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
    
    return "Unknown"
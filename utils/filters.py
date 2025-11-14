# filters.py - Updated to use new date filter
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple, Any, Set
from utils.date_filter import render_date_filter_ui, calculate_date_range, get_date_range_description


def trigger_rerun():
    """Update indicators - Streamlit will automatically rerun when widgets change"""
    # No manual st.rerun() needed - Streamlit automatically reruns on widget changes
    # This function is kept for compatibility but no longer forces reruns
    pass


def clear_rerun_lock():
    """Clear the rerun lock if it exists - legacy function kept for compatibility"""
    if 'indicator_rerun_lock' in st.session_state:
        del st.session_state.indicator_rerun_lock


def create_date_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create BI-friendly date range filters for the dataframe."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'record_date' not in df.columns:
        st.error("record_date column not found in data")
        return df, filter_settings
    
    if not pd.api.types.is_datetime64_any_dtype(df['record_date']):
        df['record_date'] = pd.to_datetime(df['record_date'])
    
    min_date = df['record_date'].min().date()
    max_date = df['record_date'].max().date()
    
    # Handle planned max date extension
    planned_max_date_exists = 'planned_max_date' in st.session_state
    if planned_max_date_exists and st.session_state.planned_max_date > max_date:
        planned_max_date = st.session_state.planned_max_date
    else:
        planned_max_date = max_date
    
    # Render the new date filter UI with dataset date range
    filter_config = render_date_filter_ui(min_date, max_date)
    
    # Calculate the actual date range
    try:
        start_date, end_date = calculate_date_range(filter_config)
        
        # Extend end date for planned hours if needed
        extended_for_planned = False
        if planned_max_date_exists and planned_max_date > max_date:
            if end_date >= max_date:  # Only extend if our range goes to current data
                end_date = planned_max_date
                extended_for_planned = True
        
        # Show selected range info
        range_description = get_date_range_description(filter_config)
        st.sidebar.info(f"📅 Selected: {range_description}")
        
        if extended_for_planned:
            st.sidebar.info(f"📊 Extended to include planned hours (up to {planned_max_date})")
        
    except Exception as e:
        st.sidebar.error(f"Error calculating date range: {str(e)}")
        start_date = min_date
        end_date = max_date
        range_description = "Error in selection"
    
    # Apply the filter
    mask = (df['record_date'].dt.date >= start_date) & (df['record_date'].dt.date <= end_date)
    filtered_df = df[mask]
    
    # Update filter settings for compatibility with existing code
    filter_settings.update({
        'date_filter_config': filter_config,
        'date_filter_type': range_description,  # For backward compatibility
        'start_date': start_date,
        'end_date': end_date,
        'date_range_description': range_description,
        'date_active': True,  # Always active since we always have a selection
        'includes_planned_future_dates': (
            planned_max_date_exists and planned_max_date > max_date and end_date >= max_date
        ),
        'extended_for_planned': extended_for_planned
    })
    
    return filtered_df, filter_settings


def create_customer_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create customer filter with empty selection meaning 'All'"""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'customer_number' not in df.columns or 'customer_name' not in df.columns:
        return df, filter_settings
    
    customers = df[['customer_number', 'customer_name']].dropna().drop_duplicates()
    customers['Customer'] = customers['customer_name'] + ' (' + customers['customer_number'] + ')'
    customer_options = sorted(customers['Customer'].tolist())
    
    # Use current state for indicator
    current_included = st.session_state.get('customer_included', [])
    current_excluded = st.session_state.get('customer_excluded', [])
    indicator = " 🔴" if (current_included or current_excluded) else ""
    
    with st.sidebar.expander(f"Customer{indicator}"):
        selected_customers = st.multiselect(
            "Select specific customers",
            options=customer_options,
            default=current_included,
            key='customer_included',
            on_change=trigger_rerun
        )
        
        exclude_customers = st.multiselect(
            "Exclude customers",
            options=customer_options,
            default=current_excluded,
            key='customer_excluded',
            on_change=trigger_rerun
        )
    
    filtered_df = df.copy()
    
    if selected_customers:
        included_ids = [c.split('(')[-1].split(')')[0] for c in selected_customers if c and '(' in c and ')' in c]
        filtered_df = filtered_df[filtered_df['customer_number'].isin(included_ids)]
    
    if exclude_customers:
        excluded_ids = [c.split('(')[-1].split(')')[0] for c in exclude_customers if c and '(' in c and ')' in c]
        filtered_df = filtered_df[~filtered_df['customer_number'].isin(excluded_ids)]
    
    filter_settings['include_all_customers'] = len(selected_customers) == 0
    filter_settings['included_customers'] = [c.split('(')[-1].split(')')[0] for c in selected_customers]
    filter_settings['excluded_customers'] = [c.split('(')[-1].split(')')[0] for c in exclude_customers]
    filter_settings['customer_active'] = len(selected_customers) > 0 or len(exclude_customers) > 0
    
    return filtered_df, filter_settings


def create_project_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create project filters for the dataframe with include/exclude options."""
    clear_rerun_lock()
    filter_settings = {}
    
    has_project_data = 'project_number' in df.columns and 'project_name' in df.columns
    if not has_project_data:
        return df, filter_settings
    
    projects = df[['project_number', 'project_name']].dropna().drop_duplicates()
    projects['Project label'] = projects['project_name'] + ' (' + projects['project_number'] + ')'
    project_options = sorted(projects['Project label'].tolist())
    
    current_included = st.session_state.get('project_included', [])
    current_excluded = st.session_state.get('project_excluded', [])
    indicator = " 🔴" if (current_included or current_excluded) else ""
    
    with st.sidebar.expander(f"Project{indicator}"):
        selected_projects = st.multiselect(
            "Select specific projects",
            options=project_options,
            default=current_included,
            key='project_included',
            on_change=trigger_rerun
        )
        
        exclude_projects = st.multiselect(
            "Exclude projects",
            options=project_options,
            default=current_excluded,
            key='project_excluded',
            on_change=trigger_rerun
        )
    
    filtered_df = df.copy()
    
    if selected_projects:
        included_ids = [p.split('(')[-1].split(')')[0] for p in selected_projects if p and '(' in p and ')' in p]
        filtered_df = filtered_df[filtered_df['project_number'].isin(included_ids)]
    
    if exclude_projects:
        excluded_ids = [p.split('(')[-1].split(')')[0] for p in exclude_projects if p and '(' in p and ')' in p]
        filtered_df = filtered_df[~filtered_df['project_number'].isin(excluded_ids)]
    
    filter_settings['include_all_projects'] = len(selected_projects) == 0
    filter_settings['included_projects'] = [p.split('(')[-1].split(')')[0] for p in selected_projects]
    filter_settings['excluded_projects'] = [p.split('(')[-1].split(')')[0] for p in exclude_projects]
    filter_settings['project_active'] = len(selected_projects) > 0 or len(exclude_projects) > 0
    
    return filtered_df, filter_settings

def create_project_type_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create project type filter for multiple tag categories with include/exclude options."""
    clear_rerun_lock()
    filter_settings = {}

    # Get tag mappings from session state (extracted before filtering in render_sidebar_filters)
    tag_mappings = st.session_state.get('tag_mappings', {})

    if not tag_mappings:
        return df, filter_settings

    # Find all project_tag_* columns and get all unique values
    tag_columns = [col for col in df.columns if col.startswith('project_tag_')]

    if not tag_columns:
        return df, filter_settings

    # Collect all unique tag values with their category
    tag_options = []  # List of (category, value) tuples

    for tag_col in sorted(tag_columns):
        category_name = tag_mappings.get(tag_col, tag_col)
        for value in sorted(df[tag_col].dropna().unique().tolist()):
            tag_options.append((category_name, value))

    if not tag_options:
        return df, filter_settings

    # Create display function
    def format_tag_option(tag_tuple):
        category, value = tag_tuple
        return f"{category}: {value}"

    current_included = st.session_state.get('project_type_included', [])
    current_excluded = st.session_state.get('project_type_excluded', [])
    indicator = " 🔴" if (current_included or current_excluded) else ""

    with st.sidebar.expander(f"Project Type{indicator}"):
        selected_tags = st.multiselect(
            "Select specific project types",
            options=tag_options,
            default=current_included,
            key='project_type_included',
            format_func=format_tag_option,
            on_change=trigger_rerun
        )

        exclude_tags = st.multiselect(
            "Exclude project types",
            options=tag_options,
            default=current_excluded,
            key='project_type_excluded',
            format_func=format_tag_option,
            on_change=trigger_rerun
        )

    filtered_df = df.copy()

    # Apply include filter (match any tag column)
    if selected_tags:
        mask = pd.Series(False, index=filtered_df.index)
        for category, value in selected_tags:
            # Find which tag_col matches this category
            for tag_col in tag_columns:
                if tag_mappings.get(tag_col, tag_col) == category:
                    mask |= (filtered_df[tag_col] == value)
        filtered_df = filtered_df[mask]

    # Apply exclude filter (match any tag column)
    if exclude_tags:
        for category, value in exclude_tags:
            for tag_col in tag_columns:
                if tag_mappings.get(tag_col, tag_col) == category:
                    filtered_df = filtered_df[filtered_df[tag_col] != value]

    filter_settings['include_all_types'] = len(selected_tags) == 0
    filter_settings['included_types'] = selected_tags
    filter_settings['included_project_types'] = [v for _, v in selected_tags]  # For planned data
    filter_settings['excluded_types'] = exclude_tags
    filter_settings['excluded_project_types'] = [v for _, v in exclude_tags]
    filter_settings['project_type_active'] = len(selected_tags) > 0 or len(exclude_tags) > 0

    return filtered_df, filter_settings


def create_price_model_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create price model filter for the dataframe with include/exclude options."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'Price model' not in df.columns:
        return df, filter_settings
    
    price_models = sorted(df['Price model'].dropna().unique().tolist())
    
    current_included = st.session_state.get('price_model_included', [])
    current_excluded = st.session_state.get('price_model_excluded', [])
    indicator = " 🔴" if (current_included or current_excluded) else ""
    
    with st.sidebar.expander(f"Price Model{indicator}"):
        selected_models = st.multiselect(
            "Select specific price models",
            options=price_models,
            default=current_included,
            key='price_model_included',
            on_change=trigger_rerun
        )
        
        exclude_models = st.multiselect(
            "Exclude price models",
            options=price_models,
            default=current_excluded,
            key='price_model_excluded',
            on_change=trigger_rerun
        )
    
    filtered_df = df.copy()
    
    if selected_models:
        filtered_df = filtered_df[filtered_df['Price model'].isin(selected_models)]
    
    if exclude_models:
        filtered_df = filtered_df[~filtered_df['Price model'].isin(exclude_models)]
    
    filter_settings['include_all_models'] = len(selected_models) == 0
    filter_settings['included_models'] = selected_models
    filter_settings['excluded_models'] = exclude_models
    filter_settings['price_model_active'] = len(selected_models) > 0 or len(exclude_models) > 0
    
    return filtered_df, filter_settings

def create_activity_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create activity and phase filters for the dataframe with include/exclude options."""
    clear_rerun_lock()
    filter_settings = {}
    
    has_activity = 'activity_tag' in df.columns
    has_phase = 'phase_tag' in df.columns
    
    if not has_activity and not has_phase:
        return df, filter_settings
    
    filtered_df = df.copy()
    phase_active = False
    activity_active = False
    
    if has_phase:
        phases = sorted(df['phase_tag'].dropna().unique().tolist())
        current_included = st.session_state.get('phase_included', [])
        current_excluded = st.session_state.get('phase_excluded', [])
        indicator = " 🔴" if (current_included or current_excluded) else ""
        
        with st.sidebar.expander(f"Phase{indicator}"):
            selected_phases = st.multiselect(
                "Select specific phases",
                options=phases,
                default=current_included,
                key='phase_included',
                on_change=trigger_rerun
            )
            
            exclude_phases = st.multiselect(
                "Exclude phases",
                options=phases,
                default=current_excluded,
                key='phase_excluded',
                on_change=trigger_rerun
            )
        
        if selected_phases:
            filtered_df = filtered_df[filtered_df['phase_tag'].isin(selected_phases)]
        
        if exclude_phases:
            filtered_df = filtered_df[~filtered_df['phase_tag'].isin(exclude_phases)]
            
        filter_settings['include_all_phases'] = len(selected_phases) == 0
        filter_settings['included_phases'] = selected_phases
        filter_settings['excluded_phases'] = exclude_phases
        phase_active = len(selected_phases) > 0 or len(exclude_phases) > 0
    
    if has_activity:
        activities = sorted(filtered_df['activity_tag'].dropna().unique().tolist())
        current_included = st.session_state.get('activity_included', [])
        current_excluded = st.session_state.get('activity_excluded', [])
        indicator = " 🔴" if (current_included or current_excluded) else ""
        
        with st.sidebar.expander(f"Activity{indicator}"):
            selected_activities = st.multiselect(
                "Select specific activities",
                options=activities,
                default=current_included,
                key='activity_included',
                on_change=trigger_rerun
            )
            
            exclude_activities = st.multiselect(
                "Exclude activities",
                options=activities,
                default=current_excluded,
                key='activity_excluded',
                on_change=trigger_rerun
            )
        
        if selected_activities:
            filtered_df = filtered_df[filtered_df['activity_tag'].isin(selected_activities)]
        
        if exclude_activities:
            filtered_df = filtered_df[~filtered_df['activity_tag'].isin(exclude_activities)]
            
        filter_settings['include_all_activities'] = len(selected_activities) == 0
        filter_settings['included_activities'] = selected_activities
        filter_settings['excluded_activities'] = exclude_activities
        activity_active = len(selected_activities) > 0 or len(exclude_activities) > 0
    
    filter_settings['activity_active'] = phase_active or activity_active
    
    return filtered_df, filter_settings


def create_person_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create person filter for the dataframe with include/exclude options."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'person_name' not in df.columns:
        return df, filter_settings
    
    persons = sorted(df['person_name'].dropna().unique().tolist())
    
    current_included = st.session_state.get('person_included', [])
    current_excluded = st.session_state.get('person_excluded', [])
    indicator = " 🔴" if (current_included or current_excluded) else ""
    
    with st.sidebar.expander(f"Person{indicator}"):
        selected_persons = st.multiselect(
            "Select specific people",
            options=persons,
            default=current_included,
            key='person_included',
            on_change=trigger_rerun
        )
        
        exclude_persons = st.multiselect(
            "Exclude people",
            options=persons,
            default=current_excluded,
            key='person_excluded',
            on_change=trigger_rerun
        )
    
    filtered_df = df.copy()
    
    if selected_persons:
        filtered_df = filtered_df[filtered_df['person_name'].isin(selected_persons)]
    
    if exclude_persons:
        filtered_df = filtered_df[~filtered_df['person_name'].isin(exclude_persons)]
    
    filter_settings['include_all_persons'] = len(selected_persons) == 0
    filter_settings['included_persons'] = selected_persons
    filter_settings['excluded_persons'] = exclude_persons
    filter_settings['person_active'] = len(selected_persons) > 0 or len(exclude_persons) > 0
    
    return filtered_df, filter_settings

def create_person_type_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create person type filter for the dataframe."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'person_type' not in df.columns:
        return df, filter_settings
    
    current_selection = st.session_state.get('person_type_selection', "All")
    indicator = " 🔴" if current_selection != "All" else ""
    
    with st.sidebar.expander(f"Person Type (Internal/External){indicator}"):
        include_options = ["All", "Internal", "External"]
        selected_include = st.radio(
            "Include person types", 
            options=include_options, 
            index=include_options.index(current_selection) if current_selection in include_options else 0,
            key='person_type_selection',
            on_change=trigger_rerun
        )
    
    if selected_include == "Internal":
        # Use more robust boolean filtering to avoid NA ambiguity
        mask = df['person_type'].notna() & (df['person_type'].str.lower() == 'internal')
        filtered_df = df[mask]
        filter_settings['selected_person_type'] = 'internal'
    elif selected_include == "External":
        # Use more robust boolean filtering to avoid NA ambiguity
        mask = df['person_type'].notna() & (df['person_type'].str.lower() == 'external')
        filtered_df = df[mask]
        filter_settings['selected_person_type'] = 'external'
    else:
        filtered_df = df
        filter_settings['selected_person_type'] = 'all'
    
    filter_settings['person_type_active'] = selected_include != "All"
    
    return filtered_df, filter_settings


def create_project_hours_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Filter projects based on their total hours worked."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'project_number' not in df.columns or 'hours_used' not in df.columns:
        return df, filter_settings
    
    filtered_df = df.copy()
    project_hours = df.groupby('project_number')['hours_used'].sum().reset_index()
    total_projects = project_hours['project_number'].nunique()
    
    current_enabled = st.session_state.get('project_hours_enabled', False)
    indicator = " 🔴" if current_enabled else ""
    
    with st.sidebar.expander(f"Project Hours Range{indicator}"):
        enable_hours_filter = st.checkbox(
            "Enable hours filter", 
            value=current_enabled,
            key='project_hours_enabled',
            on_change=trigger_rerun
        )
        
        default_min = 0.0
        default_max = 100000.0
        
        col1, col2 = st.columns(2)
        with col1:
            min_selected_hours = st.number_input(
                "Min hours", min_value=0.0, max_value=default_max,
                value=st.session_state.get('project_hours_min', default_min), 
                step=0.1,
                key='project_hours_min'
            )
        with col2:
            max_selected_hours = st.number_input(
                "Max hours", min_value=0.0, max_value=default_max * 10,
                value=st.session_state.get('project_hours_max', default_max), 
                step=0.1,
                key='project_hours_max'
            )

        if enable_hours_filter:
            valid_projects = project_hours[
                (project_hours['hours_used'] >= min_selected_hours) & 
                (project_hours['hours_used'] <= max_selected_hours)
            ]['project_number'].tolist()
            
            projects_in_range = len(valid_projects)
            st.info(f"Showing {projects_in_range} of {total_projects} projects")

            if not valid_projects:
                st.warning("No projects found with hours in the selected range.")
                return pd.DataFrame(columns=df.columns), filter_settings

            filtered_df = filtered_df[filtered_df['project_number'].isin(valid_projects)]
            
            filter_settings['project_min_hours'] = min_selected_hours
            filter_settings['project_max_hours'] = max_selected_hours
            filter_settings['projects_in_range'] = projects_in_range
            filter_settings['project_hours_filter_enabled'] = True
        else:
            st.info(f"Filter disabled. Showing all {total_projects} projects.")
            filter_settings['project_hours_filter_enabled'] = False
    
    filter_settings['total_projects'] = total_projects
    filter_settings['project_hours_active'] = enable_hours_filter
    
    return filtered_df, filter_settings

def create_project_effective_rate_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Filter projects based on their effective hourly rate (fee / total hours)."""
    clear_rerun_lock()
    filter_settings = {}
    
    required_columns = ['project_number', 'hours_used', 'hours_billable', 'billable_rate_record']
    if not all(col in df.columns for col in required_columns):
        return df, filter_settings
    
    filtered_df = df.copy()
    
    project_rates = df.groupby('project_number').apply(
        lambda x: pd.Series({
            'Total hours': x['hours_used'].sum(),
            'Fee': (x['hours_billable'] * x['billable_rate_record']).sum(),
            'Effective rate': (x['hours_billable'] * x['billable_rate_record']).sum() / x['hours_used'].sum()
            if x['hours_used'].sum() > 0 else 0
        })
    ).reset_index()
    
    total_projects = project_rates['project_number'].nunique()
    
    current_enabled = st.session_state.get('project_rate_enabled', False)
    indicator = " 🔴" if current_enabled else ""
    
    with st.sidebar.expander(f"Project Effective Rate Range{indicator}"):
        enable_rate_filter = st.checkbox(
            "Enable effective rate filter", 
            value=current_enabled,
            key='project_rate_enabled',
            on_change=trigger_rerun
        )
        
        default_min = 0.0
        default_max = 10000.0
        
        col1, col2 = st.columns(2)
        with col1:
            min_selected_rate = st.number_input(
                "Min rate", min_value=0.0, max_value=default_max,
                value=st.session_state.get('project_rate_min', default_min), 
                step=1.0,
                key='project_rate_min'
            )
        with col2:
            max_selected_rate = st.number_input(
                "Max rate", min_value=0.0, max_value=default_max * 10,
                value=st.session_state.get('project_rate_max', default_max), 
                step=1.0,
                key='project_rate_max'
            )

        if enable_rate_filter:
            valid_projects = project_rates[
                (project_rates['Effective rate'] >= min_selected_rate) & 
                (project_rates['Effective rate'] <= max_selected_rate)
            ]['project_number'].tolist()
            
            projects_in_range = len(valid_projects)
            st.info(f"Showing {projects_in_range} of {total_projects} projects")

            if not valid_projects:
                st.warning("No projects found with effective rates in the selected range.")
                return pd.DataFrame(columns=df.columns), filter_settings

            filtered_df = filtered_df[filtered_df['project_number'].isin(valid_projects)]
            
            filter_settings['project_min_effective_rate'] = min_selected_rate
            filter_settings['project_max_effective_rate'] = max_selected_rate
            filter_settings['projects_in_rate_range'] = projects_in_range
            filter_settings['project_effective_rate_filter_enabled'] = True
        else:
            st.info(f"Filter disabled. Showing all {total_projects} projects.")
            filter_settings['project_effective_rate_filter_enabled'] = False
    
    filter_settings['total_projects'] = total_projects
    filter_settings['project_effective_rate_active'] = enable_rate_filter
    
    return filtered_df, filter_settings


def create_billability_filter(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Create billability filter for the dataframe."""
    clear_rerun_lock()
    filter_settings = {}
    
    if 'hours_used' not in df.columns or 'hours_billable' not in df.columns:
        return df, filter_settings
    
    current_selection = st.session_state.get('billability_selection', "All")
    indicator = " 🔴" if current_selection != "All" else ""
    
    with st.sidebar.expander(f"Billability{indicator}"):
        include_options = ["All", "Billable / Partially", "Non-billable"]
        selected_include = st.radio(
            "Include time records", 
            options=include_options, 
            index=include_options.index(current_selection) if current_selection in include_options else 0,
            key='billability_selection',
            on_change=trigger_rerun
        )
    
    if selected_include == "Billable / Partially":
        filtered_df = df[df['hours_billable'] > 0]
        filter_settings['selected_billability'] = 'billable'
    elif selected_include == "Non-billable":
        filtered_df = df[df['hours_billable'] == 0]
        filter_settings['selected_billability'] = 'non-billable'
    else:
        filtered_df = df
        filter_settings['selected_billability'] = 'all'
    
    filter_settings['billability_active'] = selected_include != "All"
    
    return filtered_df, filter_settings


def apply_all_filters(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Apply all filters to the dataframe."""
    filtered_df = df.copy()
    all_filter_settings = {}
    
    filter_functions = [
        create_date_filters, create_customer_filter, create_project_filter,
        create_project_type_filter, create_price_model_filter, create_activity_filter,
        create_person_filter, create_person_type_filter, create_project_hours_filter,
        create_project_effective_rate_filter, create_billability_filter
    ]
    
    for filter_func in filter_functions:
        try:
            filtered_df, new_settings = filter_func(filtered_df)
            all_filter_settings.update(new_settings)
            
            if filtered_df.empty:
                all_filter_settings['no_data'] = True
                return filtered_df, all_filter_settings
                
        except Exception as e:
            all_filter_settings['no_data'] = True
            return filtered_df, all_filter_settings
    
    all_filter_settings['no_data'] = filtered_df.empty
    return filtered_df, all_filter_settings
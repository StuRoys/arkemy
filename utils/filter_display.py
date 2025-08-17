# filter_display.py
import streamlit as st
from typing import Dict, Any

def display_filter_badges(filter_settings: Dict[str, Any], location: str = "main") -> None:
    """
    Displays badges for active filters in either main UI or sidebar.
    
    Args:
        filter_settings: Dictionary containing all active filter settings
        location: Where to display badges ("main" or "sidebar")
    """
    # Choose the right streamlit object based on location
    st_obj = st.sidebar if location == "sidebar" else st
    
    # Define filter categories and their corresponding emoji
    filter_categories = {
        "date": "🗓️",
        "customer": "👥",
        "project": "📋",
        "project_type": "📊",
        "phase": "🔄",
        "activity": "🔨",
        "person": "👤",
        "person_type": "🧑‍💼",  # New emoji for person type filter
        "project_hours": "⏱️",
        "project_rate": "💵",  # New emoji for project rate filter
        "billability": "💰"
    }
    
    # A list to collect all active filters
    active_filters = []
    
    # Date filter
    if 'date_filter_type' in filter_settings and filter_settings['date_filter_type'] != "All time":
        date_text = filter_settings['date_filter_type']
        if date_text == "Custom range":
            start_date = filter_settings.get('start_date')
            end_date = filter_settings.get('end_date')
            if start_date and end_date:
                date_text = f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        active_filters.append(f"{filter_categories['date']} Date: {date_text}")
    
    # Customer filters
    if 'included_customers' in filter_settings and filter_settings['included_customers']:
        num_customers = len(filter_settings['included_customers'])
        active_filters.append(f"{filter_categories['customer']} Customers: {num_customers} included")
    
    if 'excluded_customers' in filter_settings and filter_settings['excluded_customers']:
        num_customers = len(filter_settings['excluded_customers'])
        active_filters.append(f"{filter_categories['customer']} Customers: {num_customers} excluded")
    
    # Project filters
    if 'included_projects' in filter_settings and filter_settings['included_projects']:
        num_projects = len(filter_settings['included_projects'])
        active_filters.append(f"{filter_categories['project']} Projects: {num_projects} included")
    
    if 'excluded_projects' in filter_settings and filter_settings['excluded_projects']:
        num_projects = len(filter_settings['excluded_projects'])
        active_filters.append(f"{filter_categories['project']} Projects: {num_projects} excluded")
    
    # Project type filters
    if 'included_types' in filter_settings and filter_settings['included_types']:
        num_types = len(filter_settings['included_types'])
        active_filters.append(f"{filter_categories['project_type']} Project Types: {num_types} included")
    
    if 'excluded_types' in filter_settings and filter_settings['excluded_types']:
        num_types = len(filter_settings['excluded_types'])
        active_filters.append(f"{filter_categories['project_type']} Project Types: {num_types} excluded")
    
    # Phase filters
    if 'included_phases' in filter_settings and filter_settings['included_phases']:
        num_phases = len(filter_settings['included_phases'])
        active_filters.append(f"{filter_categories['phase']} Phases: {num_phases} included")
    
    if 'excluded_phases' in filter_settings and filter_settings['excluded_phases']:
        num_phases = len(filter_settings['excluded_phases'])
        active_filters.append(f"{filter_categories['phase']} Phases: {num_phases} excluded")
    
    # Activity filters
    if 'included_activities' in filter_settings and filter_settings['included_activities']:
        num_activities = len(filter_settings['included_activities'])
        active_filters.append(f"{filter_categories['activity']} Activities: {num_activities} included")
    
    if 'excluded_activities' in filter_settings and filter_settings['excluded_activities']:
        num_activities = len(filter_settings['excluded_activities'])
        active_filters.append(f"{filter_categories['activity']} Activities: {num_activities} excluded")
    
    # Person filters
    if 'included_persons' in filter_settings and filter_settings['included_persons']:
        num_persons = len(filter_settings['included_persons'])
        active_filters.append(f"{filter_categories['person']} People: {num_persons} included")
    
    if 'excluded_persons' in filter_settings and filter_settings['excluded_persons']:
        num_persons = len(filter_settings['excluded_persons'])
        active_filters.append(f"{filter_categories['person']} People: {num_persons} excluded")
    
    # Person type filter (new)
    if 'selected_person_type' in filter_settings and filter_settings['selected_person_type'] != 'all':
        person_type = filter_settings['selected_person_type'].capitalize()
        active_filters.append(f"{filter_categories['person_type']} Person Type: {person_type}")
    
    # Project hours range filter
    if 'project_min_hours' in filter_settings and 'project_max_hours' in filter_settings:
        min_hours = filter_settings['project_min_hours']
        max_hours = filter_settings['project_max_hours']
        active_filters.append(f"{filter_categories['project_hours']} Project Hours: {min_hours} to {max_hours}")
    
    # Project effective rate filter (new)
    if 'project_min_effective_rate' in filter_settings and 'project_max_effective_rate' in filter_settings:
        min_rate = filter_settings['project_min_effective_rate']
        max_rate = filter_settings['project_max_effective_rate']
        active_filters.append(f"{filter_categories['project_rate']} Effective Rate: {min_rate} to {max_rate}")
    
    # Billability filter
    if 'selected_billability' in filter_settings and filter_settings['selected_billability'] != 'all':
        billability = filter_settings['selected_billability']
        active_filters.append(f"{filter_categories['billability']} Hours: {billability}")
    
    # Display the active filters
    if active_filters:
        # Create the HTML for the filter badges
        html = """
        <style>
        .filter-badge {
            display: inline-block;
            background-color: #f0f2f6;
            padding: 8px 12px;
            border-radius: 20px;
            margin-right: 8px;
            margin-bottom: 8px;
            font-size: 0.9em;
        }
        .filter-container {
            display: flex;
            flex-wrap: wrap;
            margin-bottom: 16px;
        }
        </style>
        <div class="filter-container">
        """
        
        for filter_text in active_filters:
            html += f'<div class="filter-badge">{filter_text}</div>'
        
        html += "</div>"
        
        st_obj.markdown(html, unsafe_allow_html=True)
    else:
        st_obj.info("No filters applied")
# ui/sidebar.py
import streamlit as st
from utils.filters import (
    create_date_filters, 
    create_customer_filter, 
    create_project_filter, 
    create_activity_filter, 
    create_person_filter, 
    create_person_type_filter, 
    create_project_hours_filter,
    create_project_effective_rate_filter,  # New import
    create_billability_filter,
    create_project_type_filter,
    create_price_model_filter
)
from utils.filter_display import display_filter_badges
from utils.project_reference import get_dynamic_project_filters
import glob
import os


def detect_available_datasets():
    """
    Detect which datasets are available (regular and/or adjusted).
    
    Returns:
        dict: {
            'regular': bool,
            'adjusted': bool,
            'available_versions': list,
            'recommended_default': str
        }
    """
    regular_files = glob.glob("data/*time_records*_regular.parquet")
    adjusted_files = glob.glob("data/*time_records*_adjusted.parquet")
    
    has_regular = len(regular_files) > 0
    has_adjusted = len(adjusted_files) > 0
    
    available_versions = []
    if has_regular:
        available_versions.append('regular')
    if has_adjusted:
        available_versions.append('adjusted')
    
    # Determine recommended default (prefer adjusted if available)
    if has_adjusted:
        recommended_default = 'adjusted'
    elif has_regular:
        recommended_default = 'regular'
    else:
        recommended_default = 'adjusted'  # Fallback
    
    return {
        'regular': has_regular,
        'adjusted': has_adjusted,
        'available_versions': available_versions,
        'recommended_default': recommended_default,
        'single_dataset': len(available_versions) == 1
    }


def apply_filters_to_planned_data(planned_df, filter_settings, filtered_actual_df=None):
    """
    Apply comprehensive filtering to planned data based on filter_settings from main data.
    
    Args:
        planned_df: DataFrame containing planned data
        filter_settings: Dictionary of filter settings applied to main data
        filtered_actual_df: Optional filtered actual data to derive project list for customer filtering
        
    Returns:
        DataFrame: Filtered planned data
    """
    if planned_df is None or planned_df.empty:
        return planned_df
    
    filtered_df = planned_df.copy()
    
    # Special handling for customer filtering: since planned data lacks customer columns,
    # filter through projects using the filtered actual data
    if (('included_customers' in filter_settings and filter_settings['included_customers']) or 
        ('excluded_customers' in filter_settings and filter_settings['excluded_customers'])):
        if filtered_actual_df is not None and not filtered_actual_df.empty:
            # Extract project list from filtered actual data (which has been filtered by customer)
            project_col_actual = None
            if 'project_number' in filtered_actual_df.columns:
                project_col_actual = 'project_number'
            elif 'Project number' in filtered_actual_df.columns:
                project_col_actual = 'Project number'
            
            project_col_planned = None
            if 'project_number' in filtered_df.columns:
                project_col_planned = 'project_number'
            elif 'Project number' in filtered_df.columns:
                project_col_planned = 'Project number'
            
            if project_col_actual and project_col_planned:
                # Get list of projects from filtered actual data
                allowed_projects = filtered_actual_df[project_col_actual].unique().tolist()
                # Filter planned data to only include those projects
                filtered_df = filtered_df[filtered_df[project_col_planned].isin(allowed_projects)]
    
    # 1. Date filters
    if 'start_date' in filter_settings and 'end_date' in filter_settings:
        if 'record_date' in filtered_df.columns:
            start_date = filter_settings['start_date']
            end_date = filter_settings['end_date']
            filtered_df = filtered_df[
                (filtered_df['record_date'].dt.date >= start_date) & 
                (filtered_df['record_date'].dt.date <= end_date)
            ]
    
    # 2. Project filters (included projects)
    if 'included_projects' in filter_settings and filter_settings['included_projects']:
        # Check for different possible column names in planned data
        project_col = None
        if 'Project number' in filtered_df.columns:
            project_col = 'Project number'
        elif 'project_number' in filtered_df.columns:
            project_col = 'project_number'
        
        if project_col:
            filtered_df = filtered_df[filtered_df[project_col].isin(filter_settings['included_projects'])]
    
    # 3. Project filters (excluded projects)
    if 'excluded_projects' in filter_settings and filter_settings['excluded_projects']:
        # Check for different possible column names in planned data
        project_col = None
        if 'Project number' in filtered_df.columns:
            project_col = 'Project number'
        elif 'project_number' in filtered_df.columns:
            project_col = 'project_number'
        
        if project_col:
            filtered_df = filtered_df[~filtered_df[project_col].isin(filter_settings['excluded_projects'])]
    
    # Note: Customer filtering is handled above through project-based filtering
    # since planned data lacks customer columns
    
    # 4. Person filters (included persons)
    if 'included_persons' in filter_settings and filter_settings['included_persons']:
        # Check for different possible column names in planned data
        person_col = None
        if 'Person' in filtered_df.columns:
            person_col = 'Person'
        elif 'person_name' in filtered_df.columns:
            person_col = 'person_name'
        
        if person_col:
            filtered_df = filtered_df[filtered_df[person_col].isin(filter_settings['included_persons'])]
    
    # 5. Person filters (excluded persons)
    if 'excluded_persons' in filter_settings and filter_settings['excluded_persons']:
        # Check for different possible column names in planned data
        person_col = None
        if 'Person' in filtered_df.columns:
            person_col = 'Person'
        elif 'person_name' in filtered_df.columns:
            person_col = 'person_name'
        
        if person_col:
            filtered_df = filtered_df[~filtered_df[person_col].isin(filter_settings['excluded_persons'])]
    
    # 6. Person type filters
    if 'selected_person_type' in filter_settings and filter_settings['selected_person_type'] != 'all':
        # Check for different possible column names in planned data
        person_type_col = None
        if 'Person type' in filtered_df.columns:
            person_type_col = 'Person type'
        elif 'person_type' in filtered_df.columns:
            person_type_col = 'person_type'
        
        if person_type_col:
            if filter_settings['selected_person_type'] == 'internal':
                filtered_df = filtered_df[filtered_df[person_type_col].fillna('').str.lower() == 'internal']
            elif filter_settings['selected_person_type'] == 'external':
                filtered_df = filtered_df[filtered_df[person_type_col].fillna('').str.lower() == 'external']
    
    # 7. Project type filters (included project types)
    if 'included_project_types' in filter_settings and filter_settings['included_project_types']:
        # Check for different possible column names in planned data
        project_type_col = None
        if 'Project type' in filtered_df.columns:
            project_type_col = 'Project type'
        elif 'project_tag' in filtered_df.columns:
            project_type_col = 'project_tag'
        
        if project_type_col:
            filtered_df = filtered_df[filtered_df[project_type_col].isin(filter_settings['included_project_types'])]
    
    # 8. Project type filters (excluded project types)
    if 'excluded_project_types' in filter_settings and filter_settings['excluded_project_types']:
        # Check for different possible column names in planned data
        project_type_col = None
        if 'Project type' in filtered_df.columns:
            project_type_col = 'Project type'
        elif 'project_tag' in filtered_df.columns:
            project_type_col = 'project_tag'
        
        if project_type_col:
            filtered_df = filtered_df[~filtered_df[project_type_col].isin(filter_settings['excluded_project_types'])]
    
    # 9. Price model filters (included price models)
    if 'included_price_models' in filter_settings and filter_settings['included_price_models']:
        # Check for different possible column names in planned data
        price_model_col = None
        if 'Price model' in filtered_df.columns:
            price_model_col = 'Price model'
        elif 'price_model_type' in filtered_df.columns:
            price_model_col = 'price_model_type'
        
        if price_model_col:
            filtered_df = filtered_df[filtered_df[price_model_col].isin(filter_settings['included_price_models'])]
    
    # 10. Price model filters (excluded price models)
    if 'excluded_price_models' in filter_settings and filter_settings['excluded_price_models']:
        # Check for different possible column names in planned data
        price_model_col = None
        if 'Price model' in filtered_df.columns:
            price_model_col = 'Price model'
        elif 'price_model_type' in filtered_df.columns:
            price_model_col = 'price_model_type'
        
        if price_model_col:
            filtered_df = filtered_df[~filtered_df[price_model_col].isin(filter_settings['excluded_price_models'])]
    
    # 11. Activity filters (included activities)
    if 'included_activities' in filter_settings and filter_settings['included_activities']:
        # Check for different possible column names in planned data
        activity_col = None
        if 'Activity' in filtered_df.columns:
            activity_col = 'Activity'
        elif 'activity_tag' in filtered_df.columns:
            activity_col = 'activity_tag'
        
        if activity_col:
            filtered_df = filtered_df[filtered_df[activity_col].isin(filter_settings['included_activities'])]
    
    # 12. Activity filters (excluded activities)
    if 'excluded_activities' in filter_settings and filter_settings['excluded_activities']:
        # Check for different possible column names in planned data
        activity_col = None
        if 'Activity' in filtered_df.columns:
            activity_col = 'Activity'
        elif 'activity_tag' in filtered_df.columns:
            activity_col = 'activity_tag'
        
        if activity_col:
            filtered_df = filtered_df[~filtered_df[activity_col].isin(filter_settings['excluded_activities'])]
    
    # 13. Phase filters (included phases)
    if 'included_phases' in filter_settings and filter_settings['included_phases']:
        # Check for different possible column names in planned data
        phase_col = None
        if 'Phase' in filtered_df.columns:
            phase_col = 'Phase'
        elif 'phase_tag' in filtered_df.columns:
            phase_col = 'phase_tag'
        
        if phase_col:
            filtered_df = filtered_df[filtered_df[phase_col].isin(filter_settings['included_phases'])]
    
    # 14. Phase filters (excluded phases)
    if 'excluded_phases' in filter_settings and filter_settings['excluded_phases']:
        # Check for different possible column names in planned data
        phase_col = None
        if 'Phase' in filtered_df.columns:
            phase_col = 'Phase'
        elif 'phase_tag' in filtered_df.columns:
            phase_col = 'phase_tag'
        
        if phase_col:
            filtered_df = filtered_df[~filtered_df[phase_col].isin(filter_settings['excluded_phases'])]
    
    return filtered_df

def render_sidebar_filters(df, planned_df=None):
    """
    Render filter controls in the sidebar and return filtered dataframes and settings.
    """
    # Create a copy of the input dataframe to avoid modifying the original
    filtered_df = df.copy()
    filter_settings = {}

    # Create a copy of planned_df and apply Person type mapping if needed
    if planned_df is not None:
        filtered_planned_df = planned_df.copy()
        
        # Create a mapping of Person → Person type from the main data
        if 'Person type' in df.columns:
            person_type_map = df[['Person', 'Person type']].drop_duplicates().set_index('Person')['Person type']
            
            # Apply this mapping directly to filtered_planned_df
            filtered_planned_df['Person type'] = filtered_planned_df['Person'].map(person_type_map)
            
            # Handle any persons in planned data that aren't in main data
            if filtered_planned_df['Person type'].isna().any() and st.session_state.get('debug_mode', False):
                st.info(f"🐛 Debug: {filtered_planned_df['Person type'].isna().sum()} persons in planned data not found in main data")
    else:
        filtered_planned_df = None    

    # Apply dynamic project filters if reference data exists
    if 'project_reference_df' in st.session_state and st.session_state.project_reference_df is not None:
        try:
            # Always call the function to render UI
            temp_df, project_meta_settings, handled_columns = get_dynamic_project_filters(
                filtered_df, st.session_state.project_reference_df
            )
            
            filtered_df = temp_df
            filter_settings.update(project_meta_settings)
                
            if filtered_df.empty:
                filter_settings['no_data'] = True
        except Exception as e:
            st.sidebar.error(f"Error applying project metadata filters: {str(e)}")
            filter_settings['no_data'] = True
    
    # Apply all filters sequentially
    filter_functions = [
        create_date_filters,
        create_customer_filter,
        create_project_filter,
        create_project_type_filter,
        create_price_model_filter,
        create_activity_filter,
        create_person_filter,
        create_person_type_filter,
        create_project_hours_filter,
        create_project_effective_rate_filter,  # New filter added
        create_billability_filter
    ]
    
    # Apply each filter function
    for filter_func in filter_functions:
        try:
            temp_df, new_settings = filter_func(filtered_df)
            filtered_df = temp_df
            filter_settings.update(new_settings)
        except Exception as e:
            st.sidebar.error(f"Error applying filter: {str(e)}")
    
    # Apply comprehensive filters to planned data if available
    if filtered_planned_df is not None:
        filtered_planned_df = apply_filters_to_planned_data(filtered_planned_df, filter_settings, filtered_df)
 
    # Display filter badges after all filters have been processed
    display_filter_badges(filter_settings, location="sidebar")
    
    # Dataset version selector
    st.sidebar.markdown("---")
    
    # Detect available datasets
    dataset_info = detect_available_datasets()
    
    # Initialize dataset version if not set, using smart detection
    if 'data_version' not in st.session_state:
        st.session_state.data_version = dataset_info['recommended_default']
    
    # Only show dataset selector if multiple datasets are available
    if not dataset_info['single_dataset'] and len(dataset_info['available_versions']) > 1:
        # Dataset version radio button
        st.sidebar.subheader("📊 Dataset Version")
        selected_version = st.sidebar.radio(
            "Choose dataset:",
            options=["adjusted", "regular"],
            index=0 if st.session_state.data_version == "adjusted" else 1,
            format_func=lambda x: "💰 Regular Values" if x == "regular" else "📈 Adjusted Values",
            help="Switch between regular and adjusted financial values (rates, costs, profits)",
            key="data_version_radio"
        )
    else:
        # Single dataset - show info but no toggle
        selected_version = st.session_state.data_version
        if dataset_info['single_dataset']:
            available_type = dataset_info['available_versions'][0]
            st.sidebar.subheader("📊 Dataset Version")
            if available_type == "adjusted":
                st.sidebar.info("📈 Using Adjusted Values (only dataset available)")
            else:
                st.sidebar.info("💰 Using Regular Values (only dataset available)")
        elif len(dataset_info['available_versions']) == 0:
            selected_version = "adjusted"  # Fallback
    
    # Trigger reload if version changed
    if selected_version != st.session_state.data_version:
        st.session_state.data_version = selected_version
        st.info(f"🔄 Switching to {selected_version} dataset...")
        
        # Clear manifest caches to force reload with new version
        from ui.parquet_processor import clear_manifest_cache
        clear_manifest_cache()
        
        # Clear data to force reload with new version
        if 'transformed_df' in st.session_state:
            del st.session_state.transformed_df
        if 'transformed_planned_df' in st.session_state:
            del st.session_state.transformed_planned_df
        # Clear loading flags to trigger reload
        st.session_state.csv_loaded = False
        st.session_state.planned_csv_loaded = False
        st.session_state.data_loading_attempted = False
        st.rerun()
    
    
    # Add welcome and logout to very bottom of sidebar for authenticated users
    if st.session_state.get('authenticated', False):
        st.sidebar.markdown(f"Logged in as: {getattr(st.session_state.user, 'email', 'User')}")
        
        if st.sidebar.button("🚪 Logout", key="logout_sidebar_button"):
            # Import here to avoid circular imports
            from supabase import create_client
            
            # Get Supabase client
            url = os.getenv('SUPABASE_URL')
            key = os.getenv('SUPABASE_KEY')
            
            if url and key and url != 'your_supabase_project_url_here':
                supabase = create_client(url, key)
                try:
                    supabase.auth.sign_out()
                except Exception as e:
                    print(f"🔍 TERMINAL: Logout error: {e}")
            
            # Clear session state
            st.session_state.authenticated = False
            st.session_state.user = None
            
            # Clear other session state that might interfere
            for key in list(st.session_state.keys()):
                if key not in ['authenticated', 'user']:
                    del st.session_state[key]
            
            st.rerun()
        
    return filtered_df, filtered_planned_df, filter_settings
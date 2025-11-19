import streamlit as st
import pandas as pd
import os
import glob
from pathlib import Path
from utils.localhost_selector import is_localhost

# Set page configuration
st.set_page_config(
    page_title="Arkemy Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

def is_debug_mode():
    """Check if debug mode is enabled via environment variable or session state."""
    import os
    # Check environment variable first (production override)
    if os.getenv('ARKEMY_DEBUG', '').lower() in ('true', '1', 'yes'):
        return True
    # Fall back to session state for development
    return st.session_state.get('debug_mode', False)

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

def try_load_logo():
    """Try to load logo from data directory."""
    data_dir = get_data_directory()

    # Look for logo files with common patterns
    patterns = ['*logo*', '*arkemy*', '*brand*']
    extensions = ['.png', '.jpg', '.jpeg', '.svg']

    for pattern in patterns:
        for ext in extensions:
            files = glob.glob(os.path.join(data_dir, pattern + ext))
            if files:
                # Use the first matching file
                filepath = files[0]
                try:
                    # Return the file path for st.logo
                    return filepath
                except Exception as e:
                    continue

    return None

# Initialize session state variables
if 'csv_loaded' not in st.session_state:
    st.session_state.csv_loaded = False
if 'transformed_df' not in st.session_state:
    st.session_state.transformed_df = None
if 'currency' not in st.session_state:
    st.session_state.currency = 'nok'
if 'loaded_file_path' not in st.session_state:
    st.session_state.loaded_file_path = None

def render_data_loading_interface():
    """Render the clean data loading interface for users."""
    from utils.unified_data_loader import load_data_hybrid, load_data_from_upload, UnifiedDataLoader
    from utils.admin_helpers import is_admin_authenticated

    # Try to load data silently for regular users
    debug_mode = is_debug_mode()
    is_admin = is_admin_authenticated()

    # LOCALHOST MODE: Data should already be loaded via dataset selection page
    if is_localhost():
        # Check if data is loaded (should be loaded via 0_Dataset_Selection.py)
        if st.session_state.csv_loaded and st.session_state.transformed_df is not None:
            # Data already loaded, proceed to dashboard
            return True
        else:
            # This shouldn't happen due to conditional navigation, but handle it gracefully
            st.error("📂 No data loaded. Please use the 'Change Dataset' button in the sidebar.")
            return False
    else:
        # PRODUCTION MODE: Check if data is already loaded
        if st.session_state.csv_loaded and st.session_state.transformed_df is not None:
            # For regular users: no status messages, just proceed to dashboard
            if not is_admin_authenticated():
                return True
            else:
                # For admins: show minimal status in sidebar or expander
                render_admin_data_status()
                return True

        # Silent loading for regular users, verbose for admins
        loading_results = load_data_hybrid(
            volume_paths=["/data", "./data"],
            show_debug=debug_mode and is_admin,
            silent_mode=not is_admin
        )

    if loading_results['loading_method'] in ['auto_volume', 'localhost_selection']:
        # Data was auto-loaded from volume or selected from localhost
        if loading_results['success']:
            if is_admin:
                st.success("🎉 **Data loaded successfully!**")
                display_loading_results(loading_results)
            return True
        else:
            if is_admin:
                st.error(f"❌ **Loading failed**: {loading_results.get('error', 'Unknown error')}")
            else:
                st.error("Unable to load data. Please contact administrator.")

    elif loading_results['loading_method'] == 'upload_required':
        # No files found
        if is_admin:
            # Show upload interface to admins
            return render_upload_interface(debug_mode)
        else:
            # Show simple message to users
            st.info("📂 **No data available**. Please contact your administrator to upload data files.")
            return False

    return False

def render_upload_interface(debug_mode: bool) -> bool:
    """Render file upload interface."""
    from utils.unified_data_loader import load_data_from_upload

    st.markdown("### 📤 Upload Data File")
    st.markdown("Upload a parquet file containing your time tracking data. The system supports unified files with multiple record types.")

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a parquet file",
        type=['parquet', 'pq'],
        help="Upload a .parquet file with time tracking and/or planned hours data"
    )

    if uploaded_file is not None:
        st.info(f"📁 **File selected**: `{uploaded_file.name}` ({round(len(uploaded_file.getvalue()) / (1024*1024), 2)} MB)")

        if st.button("🚀 Process File", type="primary"):
            with st.spinner("Processing file..."):
                loading_results = load_data_from_upload(uploaded_file, debug_mode)

            if loading_results['success']:
                st.success("🎉 **File processed successfully!**")
                display_loading_results(loading_results)
                return True
            else:
                st.error(f"❌ **File processing failed**: {loading_results.get('error', 'Unknown error')}")

    return False

def display_loading_results(results: dict):
    """Display the results of data loading."""

    # Currency and method info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Currency Detected", results['currency'].upper())

    with col2:
        method_display = {
            'auto_volume': 'Auto-Loaded',
            'upload': 'Uploaded',
            'manual': 'Manual',
            'localhost_selection': 'Local Selection'
        }
        loading_method = method_display.get(results['loading_method'], 'Unknown')
        if results.get('data_source_path'):
            source_type = "Volume" if results['data_source_path'] == "/data" else "Local"
            if results['loading_method'] == 'localhost_selection':
                # For localhost, show the client name from the path
                loading_method = f"{loading_method} ({results.get('data_source_path', 'Local')})"
            else:
                loading_method = f"{loading_method} ({source_type})"
        st.metric("Loading Method", loading_method)

    with col3:
        total_records = sum(len(df) for df in results['processed_data'].values())
        st.metric("Total Records", f"{total_records:,}")

    # Record type breakdown
    if results['processed_data']:
        st.markdown("### 📊 Data Summary")

        for record_type, df in results['processed_data'].items():
            validation = results['validation_results'].get(record_type, {})

            with st.expander(f"📋 {record_type.replace('_', ' ').title()} ({len(df):,} records)", expanded=True):

                # Validation status
                if validation.get('is_valid', False):
                    st.success("✅ Schema validation passed")
                else:
                    st.warning("⚠️ Schema validation had issues")

                # Quick stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Records", f"{len(df):,}")
                with col2:
                    if 'person_name' in df.columns:
                        st.metric("People", df['person_name'].nunique())
                with col3:
                    if 'project_number' in df.columns:
                        st.metric("Projects", df['project_number'].nunique())

                # Sample data
                if not df.empty:
                    st.markdown("**Sample Data:**")
                    # Show key columns only
                    key_cols = ['record_date', 'person_name', 'project_number']
                    if record_type == 'time_record':
                        key_cols.extend(['hours_used', 'hours_billable'])
                    elif record_type == 'planned_record':
                        key_cols.extend(['planned_hours'])

                    available_cols = [col for col in key_cols if col in df.columns]
                    if available_cols:
                        st.dataframe(df[available_cols].head(), use_container_width=True)

def render_admin_data_status():
    """Show minimal data status for admins."""
    with st.expander("🔧 **Admin: Data Status**", expanded=False):
        # Quick stats
        df = st.session_state.transformed_df
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Records", f"{len(df):,}")
        with col2:
            st.metric("People", df['person_name'].nunique() if 'person_name' in df.columns else 'N/A')
        with col3:
            st.metric("Projects", df['project_number'].nunique() if 'project_number' in df.columns else 'N/A')
        with col4:
            st.metric("Currency", st.session_state.currency.upper())

        # Show planned data status if available
        if st.session_state.get('planned_csv_loaded', False) and st.session_state.transformed_planned_df is not None:
            planned_df = st.session_state.transformed_planned_df
            st.info(f"📅 **Planned data also loaded**: {len(planned_df):,} planned records")

        # Option to reload data
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("🔄 Reload Data", key="admin_reload"):
                # Clear session state to trigger reload
                st.session_state.csv_loaded = False
                st.session_state.transformed_df = None
                st.session_state.planned_csv_loaded = False
                st.session_state.transformed_planned_df = None
                st.rerun()

def render_data_loaded_status():
    """Legacy function - now redirects to admin status."""
    render_admin_data_status()

def main():
    """Main page logic."""


    # Try to load data
    data_loaded = render_data_loading_interface()

    if data_loaded and st.session_state.csv_loaded:
        # Import and render the main dashboard
        try:
            from ui.dashboard import render_dashboard
            render_dashboard()
        except ImportError as e:
            st.error(f"Dashboard import error: {e}")
            st.info("Dashboard functionality not available. Please check your imports.")
    else:
        # Show helpful information while waiting for data
        st.markdown("---")
        st.markdown("### 📖 About This Dashboard")

        st.markdown("""
        **Arkemy Analytics Dashboard** provides comprehensive project analytics including:

        - 📊 **Summary KPIs**: Revenue, hours, profitability metrics
        - 📈 **Time Trends**: Monthly and yearly performance tracking
        - 👥 **People Analytics**: Individual and team performance
        - 📁 **Project Analysis**: Project-level insights and comparisons
        - 💰 **Customer Analytics**: Revenue and profitability by client
        - 🏗️ **Phase Analysis**: Project phase performance tracking

        **New Features:**
        - ✨ **Schema-Driven Loading**: Easy data validation and processing
        - 🔄 **Auto-Loading**: Automatically loads data from `/data` volume
        - 📤 **Upload Fallback**: Manual upload when no volume data available
        - 🎯 **Record Type Support**: Handles both time records and planned hours
        - 🌍 **Multi-Currency**: Automatic currency detection from filenames
        """)

if __name__ == "__main__":
    main()
else:
    # When imported as a page, run main function
    main()
import streamlit as st
import glob
import time

# Import UI functions
from ui import render_dashboard
from ui.parquet_processor import process_parquet_data_from_path, process_manifest_data, is_debug_mode

# Set page configuration
st.set_page_config(
    page_title="Arkemy Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize session state variables (same as in main.py for direct page access)
if 'csv_loaded' not in st.session_state:
    st.session_state.csv_loaded = False
if 'transformed_df' not in st.session_state:
    st.session_state.transformed_df = None
if 'currency' not in st.session_state:
    st.session_state.currency = 'nok'  # Default to Norwegian krone
if 'currency_selected' not in st.session_state:
    st.session_state.currency_selected = False
if 'planned_csv_loaded' not in st.session_state:
    st.session_state.planned_csv_loaded = False
if 'transformed_planned_df' not in st.session_state:
    st.session_state.transformed_planned_df = None
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 0
if 'data_loading_attempted' not in st.session_state:
    st.session_state.data_loading_attempted = False
if 'show_uploader' not in st.session_state:
    st.session_state.show_uploader = False

# Initialize capacity-related session state variables
if 'schedule_loaded' not in st.session_state:
    st.session_state.schedule_loaded = False
if 'schedule_df' not in st.session_state:
    st.session_state.schedule_df = None
if 'absence_loaded' not in st.session_state:
    st.session_state.absence_loaded = False
if 'absence_df' not in st.session_state:
    st.session_state.absence_df = None
if 'capacity_config' not in st.session_state:
    st.session_state.capacity_config = None
if 'capacity_summary_loaded' not in st.session_state:
    st.session_state.capacity_summary_loaded = False
if 'capacity_summary_df' not in st.session_state:
    st.session_state.capacity_summary_df = None

def find_manifest_file():
    """Find data manifest file in project root"""
    manifest_files = glob.glob("data_manifest.yaml") + glob.glob("data_manifest.yml")
    return manifest_files[0] if manifest_files else None

def find_parquet_file():
    """Find the first Parquet file in data directory"""
    parquet_files = glob.glob("data/*.parquet") + glob.glob("data/*.pq")
    return parquet_files[0] if parquet_files else None

def is_data_loaded():
    """Check if data is loaded and available for analysis"""
    return (
        st.session_state.csv_loaded and 
        st.session_state.transformed_df is not None and 
        not getattr(st.session_state.transformed_df, 'empty', True)
    )

def is_capacity_data_available():
    """Check if capacity data is loaded and available for analysis"""
    return (
        st.session_state.schedule_loaded and 
        st.session_state.schedule_df is not None and 
        not getattr(st.session_state.schedule_df, 'empty', True)
    )

def show_loading_screen():
    """Show a clean loading screen"""
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh;">
        <h1>🥇 Arkemy</h1>
        <h3>Turn Your Project Data Into Gold</h3>
        <div style="margin: 40px 0;">
            <div class="stSpinner">Loading your data...</div>
        </div>
        <p style="color: #666;">Please wait while we process your project data</p>
    </div>
    """, unsafe_allow_html=True)

def auto_load_data():
    """Automatically load data from data directory or manifest on first run"""
    if st.session_state.data_loading_attempted:
        return
    
    st.session_state.data_loading_attempted = True
    
    # Show loading progress with minimal debug info
    data_version = st.session_state.get('data_version', 'adjusted')
    
    # Show debug info only if debug mode is enabled
    if is_debug_mode():
        st.info(f"🔍 Starting data loading with version: {data_version}")
        
        # Show what files exist in the data directory
        data_files = glob.glob("data/*.parquet") + glob.glob("data/*.pq")
        st.info(f"📁 Found {len(data_files)} parquet files in data directory")
        for f in sorted(data_files):
            st.info(f"  • {f}")
    
    # First, try to find and use manifest file
    manifest_path = find_manifest_file()
    if manifest_path:
        if is_debug_mode():
            st.info(f"📄 Found manifest file: {manifest_path}")
            st.info("📥 Attempting to load data using manifest...")
        try:
            process_manifest_data(manifest_path)
            return
        except Exception as e:
            st.error(f"❌ Error loading data from manifest: {str(e)}")
            if is_debug_mode():
                import traceback
                st.error(f"🔍 Full error details: {traceback.format_exc()}")
            # Fall back to parquet file loading
            st.info("🔄 Falling back to parquet file loading...")
    else:
        if is_debug_mode():
            st.info("📄 No manifest file found, trying parquet fallback")
    
    # Fallback: Find single parquet file (backward compatibility)
    parquet_path = find_parquet_file()
    if not parquet_path:
        # No data files found - show error message
        st.error("📂 No parquet files found in /data directory")
        st.markdown("""
        **To use Arkemy, place your parquet data files in the `/data` directory:**
        - For single dataset: `data/your_data_NOK.parquet`
        - For dual datasets: `data/your_data_regular.parquet` and `data/your_data_adjusted.parquet`
        - Or use a `data_manifest.yaml` file to configure multiple data sources
        """)
        return
    
    # Process the parquet file
    st.info(f"📄 Using fallback parquet file: {parquet_path}")
    st.info("📥 Attempting to load data from single parquet file...")
    try:
        process_parquet_data_from_path(parquet_path)
        st.success("✅ Data loaded successfully from parquet file!")
    except Exception as e:
        st.error(f"❌ Error loading data from parquet file: {str(e)}")
        import traceback
        st.error(f"🔍 Full error details: {traceback.format_exc()}")

def render_currency_setup():
    """Render error message if currency couldn't be auto-detected"""
    st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
    st.markdown("##### v1.3.1 Parquet")
    
    st.error("Currency could not be detected from filename.")
    st.markdown("Please name your file like: `data_NOK.parquet` or `data_USD.parquet`")
    
    # Fallback manual selection
    from utils.currency_formatter import get_currency_selector, get_currency_display_name
    currency_valid, _ = get_currency_selector("fallback_currency_selector", required=True)
    
    if currency_valid:
        st.success(f"Selected currency: {get_currency_display_name()}")
        st.session_state.currency_selected = True
        st.rerun()

def show_data_loading_debug():
    """Show comprehensive data loading debug information"""
    with st.sidebar.expander("🐛 Data Loading Debug", expanded=True):
        
        # Add manual cache clear button
        if st.button("🗑️ Clear Cache", help="Clear manifest cache and force reload"):
            from ui.parquet_processor import clear_manifest_cache
            clear_manifest_cache()
            st.success("Cache cleared! Reloading...")
            time.sleep(1)  # Brief pause to show message
            st.rerun()
        
        # Show loading method used
        loading_method = getattr(st.session_state, 'data_loading_method', 'unknown')
        method_icons = {
            'manifest': '📁',
            'single_file': '📄',
            'manifest_failed': '❌',
            'single_file_failed': '❌',
            'unknown': '❓'
        }
        
        st.write(f"**Loading Method:** {method_icons.get(loading_method, '❓')} {loading_method}")
        
        # Show manifest debug info if available
        debug_info = getattr(st.session_state, 'manifest_debug_info', {})
        if debug_info:
            
            if 'error' in debug_info:
                st.error(f"Error: {debug_info['error']}")
            
            if 'manifest_path' in debug_info:
                st.write(f"**Manifest:** `{debug_info['manifest_path']}`")
                
            if 'parquet_path' in debug_info:
                st.write(f"**Parquet:** `{debug_info['parquet_path']}`")
                
            if 'currency' in debug_info:
                st.write(f"**Currency:** {debug_info['currency']}")
                
            if 'available_sources' in debug_info:
                sources = debug_info['available_sources']
                st.write(f"**Available Sources:** {len(sources)}")
                for source in sources:
                    st.write(f"  ✅ {source}")
                
            # Show detailed file resolution status
            if 'detailed_status' in debug_info:
                st.write("**File Resolution:**")
                for source_name, status in debug_info['detailed_status'].items():
                    icon = "✅" if status['exists'] else "❌"
                    st.write(f"{icon} **{source_name}**")
                    if not status['exists']:
                        st.write(f"    Path: `{status['configured_path']}`")
                        if status.get('error'):
                            st.write(f"    Error: {status['error']}")
                        elif status['resolved_path']:
                            st.write(f"    Resolved: `{status['resolved_path']}`")

def show_data_status():
    """Show data loading status for debugging"""
    with st.sidebar.expander("📊 Data Status"):
        st.write("**Main Data:**")
        st.write(f"- CSV loaded: {st.session_state.csv_loaded}")
        st.write(f"- Main DF shape: {getattr(st.session_state.transformed_df, 'shape', 'None')}")
        
        st.write("**Planned Data:**")
        st.write(f"- Planned loaded: {st.session_state.planned_csv_loaded}")
        st.write(f"- Planned DF shape: {getattr(st.session_state.transformed_planned_df, 'shape', 'None')}")
        
        st.write("**Capacity Data:**")
        st.write(f"- Schedule loaded: {st.session_state.schedule_loaded}")
        st.write(f"- Schedule DF shape: {getattr(st.session_state.schedule_df, 'shape', 'None')}")
        st.write(f"- Absence loaded: {st.session_state.absence_loaded}")
        st.write(f"- Absence DF shape: {getattr(st.session_state.absence_df, 'shape', 'None')}")
        st.write(f"- Capacity summary loaded: {st.session_state.capacity_summary_loaded}")
        st.write(f"- Capacity summary DF shape: {getattr(st.session_state.capacity_summary_df, 'shape', 'None')}")
        st.write(f"- Config available: {st.session_state.capacity_config is not None}")

    if st.sidebar.button("View Capacity Data"):
        if st.session_state.get('schedule_df') is not None:
            st.write("**Schedule Data:**")
            st.dataframe(st.session_state.schedule_df.head())
        
        if st.session_state.get('capacity_summary_df') is not None:
            st.write("**Capacity Summary:**")
            st.dataframe(st.session_state.capacity_summary_df.head())

# Analytics Dashboard main logic
if not is_data_loaded():
    # Auto-load data on first run
    auto_load_data()
    
    # Show loading screen if data still not loaded
    if not is_data_loaded():
        show_loading_screen()
else:
    # Show debug information in sidebar if debug mode is enabled
    if is_debug_mode():
        show_data_loading_debug()
        show_data_status()
    
    # Render the dashboard with data
    render_dashboard()
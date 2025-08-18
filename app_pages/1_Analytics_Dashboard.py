import streamlit as st
import glob
import os

# ==========================================
# AUTHENTICATION CHECK - MUST COME FIRST
# ==========================================

# Check if user is authenticated
authentication_status = st.session_state.get('authentication_status')
if authentication_status != True:
    # User is not authenticated - redirect to main page
    st.error("🔒 Access denied. Please log in through the main page.")
    st.markdown("[👉 Go to Login Page](/?page=main)")
    st.stop()

# Import UI functions
from ui import render_dashboard
from ui.parquet_processor import process_parquet_data_from_path

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

def get_data_directory():
    """Get the appropriate data directory - Railway volume or local"""
    # Check for Railway volume first
    if os.path.exists("/data"):
        return "/data"
    # Check for local temp directory
    elif os.path.exists(os.path.expanduser("~/temp_data")):
        return os.path.expanduser("~/temp_data")
    # Fallback to local data directory
    else:
        return "data"

def find_parquet_file():
    """Find main time_records parquet file - REQUIRED for app to work"""
    data_dir = get_data_directory()
    parquet_files = glob.glob(f"{data_dir}/*.parquet") + glob.glob(f"{data_dir}/*.pq")
    
    if not parquet_files:
        return None
        
    # Look for time_records files (required for main data)
    time_records_files = [f for f in parquet_files if 'time_records' in f.lower()]
    if time_records_files:
        # Return newest if multiple files
        return max(time_records_files, key=lambda f: os.path.getmtime(f))
    
    # No fallback - time_records is required
    return None

def find_planned_parquet_file():
    """Find optional planned parquet file"""
    data_dir = get_data_directory()
    parquet_files = glob.glob(f"{data_dir}/*.parquet") + glob.glob(f"{data_dir}/*.pq")
    
    if not parquet_files:
        return None
        
    # Look for planned files (optional)
    planned_files = [f for f in parquet_files if 'planned' in f.lower()]
    if planned_files:
        # Return newest if multiple files
        return max(planned_files, key=lambda f: os.path.getmtime(f))
    
    return None

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

def show_data_error():
    """Show error when required data is missing"""
    st.markdown("""
    <div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 70vh;">
        <h1>🥇 Arkemy</h1>
        <h3>Turn Your Project Data Into Gold</h3>
        <div style="margin: 40px 0; color: #ff6b6b;">
            <h4>📊 No Data Found</h4>
        </div>
        <p style="color: #666;">Please upload time records data via the Admin panel</p>
    </div>
    """, unsafe_allow_html=True)

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
    """Automatically load data from data directory on first run"""
    print("🔍 TERMINAL: auto_load_data() called")
    if st.session_state.data_loading_attempted:
        print("🔍 TERMINAL: Data loading already attempted, skipping")
        return
    
    print("🔍 TERMINAL: Starting data loading process...")
    st.session_state.data_loading_attempted = True
    
    # Check what data directory we're using
    data_dir = get_data_directory()
    print(f"🔍 TERMINAL: Using data directory: {data_dir}")
    
    # Show what files exist in the data directory
    if os.path.exists(data_dir):
        all_files = os.listdir(data_dir)
        print(f"🔍 TERMINAL: Found {len(all_files)} total files in {data_dir}")
        for f in sorted(all_files):
            print(f"🔍 TERMINAL:   • {f}")
            
        parquet_files = [f for f in all_files if f.endswith(('.parquet', '.pq'))]
        print(f"🔍 TERMINAL: Parquet files: {parquet_files}")
    else:
        print(f"🔍 TERMINAL: Data directory {data_dir} doesn't exist!")
        return
    
    # Look for required main data (time_records)
    print("🔍 TERMINAL: Looking for main time_records data...")
    main_parquet_path = find_parquet_file()
    print(f"🔍 TERMINAL: find_parquet_file() returned: {main_parquet_path}")
    
    if not main_parquet_path:
        # Show clear error - main data is required
        st.error("📊 No time records data found in data directory")
        st.info("Please upload a file named like: *time_records*.parquet via Admin panel")
        print(f"🔍 TERMINAL: No time_records files found in {data_dir} directory")
        return
    
    # Process the main parquet file
    print(f"🔍 TERMINAL: Loading main data from: {main_parquet_path}")
    try:
        process_parquet_data_from_path(main_parquet_path)
        print("🔍 TERMINAL: Main data loaded successfully!")
        
        # Try to load optional planned data
        planned_parquet_path = find_planned_parquet_file()
        if planned_parquet_path:
            print(f"🔍 TERMINAL: Found planned data: {planned_parquet_path}")
            # TODO: Add planned data loading here when needed
        else:
            print("🔍 TERMINAL: No planned data found (optional)")
            
    except Exception as e:
        st.error(f"❌ Error loading data from parquet file: {str(e)}")
        print(f"🔍 TERMINAL: Error loading data: {str(e)}")
        import traceback
        print(f"🔍 TERMINAL: Full error details: {traceback.format_exc()}")

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


# Analytics Dashboard main logic
print("🔍 TERMINAL: Analytics Dashboard main logic executing")
print(f"🔍 TERMINAL: is_data_loaded() = {is_data_loaded()}")

if not is_data_loaded():
    print("🔍 TERMINAL: Data not loaded, calling auto_load_data()")
    # Auto-load data on first run
    auto_load_data()
    
    # Show loading screen if data still not loaded
    if not is_data_loaded():
        print("🔍 TERMINAL: Data still not loaded after auto_load_data, showing loading screen")
        show_loading_screen()
    else:
        print("🔍 TERMINAL: Data loaded successfully after auto_load_data")
        # Render the dashboard with newly loaded data
        render_dashboard()
else:
    print("🔍 TERMINAL: Data already loaded, showing dashboard")
    # Render the dashboard with data
    render_dashboard()
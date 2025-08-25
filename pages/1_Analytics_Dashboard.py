import streamlit as st
import pandas as pd
from utils.data_validation import validate_csv_schema, transform_csv, display_validation_results

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

# Initialize session state variables
if 'csv_loaded' not in st.session_state:
    st.session_state.csv_loaded = False
if 'transformed_df' not in st.session_state:
    st.session_state.transformed_df = None
if 'currency' not in st.session_state:
    st.session_state.currency = 'nok'

def process_parquet_file(uploaded_file):
    """Process uploaded parquet file with validation"""
    try:
        # Read parquet file
        df = pd.read_parquet(uploaded_file)
        
        if is_debug_mode():
            st.info(f"🐛 Debug - Loaded file: {df.shape[0]} rows, {df.shape[1]} columns")
            st.info(f"🐛 Debug - Columns: {list(df.columns)}")
        
        # Validate schema
        st.subheader("📋 Schema Validation")
        validation_results = validate_csv_schema(df)
        
        # Always show validation results for immediate feedback
        display_validation_results(validation_results)
        
        if validation_results["is_valid"]:
            # Transform and store data
            transformed_df = transform_csv(df)
            st.session_state.transformed_df = transformed_df
            st.session_state.csv_loaded = True
            
            st.success(f"✅ Data loaded successfully! {transformed_df.shape[0]} rows processed.")
            
            # Show basic data info
            st.subheader("📊 Data Summary")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Records", f"{len(transformed_df):,}")
            with col2:
                st.metric("People", transformed_df['person_name'].nunique())
            with col3:
                st.metric("Projects", transformed_df['project_number'].nunique())
            
            # Show sample data
            if is_debug_mode():
                with st.expander("🔍 Sample Data (Debug)", expanded=False):
                    st.dataframe(transformed_df.head())
            
            return True
        else:
            st.error("❌ Schema validation failed. Please fix the issues above and try again.")
            return False
            
    except Exception as e:
        st.error(f"❌ Error reading parquet file: {str(e)}")
        if is_debug_mode():
            import traceback
            st.code(traceback.format_exc())
        return False

def show_uploader():
    """Show the file uploader interface"""
    st.title("🥇 Arkemy Analytics Dashboard")
    st.markdown("##### Simple Parquet File Uploader")
    
    st.markdown("---")
    
    # File uploader
    st.subheader("📤 Upload Your Parquet File")
    uploaded_file = st.file_uploader(
        "Choose a parquet file",
        type=['parquet', 'pq'],
        help="Upload a parquet file containing your project time tracking data"
    )
    
    if uploaded_file is not None:
        st.info(f"📁 File: {uploaded_file.name} ({uploaded_file.size:,} bytes)")
        
        if st.button("🔄 Process File", type="primary"):
            with st.spinner("Processing your file..."):
                success = process_parquet_file(uploaded_file)
                if success:
                    st.rerun()

def show_dashboard():
    """Show the main dashboard when data is loaded"""
    from ui import render_dashboard
    render_dashboard()

# Main application logic
if not st.session_state.csv_loaded or st.session_state.transformed_df is None:
    # Show uploader
    show_uploader()
else:
    # Show dashboard with data
    show_dashboard()
    
    # Add option to upload new data
    with st.sidebar:
        st.markdown("### 🔄 Data Management")
        if st.button("Upload New File"):
            # Clear existing data
            st.session_state.csv_loaded = False
            st.session_state.transformed_df = None
            st.rerun()
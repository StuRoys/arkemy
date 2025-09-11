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

def detect_file_type(df, filename):
    """Detect if file contains main data or planned data based on filename"""
    filename_lower = filename.lower()
    
    if 'time_records' in filename_lower:
        return "main"
    elif 'planned_records' in filename_lower:
        return "planned"
    else:
        return "main"

def process_parquet_file(uploaded_file, file_type=None):
    """Process uploaded parquet file with validation"""
    try:
        # Read parquet file
        df = pd.read_parquet(uploaded_file)
        
        # Auto-detect file type if not specified
        if file_type is None:
            file_type = detect_file_type(df, uploaded_file.name)
        
        # Always show file analysis - critical for debugging
        st.info(f"📁 **File:** {uploaded_file.name}")
        st.info(f"🔍 **Detected Type:** {file_type}")
        st.info(f"📏 **Shape:** {df.shape[0]:,} rows, {df.shape[1]} columns")
        
        with st.expander("🔍 **Column Analysis**", expanded=True):
            st.write("**All Columns Found:**")
            for i, col in enumerate(df.columns, 1):
                st.write(f"{i:2d}. `{col}`")
            
            st.markdown("---")
            
            # Show what we're looking for
            if file_type == "planned":
                st.write("**Looking for (Planned Data):**")
                planned_required = ["record_date", "person_name", "project_number", "planned_hours"]
                planned_optional = ["planned_hourly_rate"]
                
                st.write("*Required:*")
                for col in planned_required:
                    found = col in [c.lower() for c in df.columns]
                    status = "✅" if found else "❌"
                    st.write(f"{status} `{col}`")
                
                st.write("*Optional:*")
                for col in planned_optional:
                    found = col in [c.lower() for c in df.columns]
                    status = "✅" if found else "⚠️"
                    st.write(f"{status} `{col}`")
            else:
                st.write("**Looking for (Main Data):**")
                main_required = ["record_date", "person_name", "project_number", "hours_used"]
                main_common = ["hours_billable", "fee_record", "cost_hour", "billable_rate_record"]
                
                st.write("*Required:*")
                for col in main_required:
                    # Check both exact match and case variations
                    found = any(col.lower() == c.lower() for c in df.columns)
                    status = "✅" if found else "❌"
                    st.write(f"{status} `{col}`")
                
                st.write("*Common:*")
                for col in main_common:
                    found = any(col.lower() == c.lower() for c in df.columns)
                    status = "✅" if found else "⚠️"
                    st.write(f"{status} `{col}`")
        
        # Validate schema based on detected type
        st.subheader(f"📋 Schema Validation - {file_type.title()} Data")
        
        if file_type == "planned":
            from utils.data_validation import validate_planned_schema, transform_planned_csv, display_planned_validation_results
            validation_results = validate_planned_schema(df)
            display_planned_validation_results(validation_results)
        else:
            validation_results = validate_csv_schema(df)
            display_validation_results(validation_results)
        
        if validation_results["is_valid"]:
            # Transform and store data based on type
            if file_type == "planned":
                transformed_df = transform_planned_csv(df)
                st.session_state.transformed_planned_df = transformed_df
                st.session_state.planned_csv_loaded = True
                st.success(f"✅ Planned data processed successfully! {transformed_df.shape[0]} rows.")
                
                # Show planned data summary
                st.subheader("📊 Planned Data Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", f"{len(transformed_df):,}")
                with col2:
                    st.metric("People", transformed_df['person_name'].nunique())
                with col3:
                    st.metric("Projects", transformed_df['project_number'].nunique())
                
            else:
                transformed_df = transform_csv(df)
                st.session_state.transformed_df = transformed_df
                st.session_state.csv_loaded = True
                st.success(f"✅ Main data processed successfully! {transformed_df.shape[0]} rows.")
                
                # Show main data summary
                st.subheader("📊 Main Data Summary")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", f"{len(transformed_df):,}")
                with col2:
                    st.metric("People", transformed_df['person_name'].nunique())
                with col3:
                    st.metric("Projects", transformed_df['project_number'].nunique())
                
            
            
            return True
        else:
            st.error(f"❌ {file_type.title()} file validation failed. Please fix the issues above and try again.")
            return False
            
    except Exception as e:
        st.error(f"❌ Error processing {uploaded_file.name}: {str(e)}")
        return False

def show_uploader():
    """Show the multi-file uploader interface"""
    st.title("🥇 Arkemy Analytics Dashboard")
    st.markdown("##### Multi-File Parquet Uploader")
    
    st.info("📋 **Upload your data files:** You can upload both main timesheet data and planned hours data. Files are automatically detected based on content and filename.")
    
    st.markdown("---")
    
    # Multi-file uploader
    st.subheader("📤 Upload Your Parquet Files")
    uploaded_files = st.file_uploader(
        "Choose parquet files",
        type=['parquet', 'pq'],
        accept_multiple_files=True,
        help="Upload parquet files containing your project data. Main data and planned data will be automatically detected."
    )
    
    if uploaded_files:
        st.subheader("📁 Files Ready for Processing")
        
        # Show file list with detected types
        file_info = []
        for uploaded_file in uploaded_files:
            # Quick column check to detect type
            try:
                df_preview = pd.read_parquet(uploaded_file)
                detected_type = detect_file_type(df_preview, uploaded_file.name)
                file_info.append({
                    'file': uploaded_file,
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'type': detected_type,
                    'rows': len(df_preview),
                    'columns': len(df_preview.columns)
                })
            except Exception as e:
                file_info.append({
                    'file': uploaded_file,
                    'name': uploaded_file.name,
                    'size': uploaded_file.size,
                    'type': 'error',
                    'error': str(e)
                })
        
        # Display file information table
        for i, info in enumerate(file_info):
            col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
            
            with col1:
                if info['type'] == 'error':
                    st.error(f"❌ {info['name']} - Error: {info.get('error', 'Unknown error')}")
                else:
                    type_icon = "📊" if info['type'] == 'main' else "📈"
                    st.info(f"{type_icon} **{info['name']}** - {info['type'].title()} Data")
            
            with col2:
                if info['type'] != 'error':
                    st.text(f"{info['size']:,} bytes")
            
            with col3:
                if info['type'] != 'error':
                    st.text(f"{info['rows']:,} rows")
            
            with col4:
                if info['type'] != 'error':
                    st.text(f"{info['columns']} cols")
        
        st.markdown("---")
        
        # Process all files button
        if st.button("🔄 Process All Files", type="primary", use_container_width=True):
            success_count = 0
            total_files = len([f for f in file_info if f['type'] != 'error'])
            
            if total_files == 0:
                st.error("❌ No valid files to process!")
                return
            
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i, info in enumerate(file_info):
                if info['type'] == 'error':
                    continue
                    
                status_text.text(f"Processing {info['name']}...")
                progress_bar.progress((i + 1) / total_files)
                
                with st.spinner(f"Processing {info['name']}..."):
                    success = process_parquet_file(info['file'], info['type'])
                    if success:
                        success_count += 1
            
            progress_bar.progress(1.0)
            status_text.text("Processing complete!")
            
            if success_count == total_files:
                st.success(f"✅ All {success_count} files processed successfully!")
                st.balloons()
                st.rerun()
            elif success_count > 0:
                st.warning(f"⚠️ {success_count} of {total_files} files processed successfully. Check errors above.")
                st.rerun()
            else:
                st.error("❌ No files were processed successfully. Please check the errors above.")
    else:
        st.info("👆 Select parquet files to begin processing")

def show_dashboard():
    """Show the main dashboard when data is loaded"""
    from ui import render_dashboard
    render_dashboard()

# Main application logic
has_main_data = st.session_state.get('csv_loaded', False) and st.session_state.get('transformed_df') is not None
has_planned_data = st.session_state.get('planned_csv_loaded', False) and st.session_state.get('transformed_planned_df') is not None

if not has_main_data:
    # Show uploader - need main data to proceed
    if has_planned_data:
        st.warning("📈 Planned data loaded, but main timesheet data is required to access the dashboard.")
    show_uploader()
else:
    # Show dashboard with data
    st.success("📊 Data loaded successfully!")
    if has_planned_data:
        st.info("📈 Both main and planned data are available for analysis.")
    else:
        st.info("📊 Main data available. Upload planned data for forecasting features.")
    
    try:
        show_dashboard()
    except Exception as e:
        st.error(f"❌ Error loading dashboard: {str(e)}")
        
        # Fallback: show uploader again
        st.warning("Falling back to uploader due to dashboard error.")
        show_uploader()
    
    # Add option to upload new data
    with st.sidebar:
        st.markdown("### 🔄 Data Management")
        if st.button("Upload New File"):
            # Clear existing data
            st.session_state.csv_loaded = False
            st.session_state.transformed_df = None
            st.session_state.planned_csv_loaded = False
            st.session_state.transformed_planned_df = None
            st.rerun()
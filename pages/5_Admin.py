# pages/5_Admin.py
import streamlit as st
import os
import sys
from datetime import datetime

# Import admin utilities
from utils.admin_helpers import require_admin_access, render_admin_logout, is_admin_authenticated

def render_data_management_section():
    """Render comprehensive data management section."""
    # Current data status
    render_current_data_status()

    st.markdown("---")

    # Data operations
    render_data_operations()

    st.markdown("---")

    # File management
    render_file_management()

def render_current_data_status():
    """Show current data loading status with detailed file information."""
    st.markdown("### 📈 Current Data Status")

    if st.session_state.get('csv_loaded', False) and st.session_state.transformed_df is not None:
        df = st.session_state.transformed_df

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total Records", f"{len(df):,}")
        with col2:
            st.metric("👥 People", df['person_name'].nunique() if 'person_name' in df.columns else 'N/A')
        with col3:
            st.metric("📁 Projects", df['project_number'].nunique() if 'project_number' in df.columns else 'N/A')
        with col4:
            st.metric("💱 Currency", st.session_state.currency.upper())

        # Planned data status
        if st.session_state.get('planned_csv_loaded', False) and st.session_state.transformed_planned_df is not None:
            planned_df = st.session_state.transformed_planned_df
            st.success(f"📅 **Planned data loaded**: {len(planned_df):,} planned records")

        # Detailed file information
        render_detailed_file_info()

    else:
        st.warning("⚠️ **No data currently loaded**")
        # Still show what files are available
        render_available_files_info()

def render_detailed_file_info():
    """Show detailed information about loaded files."""
    import glob
    from datetime import datetime

    data_dirs = ["./data", "/data"]
    active_dir = None

    # Find which directory exists and has files
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            active_dir = data_dir
            break

    if not active_dir:
        st.info("🔍 **Data source**: No data directory found")
        return

    st.info(f"🔍 **Data source**: {active_dir}")

    # Show loaded files with details
    files_info = []

    # Main parquet file
    parquet_files = glob.glob(os.path.join(active_dir, "*.parquet"))
    for pf in parquet_files:
        if os.path.isfile(pf):
            stat = os.stat(pf)
            size_mb = stat.st_size / (1024*1024)
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            files_info.append({
                "type": "📊 Main Data",
                "file": os.path.basename(pf),
                "size": f"{size_mb:.1f} MB",
                "modified": mod_time,
                "status": "✅ Loaded" if st.session_state.get('csv_loaded') else "⚠️ Not loaded"
            })

    # Coworker CSV
    coworker_files = glob.glob(os.path.join(active_dir, "*coworker*.csv"))
    for cf in coworker_files:
        if os.path.isfile(cf):
            stat = os.stat(cf)
            size_kb = stat.st_size / 1024
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            files_info.append({
                "type": "👥 Coworker",
                "file": os.path.basename(cf),
                "size": f"{size_kb:.1f} KB",
                "modified": mod_time,
                "status": "✅ Available" if st.session_state.get('coworker_csv_loaded') else "💤 Available"
            })

    # SQM CSV
    sqm_files = glob.glob(os.path.join(active_dir, "*sqm*.csv")) + glob.glob(os.path.join(active_dir, "*hrs_sqm*.csv"))
    for sf in sqm_files:
        if os.path.isfile(sf):
            stat = os.stat(sf)
            size_kb = stat.st_size / 1024
            mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            files_info.append({
                "type": "🏗️ SQM Data",
                "file": os.path.basename(sf),
                "size": f"{size_kb:.1f} KB",
                "modified": mod_time,
                "status": "✅ Available"
            })

    # Logo files
    logo_patterns = ['*logo*', '*arkemy*', '*brand*']
    logo_extensions = ['.png', '.jpg', '.jpeg', '.svg']
    for pattern in logo_patterns:
        for ext in logo_extensions:
            logo_files = glob.glob(os.path.join(active_dir, pattern + ext))
            for lf in logo_files:
                if os.path.isfile(lf):
                    stat = os.stat(lf)
                    size_kb = stat.st_size / 1024
                    mod_time = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    files_info.append({
                        "type": "🎨 Logo",
                        "file": os.path.basename(lf),
                        "size": f"{size_kb:.1f} KB",
                        "modified": mod_time,
                        "status": "✅ Active"
                    })
                    break  # Only show first matching logo
            if logo_files:
                break
        if logo_files:
            break

    # Display files in a clean table
    if files_info:
        st.markdown("#### 📁 Active Files")
        for file_info in files_info:
            col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
            with col1:
                st.write(file_info["type"])
            with col2:
                st.code(file_info["file"], language=None)
            with col3:
                st.write(file_info["size"])
            with col4:
                st.write(file_info["status"])

def render_available_files_info():
    """Show available files when no data is loaded."""
    import glob

    data_dirs = ["./data", "/data"]
    for data_dir in data_dirs:
        if os.path.exists(data_dir):
            parquet_files = glob.glob(os.path.join(data_dir, "*.parquet"))
            if parquet_files:
                st.info(f"🔍 **Available data files in {data_dir}**:")
                for pf in parquet_files:
                    st.code(os.path.basename(pf), language=None)
                break
    else:
        st.info("🔍 **No data directory found** - upload files to get started")

def render_client_access():
    """Render client access information."""
    st.markdown("Share this URL with clients for dashboard access:")

    # Try to get current URL, fallback to placeholder
    try:
        # This will work in most deployments
        client_url = "https://your-app-url.com"  # Replace with actual deployment URL
        st.code(client_url, language=None)
        st.info("💡 **Tip**: Remove '/Admin' from the browser URL to get the client dashboard link")
    except Exception:
        st.info("💡 **Client URL**: Remove '/Admin' from the current browser URL")

def render_data_operations():
    """Render data operation buttons."""
    st.markdown("### 🔄 Data Operations")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🔄 **Reload Data**", key="admin_reload_main", use_container_width=True):
            # Clear session state to trigger reload
            st.session_state.csv_loaded = False
            st.session_state.transformed_df = None
            st.session_state.planned_csv_loaded = False
            st.session_state.transformed_planned_df = None
            st.success("Data state cleared. Navigate to Analytics Dashboard to reload.")

    with col2:
        debug_mode = st.session_state.get('debug_mode', False)
        if st.button(f"🐛 **Debug: {'ON' if debug_mode else 'OFF'}**", key="toggle_debug", use_container_width=True):
            st.session_state.debug_mode = not debug_mode
            st.success(f"Debug mode {'enabled' if not debug_mode else 'disabled'}")

    with col3:
        if st.button("📤 **Upload New File**", key="show_uploader", use_container_width=True):
            st.session_state.show_admin_uploader = True

def render_file_management():
    """Render file management interface."""
    st.markdown("### 📁 File Management")

    # Volume statistics (moved from legacy)
    render_volume_stats_inline()

    # Show upload interface if requested
    if st.session_state.get('show_admin_uploader', False):
        render_admin_file_uploader()

        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("❌ Cancel Upload"):
                st.session_state.show_admin_uploader = False
                st.rerun()

    # File browser
    render_file_browser()

def render_volume_stats_inline():
    """Render volume statistics inline."""
    volume_path = "/data"
    local_path = "./data"

    # Check both paths
    paths_to_check = [
        ("/data", "Production Volume"),
        ("./data", "Local Directory")
    ]

    for path, label in paths_to_check:
        if os.path.exists(path):
            try:
                files = get_files_from_directory(path, label)
                if files:
                    total_size = sum(f['size'] for f in files)
                    parquet_files = [f for f in files if f['is_parquet']]

                    with st.expander(f"📊 {label} Stats", expanded=False):
                        col1, col2, col3 = st.columns(3)
                        col1.metric("Total Files", len(files))
                        col2.metric("Parquet Files", len(parquet_files))
                        col3.metric("Total Size", f"{round(total_size / (1024*1024), 1)} MB")
            except Exception:
                pass

def display_admin_loading_results(results: dict):
    """Display loading results for admin interface."""
    # Currency and method info
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Currency Detected", results['currency'].upper())

    with col2:
        method_display = {
            'auto_volume': 'Auto-Loaded',
            'upload': 'Uploaded',
            'manual': 'Manual'
        }
        loading_method = method_display.get(results['loading_method'], 'Unknown')
        if results.get('data_source_path'):
            source_type = "Volume" if results['data_source_path'] == "/data" else "Local"
            loading_method = f"{loading_method} ({source_type})"
        st.metric("Loading Method", loading_method)

    with col3:
        total_records = sum(len(df) for df in results['processed_data'].values())
        st.metric("Total Records", f"{total_records:,}")

    # Record type breakdown
    if results['processed_data']:
        st.markdown("#### 📊 Data Summary")

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

def render_admin_file_uploader():
    """Render admin file upload interface."""
    from utils.unified_data_loader import load_data_from_upload

    st.markdown("#### 📤 Upload Data File")

    uploaded_file = st.file_uploader(
        "Choose a parquet file",
        type=['parquet', 'pq'],
        help="Upload a .parquet file with time tracking and/or planned hours data",
        key="admin_file_upload"
    )

    if uploaded_file is not None:
        st.info(f"📁 **File selected**: `{uploaded_file.name}` ({round(len(uploaded_file.getvalue()) / (1024*1024), 2)} MB)")

        if st.button("🚀 Process File", type="primary", key="admin_process_file"):
            with st.spinner("Processing file..."):
                loading_results = load_data_from_upload(uploaded_file, show_debug=True)

            if loading_results['success']:
                st.success("🎉 **File processed successfully!**")
                # Display loading results inline instead of importing
                display_admin_loading_results(loading_results)
                st.session_state.show_admin_uploader = False
            else:
                st.error(f"❌ **File processing failed**: {loading_results.get('error', 'Unknown error')}")

def render_file_browser():
    """Render file browser for both local and volume directories."""
    st.markdown("#### 📂 Available Files")

    # Check both directories
    local_files = get_files_from_directory("./data", "Local Directory (./data)")
    volume_files = get_files_from_directory("/data", "Production Volume (/data)")

    if local_files:
        render_file_list(local_files, "Local Directory (./data)")

    if volume_files:
        render_file_list(volume_files, "Production Volume (/data)")

    if not local_files and not volume_files:
        st.info("📂 No data files found in either local directory or production volume.")

def get_files_from_directory(directory_path: str, display_name: str):
    """Get files from a specific directory."""
    if not os.path.exists(directory_path):
        return []

    files = []
    try:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'is_parquet': filename.lower().endswith(('.parquet', '.pq')),
                    'directory': display_name
                })
    except Exception as e:
        st.error(f"Error accessing {display_name}: {e}")

    return sorted(files, key=lambda x: x['modified'], reverse=True)

def render_file_list(files, directory_name):
    """Render a list of files."""
    st.markdown(f"##### {directory_name}")

    for i, file_info in enumerate(files):
        with st.expander(f"{'📊' if file_info['is_parquet'] else '📄'} {file_info['filename']}", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Size**: {file_info['size_mb']} MB")
                st.write(f"**Modified**: {file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')}")

            with col2:
                st.write(f"**Type**: {'Parquet Data File' if file_info['is_parquet'] else 'Other'}")
                st.write(f"**Path**: `{file_info['path']}`")

def get_volume_files():
    """Get list of files in /data volume with metadata"""
    volume_path = "/data"
    files_info = []
    
    if not os.path.exists(volume_path):
        return files_info
    
    try:
        for filename in os.listdir(volume_path):
            file_path = os.path.join(volume_path, filename)
            if os.path.isfile(file_path):
                stat = os.stat(file_path)
                files_info.append({
                    'filename': filename,
                    'path': file_path,
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime),
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'is_parquet': filename.lower().endswith(('.parquet', '.pq'))
                })
        
        # Sort by modification time (newest first)
        files_info.sort(key=lambda x: x['modified'], reverse=True)
        
    except Exception as e:
        st.error(f"Error reading volume directory: {str(e)}")
    
    return files_info

def render_file_browser():
    """Render file browser interface"""
    st.markdown("### 📁 File Browser")
    
    files = get_volume_files()
    
    if not files:
        st.info("📂 Volume is empty")
        return
    
    st.success(f"Found {len(files)} file(s) in volume:")
    
    # Create table header
    cols = st.columns([3, 1, 2, 2, 1])
    cols[0].markdown("**Filename**")
    cols[1].markdown("**Type**")
    cols[2].markdown("**Size**")
    cols[3].markdown("**Modified**")
    cols[4].markdown("**Action**")
    
    st.markdown("---")
    
    # List each file
    for i, file_info in enumerate(files):
        cols = st.columns([3, 1, 2, 2, 1])
        
        # Filename with icon
        icon = "📊" if file_info['is_parquet'] else "📄"
        cols[0].write(f"{icon} {file_info['filename']}")
        
        # File type
        file_type = "Parquet" if file_info['is_parquet'] else "Other"
        cols[1].write(file_type)
        
        # Size
        if file_info['size_mb'] > 0:
            cols[2].write(f"{file_info['size_mb']} MB")
        else:
            cols[2].write(f"{file_info['size']:,} bytes")
        
        # Modified date
        cols[3].write(file_info['modified'].strftime('%Y-%m-%d %H:%M'))
        
        # Delete button
        if cols[4].button("🗑️", key=f"delete_{i}", help="Delete file"):
            if st.session_state.get(f"confirm_delete_{i}", False):
                # Actually delete
                try:
                    os.remove(file_info['path'])
                    st.success(f"Deleted {file_info['filename']}")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error deleting file: {str(e)}")
            else:
                # Show confirmation
                st.session_state[f"confirm_delete_{i}"] = True
                st.warning(f"Click delete again to confirm removal of {file_info['filename']}")

def render_file_uploader():
    """Render file upload interface"""
    st.markdown("### 📤 Upload Files")
    
    uploaded_files = st.file_uploader(
        "Choose files to upload to volume", 
        accept_multiple_files=True,
        key="admin_uploader"
    )
    
    if uploaded_files:
        st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
        for file in uploaded_files:
            st.write(f"- {file.name} ({round(len(file.getvalue()) / (1024*1024), 2)} MB)")
        
        if st.button("📤 Upload All Files", key="upload_all"):
            volume_path = "/data"
            
            if not os.path.exists(volume_path):
                st.error("❌ /data volume not available")
                return
            
            success_count = 0
            
            for uploaded_file in uploaded_files:
                try:
                    file_path = os.path.join(volume_path, uploaded_file.name)
                    
                    # Check if file exists
                    if os.path.exists(file_path):
                        st.warning(f"⚠️ {uploaded_file.name} already exists - skipping")
                        continue
                    
                    # Save file
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getvalue())
                    
                    success_count += 1
                    st.success(f"✅ Uploaded {uploaded_file.name}")
                    
                except Exception as e:
                    st.error(f"❌ Failed to upload {uploaded_file.name}: {str(e)}")
            
            if success_count > 0:
                st.success(f"Successfully uploaded {success_count} file(s)")
                st.rerun()

def render_volume_stats():
    """Render volume statistics"""
    volume_path = "/data"
    
    if not os.path.exists(volume_path):
        st.error("❌ Volume not available")
        return
    
    try:
        files = get_volume_files()
        total_size = sum(f['size'] for f in files)
        parquet_files = [f for f in files if f['is_parquet']]
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Total Files", len(files))
        col2.metric("Parquet Files", len(parquet_files))
        col3.metric("Total Size", f"{round(total_size / (1024*1024), 1)} MB")
        
        if files:
            newest = max(files, key=lambda x: x['modified'])
            col4.metric("Newest File", newest['modified'].strftime('%m-%d %H:%M'))
        
    except Exception as e:
        st.error(f"Error getting volume stats: {str(e)}")

def render_client_link():
    """Show the client link"""
    st.markdown("### 🔗 Client Access")
    
    # Get the current URL and create client link
    try:
        current_url = st.get_option("browser.serverAddress")
        if current_url and "admin" in current_url.lower():
            client_url = current_url.replace("/Admin", "").replace("/admin", "")
        else:
            client_url = "https://your-app.railway.app"
    except:
        client_url = "https://your-app.railway.app"
    
    st.code(client_url, language=None)
    st.markdown("👆 Share this URL with your client for dashboard access")

def render_debug_interface():
    """Render debug information interface"""
    st.markdown("### 🐛 Debug Information")
    st.markdown("System and data loading debug information for troubleshooting.")
    
    # Debug Mode Toggle
    st.markdown("#### 🔧 Debug Mode Control")
    
    # Check current debug mode status
    current_debug = st.session_state.get('debug_mode', False)
    env_debug = os.getenv('ARKEMY_DEBUG', '').lower() in ('true', '1', 'yes')
    
    col1, col2 = st.columns([2, 3])
    
    with col1:
        # Toggle button
        new_debug_state = st.toggle(
            "Enable Debug Mode",
            value=current_debug,
            key="debug_toggle",
            help="Toggle detailed debugging information for data loading and validation"
        )
        
        # Update session state if changed
        if new_debug_state != current_debug:
            st.session_state.debug_mode = new_debug_state
            if new_debug_state:
                st.success("Debug mode enabled!")
            else:
                st.info("Debug mode disabled")
    
    with col2:
        # Status display
        if env_debug:
            st.info("🌐 **Environment Override**: Debug mode is enabled via ARKEMY_DEBUG environment variable")
        elif st.session_state.get('debug_mode', False):
            st.success("🟢 **Debug Mode**: ON - Detailed validation and loading information will be shown")
        else:
            st.info("⚪ **Debug Mode**: OFF - Standard operation")
    
    # What debug mode shows
    with st.expander("ℹ️ What Debug Mode Shows", expanded=False):
        st.markdown("""
        When debug mode is enabled, you'll see detailed information during data loading:
        
        **Schema Validation:**
        - ❌ Missing required column headers
        - ⚠️ Data type validation errors  
        - 📋 Problematic values with row numbers (up to 10 examples per issue)
        
        **File Loading:**
        - 📁 Which files are being loaded
        - 📊 Row and column counts
        - 🔍 Data source filtering details
        - 📝 Column lists and transformations
        
        **Manifest Processing:**
        - 🗂️ File path resolution details
        - 📋 Available vs configured data sources
        - ⚠️ Fallback path attempts
        """)
    
    st.markdown("---")
    
    # Session State Debug
    st.markdown("#### 📊 Session State")
    with st.expander("View Session State", expanded=False):
        debug_state = {}
        for key, value in st.session_state.items():
            if hasattr(value, 'shape'):  # DataFrame
                debug_state[key] = f"DataFrame {value.shape}"
            elif isinstance(value, (list, dict)):
                debug_state[key] = f"{type(value).__name__} (len: {len(value)})"
            else:
                debug_state[key] = f"{type(value).__name__}: {str(value)[:100]}"
        
        st.json(debug_state)
    
    # Data Loading Debug
    st.markdown("#### 🔄 Data Loading Status")
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Main Data:**")
        st.write(f"- CSV loaded: {st.session_state.get('csv_loaded', False)}")
        st.write(f"- Main DF shape: {getattr(st.session_state.get('transformed_df'), 'shape', 'None')}")
        st.write(f"- Currency: {st.session_state.get('currency', 'None')}")
        
    with col2:
        st.write("**Additional Data:**")
        st.write(f"- Planned loaded: {st.session_state.get('planned_csv_loaded', False)}")
        st.write(f"- Planned DF shape: {getattr(st.session_state.get('transformed_planned_df'), 'shape', 'None')}")
        st.write(f"- Loading attempted: {st.session_state.get('data_loading_attempted', False)}")
    
    # Cache Management
    st.markdown("#### 🗑️ Cache Management")
    if st.button("Clear Cache", help="Clear all cached data and force reload"):
        try:
            from ui.parquet_processor import clear_manifest_cache
            clear_manifest_cache()
            st.success("Cache cleared! Data will reload on next access.")
        except Exception as e:
            st.error(f"Error clearing cache: {str(e)}")
    
    # Environment Info
    st.markdown("#### 🔧 Environment")
    env_info = {
        "Data directory exists (/data)": os.path.exists("/data"),
        "Temp directory exists (~/temp_data)": os.path.exists(os.path.expanduser("~/temp_data")),
        "Working directory": os.getcwd(),
        "Python path includes current dir": "." in sys.path
    }
    
    for key, value in env_info.items():
        icon = "✅" if value else "❌"
        st.write(f"{icon} {key}: {value}")


# Main admin page logic
st.subheader("🛠️ Admin")

if require_admin_access():
    # Show logout button
    render_admin_logout()

    # Show data management section
    render_data_management_section()

    st.markdown("---")

    # Client access and debug tools in expandable sections
    col1, col2 = st.columns(2)

    with col1:
        with st.expander("🔗 **Client Access**", expanded=False):
            render_client_access()

    with col2:
        with st.expander("🔧 **Debug Tools**", expanded=False):
            render_debug_interface()


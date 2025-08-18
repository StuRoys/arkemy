# pages/5_Admin.py
import streamlit as st

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

import os
import sys
from datetime import datetime

# Admin password (you can change this)
ADMIN_PASSWORD = "arkemy2024"

def check_admin_access():
    """Check if user has admin access"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    return st.session_state.admin_authenticated

def render_admin_login():
    """Render admin login form"""
    st.title("🔐 Admin Access")
    st.markdown("Enter password to access data management interface.")
    
    password = st.text_input("Password", type="password", key="admin_password")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col2:
        if st.button("Login", key="admin_login"):
            if password == ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.success("Access granted!")
                st.rerun()
            else:
                st.error("Invalid password")

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

def render_admin_interface():
    """Render the main admin interface"""
    st.title("🛠️ Arkemy Admin Panel")
    st.markdown("Data management interface for client deployments")
    
    # Logout button in sidebar
    with st.sidebar:
        st.markdown("### Admin Controls")
        if st.button("🚪 Logout", key="logout"):
            st.session_state.admin_authenticated = False
            st.rerun()
        
        st.markdown("---")
        st.markdown("**Volume:** `/data`")
    
    # Volume statistics
    render_volume_stats()
    
    st.markdown("---")
    
    # Main interface tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📁 Browse Files", "📤 Upload Files", "🔗 Client Link", "🐛 Debug"])
    
    with tab1:
        render_file_browser()
    
    with tab2:
        render_file_uploader()
    
    with tab3:
        render_client_link()
    
    with tab4:
        render_debug_interface()

# Main admin page logic
if check_admin_access():
    render_admin_interface()
else:
    render_admin_login()
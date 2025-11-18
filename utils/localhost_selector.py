"""
Localhost file selector for development workflow.

Provides client/file selection UI for localhost mode, allowing rapid switching
between client datasets without manual file management.
"""

import streamlit as st
import os
from typing import Optional, Tuple, List

# Placeholder constants
CLIENT_PLACEHOLDER = "-- Select Client --"
FILE_PLACEHOLDER = "-- Select File --"


def is_localhost() -> bool:
    """Check if running in localhost mode via st.secrets."""
    try:
        return st.secrets.get("localhost", False)
    except:
        return False


def get_data_directory() -> str:
    """Get the data directory path."""
    # In localhost mode, use project data directory
    project_data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    return project_data_dir


def get_client_directories() -> List[str]:
    """Get list of client subdirectories in /data (localhost only)."""
    data_dir = get_data_directory()
    if not os.path.exists(data_dir):
        return []

    clients = []
    for item in os.listdir(data_dir):
        item_path = os.path.join(data_dir, item)
        if os.path.isdir(item_path) and not item.startswith('.'):
            clients.append(item)

    return sorted(clients)


def get_files_in_client(client_name: str, file_extensions: Tuple[str, ...] = ('.parquet', '.pq')) -> List[dict]:
    """
    Get list of files in a client directory.

    Args:
        client_name: Name of the client directory
        file_extensions: Tuple of file extensions to filter (e.g., ('.parquet', '.pq') or ('.csv',))

    Returns:
        List of dicts with 'name', 'path', 'size_mb' keys
    """
    data_dir = get_data_directory()
    client_dir = os.path.join(data_dir, client_name)

    if not os.path.exists(client_dir):
        return []

    files = []
    for file in os.listdir(client_dir):
        if file.endswith(file_extensions):
            file_path = os.path.join(client_dir, file)
            size_mb = round(os.path.getsize(file_path) / (1024 * 1024), 2)
            files.append({
                'name': file,
                'path': file_path,
                'size_mb': size_mb
            })

    return sorted(files, key=lambda x: x['name'])


def render_localhost_file_selector(
    session_prefix: str = "",
    file_extensions: Tuple[str, ...] = ('.parquet', '.pq'),
    title: str = "📂 Data Selection (Localhost)"
) -> Tuple[Optional[str], Optional[str]]:
    """
    Render client/file selector in sidebar for localhost mode.

    Args:
        session_prefix: Prefix for session state keys to avoid conflicts between pages
        file_extensions: Tuple of file extensions to filter
        title: Title to display in sidebar

    Returns:
        Tuple of (selected_client, selected_file_path)
    """
    # Session state keys with prefix
    client_key = f"{session_prefix}selected_client" if session_prefix else "selected_client"
    file_key = f"{session_prefix}selected_file" if session_prefix else "selected_file"

    # Initialize session state
    if client_key not in st.session_state:
        st.session_state[client_key] = None
    if file_key not in st.session_state:
        st.session_state[file_key] = None

    with st.sidebar.expander("Select dataset"):
        clients = get_client_directories()

        if not clients:
            st.info("No client directories found in /data")
            return None, None

        # Client selector with placeholder
        client_options = [CLIENT_PLACEHOLDER] + clients

        # Determine current client index
        if st.session_state[client_key] and st.session_state[client_key] in clients:
            client_index = client_options.index(st.session_state[client_key])
        else:
            client_index = 0  # Placeholder

        selected_client_display = st.selectbox(
            "Select Client",
            options=client_options,
            index=client_index,
            key=f"{session_prefix}client_selector"
        )

        # Check if placeholder selected
        if selected_client_display == CLIENT_PLACEHOLDER:
            st.session_state[client_key] = None
            st.session_state[file_key] = None
            return None, None

        # Client changed - reset file selection
        if selected_client_display != st.session_state[client_key]:
            st.session_state[client_key] = selected_client_display
            st.session_state[file_key] = None

        # File selector
        files = get_files_in_client(selected_client_display, file_extensions)

        if not files:
            ext_display = ", ".join(file_extensions)
            st.info(f"No {ext_display} files in this client directory")
            return selected_client_display, None

        # Build file options with placeholder
        file_options_map = {f"{f['name']} ({f['size_mb']} MB)": f['path'] for f in files}
        file_display_options = [FILE_PLACEHOLDER] + list(file_options_map.keys())

        # Determine current file index
        current_file_display = None
        if st.session_state[file_key]:
            # Find the display name for the currently selected file path
            for display_name, path in file_options_map.items():
                if path == st.session_state[file_key]:
                    current_file_display = display_name
                    break

        if current_file_display and current_file_display in file_display_options:
            file_index = file_display_options.index(current_file_display)
        else:
            file_index = 0  # Placeholder

        selected_file_display = st.selectbox(
            "Select File",
            options=file_display_options,
            index=file_index,
            key=f"{session_prefix}file_selector_{selected_client_display}"
        )

        # Check if placeholder selected
        if selected_file_display == FILE_PLACEHOLDER:
            st.session_state[file_key] = None
            return selected_client_display, None

        # Get actual file path
        selected_file_path = file_options_map[selected_file_display]
        st.session_state[file_key] = selected_file_path

        return selected_client_display, selected_file_path

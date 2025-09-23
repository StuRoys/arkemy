# utils/admin_helpers.py
"""
Admin authentication and utility functions.
Extracted from pages/5_Admin.py for reuse across the application.
"""

import streamlit as st

# Admin password (you can change this)
ADMIN_PASSWORD = "arkemy2024"

def is_admin_authenticated() -> bool:
    """
    Check if user has admin access.

    Returns:
        bool: True if admin is authenticated, False otherwise
    """
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False

    return st.session_state.admin_authenticated

def render_admin_login() -> bool:
    """
    Render admin login form.

    Returns:
        bool: True if login was successful, False otherwise
    """
    password = st.text_input("Password", type="password", key="admin_password_login",
                             autocomplete="current-password", label_visibility="collapsed")

    if password:
        if password == ADMIN_PASSWORD:
            st.session_state.admin_authenticated = True
            st.success("Access granted!")
            st.rerun()
            return True
        else:
            st.error("Invalid password")

    return False

def require_admin_access():
    """
    Decorator-like function to require admin access.
    Returns True if admin is authenticated, False if login form should be shown.
    """
    if not is_admin_authenticated():
        render_admin_login()
        return False
    return True

def render_admin_logout():
    """Render admin logout button."""
    col1, col2, col3 = st.columns([3, 1, 1])

    with col2:
        if st.button("🚪 Logout", key="admin_logout"):
            st.session_state.admin_authenticated = False
            st.rerun()
# main.py - Application Entry Point and Orchestration
import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Set global app configuration
st.set_page_config(
    page_title="Arkemy: Turn Your Project Data Into Gold 🥇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize global session state variables
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

# Initialize authentication session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'user' not in st.session_state:
    st.session_state.user = None

# Initialize Supabase client
@st.cache_resource
def get_supabase_client():
    """Initialize and cache Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key or url == 'your_supabase_project_url_here':
        return None
    
    return create_client(url, key)


def check_authentication():
    """Check authentication status and set session state - no stopping here"""
    # Development bypass
    if os.getenv('ENVIRONMENT') == 'development':
        st.session_state.authenticated = True
        st.session_state.user = {'email': 'dev@localhost', 'role': 'developer'}
        return
    
    # Check if we already have authentication in session state
    if st.session_state.authenticated:
        return
    
    # Check if user has valid Supabase session
    supabase = get_supabase_client()
    if supabase:
        try:
            session = supabase.auth.get_session()
            if session and session.user:
                # Valid session found, restore authentication state
                st.session_state.authenticated = True
                st.session_state.user = session.user
                return
        except Exception as e:
            # Session check failed, user will need to login
            pass
    
    # No valid session found, user needs to authenticate

# Check authentication status
check_authentication()

# Dynamic page navigation based on authentication status
if st.session_state.authenticated:
    # Authenticated users see all app pages
    pages = [
        st.Page("pages/1_Analytics_Dashboard.py", title="Analytics Dashboard", icon="📊"),
        st.Page("pages/2_Coworker_Report.py", title="Coworker Report", icon="👥"),
        st.Page("pages/3_Project_Report.py", title="Project Report", icon="📁"),
        st.Page("pages/4_Hrs_SQM_Phase.py", title="Hours / m2 (beta)", icon="🏗️")
    ]
    
    print("🔍 TERMINAL: Setting up authenticated navigation")
else:
    # Non-authenticated users only see login page
    pages = [
        st.Page("pages/login.py", title="Login", icon="🔐")
    ]
    
    print("🔍 TERMINAL: Setting up login-only navigation")

# Set up navigation with dynamic pages
pg = st.navigation(pages)
pg.run()
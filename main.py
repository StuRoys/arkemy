# main.py - Application Entry Point with Authentication
import streamlit as st
import os
from dotenv import load_dotenv
import streamlit_authenticator as stauth

# Load environment variables
load_dotenv()

# Set page configuration
st.set_page_config(
    page_title="Arkemy: Turn Your Project Data Into Gold 🥇",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# AUTHENTICATION SETUP - RUNS FIRST
# ==========================================

# Authentication configuration
config = {
    'credentials': {
        'usernames': {
            'admin': {
                'name': 'Administrator',
                'password': 'password123'
            }
        }
    },
    'cookie': {
        'name': 'arkemy_auth',
        'key': 'arkemy_signature_key_2025', 
        'expiry_days': 30
    }
}

# Initialize authenticator
authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'], 
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    auto_hash=True
)

# Render login widget
authenticator.login(location='main')

# Get authentication status
name = st.session_state.get('name')
authentication_status = st.session_state.get('authentication_status') 
username = st.session_state.get('username')

# ==========================================
# AUTHENTICATION CHECK - STOP HERE IF NOT AUTHENTICATED
# ==========================================

# Check authentication status and handle accordingly
if authentication_status != True:
    # User is NOT authenticated - show only login screen
    if authentication_status == False:
        st.error('Username/password is incorrect')
    elif authentication_status == None:
        st.warning('Please enter your username and password')
    
    # STOP EXECUTION - nothing else should run
    st.stop()

# ==========================================
# AUTHENTICATED USER SECTION - ONLY RUNS IF LOGGED IN
# ==========================================

# User is authenticated - now set up the full application

# Initialize global session state variables (only for authenticated users)
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

# Set up app pages - ONLY for authenticated users
pages = [
    st.Page("app_pages/1_Analytics_Dashboard.py", title="Analytics Dashboard", icon="📊"),
    st.Page("app_pages/2_Coworker_Report.py", title="Coworker Report", icon="👥"),
    st.Page("app_pages/3_Project_Report.py", title="Project Report", icon="📁"),
    st.Page("app_pages/4_Hrs_SQM_Phase.py", title="Hours / m2 (beta)", icon="🏗️")
]

# Set up navigation - this creates the sidebar automatically
pg = st.navigation(pages)

# Add logout to sidebar AFTER navigation is set up
with st.sidebar:
    st.markdown("---")
    st.markdown(f"**Logged in as:** {name}")
    authenticator.logout('Logout', 'sidebar', key='logout_main')

# Run the authenticated application
pg.run()
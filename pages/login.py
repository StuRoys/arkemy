# pages/login.py - Dedicated Login Page
import streamlit as st
import os
from supabase import create_client
from streamlit_extras.stylable_container import stylable_container

# Set page configuration
st.set_page_config(
    page_title="Arkemy Login",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Try to override theme colors for buttons
try:
    st._config.set_option('theme.primaryColor', '#13d66e')
    st._config.set_option('theme.backgroundColor', '#ffffff')
    st._config.set_option('theme.secondaryBackgroundColor', '#f0f0f0')
    st._config.set_option('theme.textColor', '#000000')
except:
    pass  # Ignore if this doesn't work

@st.cache_resource
def get_supabase_client():
    """Initialize and cache Supabase client"""
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    
    if not url or not key or url == 'your_supabase_project_url_here':
        return None
    
    return create_client(url, key)

@st.dialog("Create Account")
def signup_modal():
    """Modal dialog for account creation"""
    supabase = get_supabase_client()
    
    with st.form("signup_form", clear_on_submit=False):
        signup_email = st.text_input("Email", placeholder="your@email.com", key="signup_email", label_visibility="collapsed")
        signup_password = st.text_input("Password", type="password", placeholder="Choose a password", key="signup_password", label_visibility="collapsed")
        
        # Buttons side by side INSIDE the form
        col1, col2 = st.columns(2)
        
        with col1:
            with stylable_container(
                key="signup_button",
                css_styles="""
                    button {
                        background-color: #13d66e !important;
                        color: white !important;
                        border: 1px solid #13d66e !important;
                        border-radius: 4px !important;
                        font-family: 'Poppins', sans-serif !important;
                        font-weight: 500 !important;
                    }
                    button:hover {
                        background-color: #11c162 !important;
                        border-color: #0fa855 !important;
                    }
                """
            ):
                signup_clicked = st.form_submit_button("Create Account", use_container_width=True)
        
        # We can't put a regular button inside a form, so we'll handle this differently
        # Instead, we'll add a second submit button that acts like cancel
        with col2:
            with stylable_container(
                key="cancel_button_form",
                css_styles="""
                    button {
                        background-color: #6c757d !important;
                        color: white !important;
                        border: 1px solid #6c757d !important;
                        border-radius: 4px !important;
                        font-family: 'Poppins', sans-serif !important;
                        font-weight: 500 !important;
                    }
                    button:hover {
                        background-color: #5a6268 !important;
                        border-color: #545b62 !important;
                    }
                """
            ):
                cancel_clicked = st.form_submit_button("Cancel", use_container_width=True)
    
    # Handle signup logic
    if signup_clicked and signup_email and signup_password:
        try:
            with st.spinner("Creating account..."):
                response = supabase.auth.sign_up({
                    "email": signup_email,
                    "password": signup_password
                })
                
                if response.user:
                    st.success("Account created! Please check your email to confirm your account, then login.")
                    st.rerun()
                else:
                    st.error("Account creation failed.")
        except Exception as e:
            st.error(f"Account creation failed: {str(e)}")
    
    # Handle cancel
    if cancel_clicked:
        st.rerun()

def show_login_page():
    """Display the login page"""
    # Force CSS cache bust and fix button colors + autofill
    import time
    cache_bust = str(int(time.time()))
    
    st.markdown(f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;700&display=swap?v={cache_bust}');
        
        /* Apply Poppins to all text elements */
        .stApp {{
            font-family: 'Poppins', sans-serif;
        }}
        
        .centered-title {{
            font-family: 'Poppins', sans-serif;
            text-align: center;
            font-size: 2.5rem;
            font-weight: 700;
            letter-spacing: 2px;
            margin: 2rem 0;
        }}
        .centered-text {{
            font-family: 'Poppins', sans-serif;
            text-align: center;
            margin: 1rem 0;
        }}
        
        /* Apply Poppins to form elements and hide borders */
        .stTextInput label, .stTextInput input {{
            font-family: 'Poppins', sans-serif !important;
        }}
        
        /* Target the exact form container */
        .st-emotion-cache-1bcyifm {{
            border: none !important;
            box-shadow: none !important;
        }}
        
        /* Target input root elements */
        div[data-testid="stTextInputRootElement"] {{
            border: none !important;
            border-radius: 8px !important;
            background-color: #f8f9fa !important;
            box-shadow: none !important;
        }}
        
        /* Target the actual input element */
        input[type="text"], input[type="password"] {{
            border: none !important;
            border-radius: 8px !important;
            background-color: #f8f9fa !important;
            padding: 12px 16px !important;
            font-size: 16px !important;
            box-shadow: none !important;
        }}
        
        input[type="text"]:focus, input[type="password"]:focus {{
            border: none !important;
            box-shadow: 0 0 0 2px rgba(19, 214, 110, 0.2) !important;
            outline: none !important;
            background-color: #f8f9fa !important;
        }}
        
        /* Hide autofill icons */
        input::-webkit-credentials-auto-fill-button {{
            visibility: hidden;
            position: absolute;
            right: 0;
        }}
        
        /* Force Poppins font on button text using exact selectors */
        .st-emotion-cache-17c7e5f {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 500 !important;
        }}
        
        .st-emotion-cache-czkz86 {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 500 !important;
        }}
        
        /* Target button text containers more broadly */
        .st-emotion-cache-17c7e5f p {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 500 !important;
        }}
        
        .st-emotion-cache-czkz86 p {{
            font-family: 'Poppins', sans-serif !important;
            font-weight: 500 !important;
        }}
    </style>
    
    <script>
        // Disable autofill ONLY on login form, allow on signup
        function disableLoginAutofill() {{
            // Only target the main login form inputs
            const loginForm = document.querySelector('form[data-testid]');
            if (loginForm) {{
                const emailInput = loginForm.querySelector('input[key="login_email"]') || 
                                 loginForm.querySelector('input[placeholder*="email.com"]');
                const passwordInput = loginForm.querySelector('input[key="login_password"]') || 
                                    loginForm.querySelector('input[type="password"][placeholder*="password"]');
                
                if (emailInput) {{
                    emailInput.setAttribute('autocomplete', 'off');
                    emailInput.setAttribute('name', 'fake_email_' + Math.random());
                }}
                
                if (passwordInput) {{
                    passwordInput.setAttribute('autocomplete', 'off');
                    passwordInput.setAttribute('name', 'fake_password_' + Math.random());
                }}
            }}
        }}
        
        // Run multiple times to catch dynamic content
        document.addEventListener('DOMContentLoaded', disableLoginAutofill);
        setTimeout(disableLoginAutofill, 500);
        setTimeout(disableLoginAutofill, 1000);
        setTimeout(disableLoginAutofill, 2000);
    </script>
    """, unsafe_allow_html=True)
    
    # Simple centered layout using native Streamlit columns
    _, col2, _ = st.columns([1, 2, 1])
    
    with col2:
        # Centered branding
        st.markdown('<div class="centered-title">ARKEMY</div>', unsafe_allow_html=True)
        
        supabase = get_supabase_client()
        
        if not supabase:
            st.error("🔧 Authentication not configured. Please add SUPABASE_URL and SUPABASE_KEY to your .env file.")
            st.info("For development, you can also set ENVIRONMENT=development in .env to bypass auth.")
            
            # Development bypass option
            with stylable_container(
                key="dev_mode_button",
                css_styles="""
                    button {
                        background-color: #ffc107 !important;
                        color: #212529 !important;
                        border: 1px solid #ffc107 !important;
                        border-radius: 4px !important;
                        font-family: 'Poppins', sans-serif !important;
                        font-weight: 500 !important;
                    }
                    button:hover {
                        background-color: #ffcd39 !important;
                        border-color: #ffc720 !important;
                    }
                """
            ):
                if st.button("Continue in Development Mode", help="Skip authentication for local testing"):
                    st.session_state.authenticated = True
                    st.session_state.user = {'email': 'dev@localhost', 'role': 'developer'}
                    st.rerun()
            return
        
        # Main login form
        with st.form("login_form", clear_on_submit=False):
            email = st.text_input("Email", placeholder="your@email.com", key="login_email", label_visibility="collapsed")
            password = st.text_input("Password", type="password", placeholder="Password", key="login_password", label_visibility="collapsed")
            
            with stylable_container(
                key="login_button", 
                css_styles="""
                    button {
                        background-color: #13d66e !important;
                        color: white !important;
                        border: 1px solid #13d66e !important;
                        border-radius: 4px !important;
                        font-family: 'Poppins', sans-serif !important;
                        font-weight: 500 !important;
                    }
                    button:hover {
                        background-color: #11c162 !important;
                        border-color: #0fa855 !important;
                    }
                """
            ):
                login_clicked = st.form_submit_button("Log in to your ARKEMY dashboard", use_container_width=True)
        
        # Simple spacing
        st.markdown("")
        
        # Signup section - centered text and button
        st.markdown('<div class="centered-text">Don\'t have an account?</div>', unsafe_allow_html=True)
        
        _, col_b, _ = st.columns([1, 1, 1])
        with col_b:
            with stylable_container(
                key="create_account_button",
                css_styles="""
                    button {
                        background-color: #13d66e !important;
                        color: white !important;
                        border: 1px solid #13d66e !important;
                        border-radius: 4px !important;
                        font-family: 'Poppins', sans-serif !important;
                        font-weight: 500 !important;
                    }
                    button:hover {
                        background-color: #11c162 !important;
                        border-color: #0fa855 !important;
                    }
                """
            ):
                if st.button("Create Account", use_container_width=True):
                    signup_modal()
        
        # Handle login (outside the form)
        if login_clicked and email and password:
            try:
                with st.spinner("Signing in..."):
                    response = supabase.auth.sign_in_with_password({
                        "email": email,
                        "password": password
                    })
                    
                    if response.user:
                        st.session_state.authenticated = True
                        st.session_state.user = response.user
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error("Login failed. Please check your credentials.")
            except Exception as e:
                st.error(f"Login failed: {str(e)}")
        

# Main login page logic
show_login_page()
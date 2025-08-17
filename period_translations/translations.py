import json
import os
import streamlit as st

def load_translations(language):
    """
    Load translations for the specified language from JSON file.
    
    Parameters:
    language (str): Language code (e.g., 'en', 'no')
    
    Returns:
    dict: Translation dictionary for the specified language
    """
    # Path to translations directory
    translations_dir = os.path.join(os.path.dirname(__file__), 'translations')
    
    # Create directory if it doesn't exist
    if not os.path.exists(translations_dir):
        os.makedirs(translations_dir)
    
    # Path to language file
    language_file = os.path.join(translations_dir, f"{language}.json")
    
    # Check if language file exists
    if not os.path.exists(language_file):
        # Create default English file if it doesn't exist
        if language == 'en':
            default_en = {
                "upload_csv": "Upload your CSV-file here!",
                "upload_instruction": "Upload your CSV file",
                "filter_data": "Filter data",
                "period": "Period",
                "full_year": "Full year",
                "quarters": "Quarters",
                "custom": "Custom",
                "select_year": "Select Year",
                "select_quarter": "Select Quarter",
                "q1": "Q1 (Jan-Mar)",
                "q2": "Q2 (Apr-Jun)",
                "q3": "Q3 (Jul-Sep)",
                "q4": "Q4 (Oct-Dec)",
                "select_date_range": "Select Date Range",
                "select_person": "Select Person",
                "no_person_column": "No 'Person' column found in the data.",
                "no_period_column": "No 'Period' column found in the data. Filter not applied.",
                "time_spent": "Time spent on projects",
                "forecast": "Forecast",
                "data_from_csv": "Data from uploaded CSV:",
                "select_person_warning": "Please select a person to view the chart.",
                "language": "Language",
                "data": "Data",
                "hours_chart_title": "Hours for {person}",
                "billable_rate_chart_title": "Billable Rate for {person}",
                "capacity_period": "Capacity/Period",
                "hours_period": "Hours/Period",
                "absence_period": "Absence/Period",
                "hours_registered": "Hours Registered",
                "project_hours": "Project Hours",
                "planned_hours": "Planned Hours",
                "unpaid_work": "Unpaid Work",
                "billable_rate": "Billable Rate",
                "billable_rate_percent": "Billable Rate (%)",
                "hrs": "hrs",
                "missing_required_column": "Missing required column"
            }
            with open(language_file, 'w', encoding='utf-8') as f:
                json.dump(default_en, f, indent=2)
        else:
            st.warning(f"Translation file for {language} not found. Using English.")
            return load_translations('en')
    
    # Load translations
    with open(language_file, 'r', encoding='utf-8') as f:
        translations = json.load(f)
    
    return translations

def get_text(key):
    """
    Get translated text for a key.
    
    Parameters:
    key (str): Translation key
    
    Returns:
    str: Translated text
    """
    if 'translations' not in st.session_state:
        # Default to English if no translations in session state
        st.session_state.translations = load_translations('en')
    
    # Get the translation
    if key in st.session_state.translations:
        return st.session_state.translations[key]
    else:
        # Return the key if translation not found
        return key

def initialize_translations():
    """
    Initialize translations in session state.
    """
    # Initialize language if not already done
    if 'language' not in st.session_state:
        st.session_state.language = 'en'
    
    # Force reload translations (for development - remove in production)
    st.session_state.translations = load_translations(st.session_state.language)

# Shorthand function name for convenience
def t(key):
    """
    Shorthand for get_text()
    """
    return get_text(key)
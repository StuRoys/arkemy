"""
Dataset Selection Page (Localhost Only)

Pre-navigation screen for selecting dataset in localhost mode.
After data is loaded, automatically navigates to main application.
"""

import streamlit as st
import os
import glob
from utils.localhost_selector import render_localhost_file_selector
from utils.unified_data_loader import UnifiedDataLoader

# Set page configuration
st.set_page_config(
    page_title="Arkemy - Select Dataset",
    page_icon="📂",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page header
st.title("📂 Select Dataset")
st.markdown("---")

# Instructions
st.markdown("""
### Welcome to Arkemy (Localhost Mode)

Select a dataset to begin your analysis. The selected dataset will be available across all pages.

**Instructions:**
1. Select a client from the dropdown
2. Choose a data file
3. Click "Load Dataset" to proceed
""")

st.markdown("---")

# Render file selector
selected_client, selected_file_path = render_localhost_file_selector(
    session_prefix="global_",
    file_extensions=('.parquet', '.pq'),
    title="📂 Dataset Selection"
)

# Show selection status
if selected_file_path:
    st.success(f"✓ Selected: `{selected_file_path}`")

    # Load button
    if st.button("🚀 Load Dataset", type="primary", use_container_width=True):
        with st.spinner("Loading dataset..."):
            try:
                # Initialize loader
                loader = UnifiedDataLoader()

                # Load data
                loading_results = loader.load_unified_data(
                    file_path=selected_file_path
                )

                if loading_results.get('success', False):
                    # Extract data
                    processed_data = loading_results.get('processed_data', {})
                    time_records = processed_data.get('time_record')
                    planned_records = processed_data.get('planned_record')

                    # Update session state with loaded data
                    if time_records is not None and not time_records.empty:
                        st.session_state.transformed_df = time_records
                        st.session_state.csv_loaded = True

                    if planned_records is not None and not planned_records.empty:
                        st.session_state.transformed_planned_df = planned_records
                        st.session_state.planned_csv_loaded = True

                    # Store currency
                    currency = loading_results.get('currency', 'nok')
                    st.session_state.currency = currency.lower()
                    st.session_state.currency_selected = True

                    # Store file path for tracking
                    st.session_state.loaded_file_path = selected_file_path

                    # Store tag mappings if available
                    analysis = loading_results.get('analysis', {})
                    if 'tag_mappings' in analysis:
                        st.session_state.tag_mappings = analysis['tag_mappings']

                    # Scan for CSV files in the same directory
                    directory = os.path.dirname(selected_file_path)

                    # Look for coworker CSV
                    coworker_files = glob.glob(os.path.join(directory, '*coworker*.csv'))
                    if coworker_files:
                        st.session_state.coworker_csv_path = coworker_files[0]
                        st.session_state.coworker_available = True
                    else:
                        st.session_state.coworker_csv_path = None
                        st.session_state.coworker_available = False

                    # Look for hrs/sqm CSV
                    sqm_files = glob.glob(os.path.join(directory, '*hrs_sqm_phase*.csv'))
                    if sqm_files:
                        st.session_state.sqm_csv_path = sqm_files[0]
                        st.session_state.sqm_available = True
                    else:
                        st.session_state.sqm_csv_path = None
                        st.session_state.sqm_available = False

                    # Success message
                    st.success("✓ Dataset loaded successfully!")

                    # Show what's available
                    available_features = []
                    if st.session_state.coworker_available:
                        available_features.append("Coworker Report")
                    if st.session_state.sqm_available:
                        available_features.append("Hrs/m²/Phase")

                    if available_features:
                        st.info(f"✓ Additional features available: {', '.join(available_features)}")

                    st.info("Navigating to Analytics Dashboard...")

                    # Small delay for user to see success message
                    import time
                    time.sleep(1)

                    # Rerun to trigger navigation to main app
                    st.rerun()
                else:
                    # Show error
                    error_msg = loading_results.get('error', 'Unknown error occurred')
                    st.error(f"Failed to load dataset: {error_msg}")

            except Exception as e:
                st.error(f"Error loading dataset: {str(e)}")
                st.exception(e)
else:
    st.info("👆 Please select a client and file to continue")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; font-size: 0.9em;'>
    <p>Localhost Testing Mode | Change datasets anytime using the reset button in the sidebar</p>
</div>
""", unsafe_allow_html=True)

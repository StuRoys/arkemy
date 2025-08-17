# ui/uploader.py
import streamlit as st
from app_explainer import get_app_explainer_text
from utils.currency_formatter import get_currency_selector, get_currency_display_name

def render_upload_interface():
    """
    Renders the initial data upload interface when no data is loaded.
    """
    # Set page title
    st.title('Arkemy: Turn Your Project Data Into Gold 🥇')
    st.markdown("##### v1.3.1 Parquet")

    # Create a container for all uploaders
    st.markdown("### Data Upload")
    st.markdown("Upload your Parquet file to begin analyzing your project data.")
    
    # Create a 2-column layout
    col1, col2 = st.columns(2)
    
    with col1:
        # Parquet file uploader
        st.markdown("#### 1. Combined Data File (Required)")
        parquet_file = st.file_uploader("Select and upload combined Parquet file", type=["parquet", "pq"], key="parquet_uploader")
        
        # Currency selector (required)
        st.markdown("#### 2. Currency Setting (Required)")
        currency_valid, currency_message = get_currency_selector("upload_currency_selector", required=True)
        
        # Show the current currency selection
        if currency_valid:
            st.success(f"Selected currency: {get_currency_display_name()}")
            st.session_state.currency_selected = True
        
        # Process Parquet file if both file is uploaded AND currency is selected
        if parquet_file is not None and currency_valid:
            process_button = st.button("Process Data", key="process_data_button")
            
            if process_button:
                import tempfile
                import os
                from ui.parquet_processor import process_parquet_data_from_path
                
                # Get the original filename to preserve client/currency detection
                original_filename = parquet_file.name
                
                # Create temporary file with original filename pattern
                temp_dir = tempfile.gettempdir()
                tmp_path = os.path.join(temp_dir, original_filename)
                
                # Ensure we don't overwrite existing temp files by adding a unique suffix if needed
                counter = 1
                base_path = tmp_path
                while os.path.exists(tmp_path):
                    name, ext = os.path.splitext(base_path)
                    tmp_path = f"{name}_{counter}{ext}"
                    counter += 1
                
                try:
                    # Save uploaded file to temporary location with original filename
                    with open(tmp_path, 'wb') as tmp_file:
                        tmp_file.write(parquet_file.getvalue())
                    
                    # Process the temporary file
                    process_parquet_data_from_path(tmp_path)
                finally:
                    # Clean up temporary file
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    with col2:
        # Display app explainer text in the second column
        st.markdown(get_app_explainer_text(), unsafe_allow_html=True)
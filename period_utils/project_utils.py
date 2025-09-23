import pandas as pd
import numpy as np
import streamlit as st
from period_translations.translations import t

def prepare_project_dataframe(df):
    """Prepare project dataframe for visualization."""
    # Create a copy to avoid modifying original
    df_copy = df.copy()
    
    # Ensure Period is datetime for proper sorting
    if "Period" in df_copy.columns and not pd.api.types.is_datetime64_any_dtype(df_copy["Period"]):
        df_copy["Period"] = pd.to_datetime(df_copy["Period"], errors='coerce')
    
    # Drop duplicate columns
    df_copy = df_copy.loc[:, ~df_copy.columns.duplicated()]
    
    # Add formatted period string for display
    if "Period" in df_copy.columns:
        df_copy["Period_display"] = df_copy["Period"].dt.strftime("%b %Y")
    
    return df_copy

def create_translation_map(metric_types):
    """Create translation mapping for metric types."""
    translations_map = {}
    
    for metric in metric_types:
        # Convert to lowercase and replace spaces with underscores for translation key
        translation_key = metric.lower().replace(" ", "_").replace("/", "_")
        translations_map[metric] = t(translation_key) if translation_key in st.session_state.translations else metric
    
    return translations_map

def create_color_map(metric_types, scheme="blue"):
    """Create color mapping for metric types based on color scheme."""
    color_schemes = {
        "blue": {
            "primary": "#1f77b4",    # Deep blue
            "secondary": "#9ecae1"    # Light blue
        },
        "green": {
            "primary": "#2e8b57",    # Sea green
            "secondary": "#90ee90"    # Light green
        },
        "purple": {
            "primary": "#9370db",    # Medium purple
            "secondary": "#d8bfd8"    # Thistle
        }
    }
    
    selected_scheme = color_schemes.get(scheme, color_schemes["blue"])
    
    # Assign colors based on position in list (inverse so "used" gets darker primary color)
    if len(metric_types) >= 2:
        return {
            metric_types[0]: selected_scheme["secondary"],  # Planned data gets light color
            metric_types[1]: selected_scheme["primary"]     # Used data gets dark color
        }
    elif len(metric_types) == 1:
        return {metric_types[0]: selected_scheme["primary"]}
    else:
        return {}

def create_hover_template(include_units=False, unit_text="", decimal_places=0):
    """Create a custom hover template for charts."""
    format_str = f":.{decimal_places}f"
    
    if include_units:
        hovertemplate = (
            f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
            f"%{{x}}<br>"
            f"%{{y{format_str}}} {unit_text}</span><br>"
            "<extra></extra>"
        )
    else:
        hovertemplate = (
            f"<span style='font-size:16px'><b>%{{customdata[0]}}</b><br>"
            f"%{{x}}<br>"
            f"%{{y{format_str}}}</span><br>"
            "<extra></extra>"
        )
    
    return hovertemplate

def display_summary_metrics(df, value_cols, translations_map, format_suffix="", decimal_places=1):
    """Display summary metrics in two columns."""
    if df.empty:
        return
    
    # Create summary
    st.markdown(f"### {t('summary')}")
    
    # Create columns for metrics
    columns = st.columns(len(value_cols))
    
    # Calculate stats for each column
    for i, (col, col_display) in enumerate(zip(value_cols, columns)):
        # Get value to display
        value = df[col].sum() if col in df.columns else 0
        
        # Format value with specified decimal places
        formatted_value = f"{value:.{decimal_places}f}{format_suffix}"
        
        # Display metric
        with col_display:
            st.metric(
                translations_map.get(col, col),
                formatted_value
            )
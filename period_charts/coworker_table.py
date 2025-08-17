import streamlit as st
import pandas as pd
from period_translations.translations import t

def render_person_table(df, selected_person):
    """
    Render a table showing data filtered by person with translated headers.
    
    Parameters:
    df (DataFrame): The DataFrame containing the data
    selected_person (str): The person to filter by
    """
    # Check if Person column exists
    if "Person" not in df.columns:
        st.error(t("missing_required_column") + " Person")
        return
    
    # Filter data by selected person
    filtered_df = df[df["Person"] == selected_person]
    
    # Sort by Period if it exists
    if "Period" in filtered_df.columns:
        filtered_df = filtered_df.sort_values("Period")
    
    # Translation mapping for columns
    translation_mapping = {
        "Period": t("period"),
        "Person": t("select_person"),
        "Capacity/Period": t("capacity_period"),
        "Hours/Period": t("hours_period"),
        "Absence/Period": t("absence_period"),
        "Hours/Registered": t("hours_registered"),
        "Project hours": t("project_hours"),
        "Planned hours": t("planned_hours"),
        "Unpaid work": t("unpaid_work"),
        "Billable Rate": t("billable_rate")
    }
    
    # Create a display copy with translated column names
    display_df = filtered_df.copy()
    display_df = display_df.rename(columns=translation_mapping)
    
    # Create column config for special formatting
    column_config = {}
    
    # Add datetime formatting for Period column if it exists
    period_translated = t("period")
    if period_translated in display_df.columns:
        column_config[period_translated] = st.column_config.DatetimeColumn(format="MMM, YYYY")
    
    # Display the dataframe with translated headers
    st.dataframe(display_df, column_config=column_config)
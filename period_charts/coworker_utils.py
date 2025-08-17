import streamlit as st
import pandas as pd
from period_translations.translations import t

def render_details_section(filtered_df):
    """
    Render the 'Details' expander with summary metrics.
    
    Parameters:
    filtered_df (DataFrame): The filtered DataFrame containing data for a specific person
    """
    # Put summary in an expander
    with st.expander("Details"):
        if filtered_df.empty:
            st.info("No data available for the selected period and person.")
            return
        
        # Calculate sums
        sum_hours_period = filtered_df["Hours/Period"].sum() if "Hours/Period" in filtered_df.columns else 0
        sum_absence = filtered_df["Absence/Period"].sum() if "Absence/Period" in filtered_df.columns else 0
        sum_capacity = filtered_df["Capacity/Period"].sum()
        sum_registered = filtered_df["Hours/Registered"].sum() if "Hours/Registered" in filtered_df.columns else 0
        sum_project_hours = filtered_df["Project hours"].sum()
        sum_unpaid = filtered_df["Unpaid work"].sum() if "Unpaid work" in filtered_df.columns else 0
        
        # Calculate ratios (with safeguards against division by zero)
        absence_percent = (sum_absence / sum_hours_period * 100) if sum_hours_period != 0 else 0
        capacity_percent = (sum_capacity / sum_hours_period * 100) if sum_hours_period != 0 else 0
        
        # Registered hour ratios
        registered_vs_schedule = (sum_registered / sum_hours_period * 100) if sum_hours_period != 0 else 0
        registered_vs_capacity = (sum_registered / sum_capacity * 100) if sum_capacity != 0 else 0
        
        # Billable hour ratios
        billable_vs_schedule = (sum_project_hours / sum_hours_period * 100) if sum_hours_period != 0 else 0
        billable_vs_capacity = (sum_project_hours / sum_capacity * 100) if sum_capacity != 0 else 0
        billable_vs_registered = (sum_project_hours / sum_registered * 100) if sum_registered != 0 else 0
        
        # Non-billable hour ratios
        non_billable_vs_schedule = (sum_unpaid / sum_hours_period * 100) if sum_hours_period != 0 else 0
        non_billable_vs_capacity = (sum_unpaid / sum_capacity * 100) if sum_capacity != 0 else 0
        non_billable_vs_registered = (sum_unpaid / sum_registered * 100) if sum_registered != 0 else 0
        
        # Section 1: Capacity calculation
        st.subheader("Schedule - Planned absence = Capacity")
        cols1 = st.columns([3, 1, 3, 1, 3])
        
        with cols1[0]:
            st.metric("Schedule", f"{sum_hours_period:.0f} {t('hrs')}")
            st.metric("Schedule %", "100.0%")
        
        with cols1[1]:
            st.markdown("# −", help=None)
            st.markdown("# −", help=None)
        
        with cols1[2]:
            st.metric("Planned absence", f"{sum_absence:.0f} {t('hrs')}")
            st.metric("Planned absence %", f"{absence_percent:.1f}%")
        
        with cols1[3]:
            st.markdown("# =", help=None)
            st.markdown("# =", help=None)
        
        with cols1[4]:
            st.metric("Capacity", f"{sum_capacity:.0f} {t('hrs')}")
            st.metric("Capacity %", f"{capacity_percent:.1f}%")
        
        # Section 2: Hours registration
        st.subheader("Hours Registered - Billable = Non-billable")
        cols2 = st.columns(3)
        
        with cols2[0]:
            st.metric("Registered hours", f"{sum_registered:.0f} {t('hrs')}")
            st.metric("Registered vs Schedule", f"{registered_vs_schedule:.1f}%")
            st.metric("Registered vs Capacity", f"{registered_vs_capacity:.1f}%")
        
        with cols2[1]:
            st.metric("Billable hours", f"{sum_project_hours:.0f} {t('hrs')}")
            st.metric("Billable vs Schedule", f"{billable_vs_schedule:.1f}%")
            st.metric("Billable vs Capacity", f"{billable_vs_capacity:.1f}%")
            st.metric("Billable vs Registered", f"{billable_vs_registered:.1f}%")
        
        with cols2[2]:
            st.metric("Non-billable hours", f"{sum_unpaid:.0f} {t('hrs')}")
            st.metric("Non-billable vs Schedule", f"{non_billable_vs_schedule:.1f}%")
            st.metric("Non-billable vs Capacity", f"{non_billable_vs_capacity:.1f}%")
            st.metric("Non-billable vs Registered", f"{non_billable_vs_registered:.1f}%")

def render_data_section(filtered_df):
    """
    Render the 'Data' expander with the dataframe display.
    
    Parameters:
    filtered_df (DataFrame): The filtered DataFrame containing data for a specific person
    """
    with st.expander(t('data')):
        if filtered_df.empty:
            st.info("No data available for the selected period and person.")
            return
        
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
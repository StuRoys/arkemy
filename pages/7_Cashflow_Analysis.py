"""
Cashflow Analysis Page

Shows monthly cashflow with Sankey diagram and period comparison KPIs.
Uses unfiltered company-wide data (overrides sidebar filters).
"""

import streamlit as st
from period_charts.cashflow_analysis import render_cashflow_analysis

# Set page configuration
st.set_page_config(
    layout="wide",
    initial_sidebar_state="expanded"
)

# Page header
st.subheader("💰 Cashflow Analysis")

# Access unfiltered data from session state
if not st.session_state.get('csv_loaded', False) or st.session_state.transformed_df is None:
    st.error("📂 No data loaded. Please load data from the Analytics Dashboard.")
    st.stop()

# Get unfiltered data (override sidebar filters for company-wide view)
unfiltered_df = st.session_state.transformed_df

# Render cashflow analysis
render_cashflow_analysis(unfiltered_df)

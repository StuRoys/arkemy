# ui/coworker_dashboard.py
import streamlit as st
import pandas as pd
from typing import Dict, Any, Optional, Tuple

from processors.coworker_processor import (
    process_coworker_data,
    setup_coworker_filters,
    apply_coworker_filters,
    calculate_coworker_summary_metrics,
    get_person_performance_ranking,
    generate_coworker_insights
)
from charts.coworker_charts import (
    render_coworker_comparison_chart,
    render_coworker_hours_flow_chart,
    render_coworker_forecast_chart,
    render_coworker_details_section,
    render_coworker_data_section
)

def render_coworker_dashboard(transformed_df: pd.DataFrame, 
                             planned_df: Optional[pd.DataFrame] = None,
                             filter_settings: Optional[Dict] = None):
    """
    Main coworker dashboard interface.
    
    This function creates the complete coworker analysis interface,
    integrating with the existing Arkemy data and UI patterns.
    
    Args:
        transformed_df: Main Arkemy dataframe
        planned_df: Optional planned hours dataframe
        filter_settings: Existing filter settings from main dashboard
    """
    st.header("📊 Coworker Analysis")
    
    # Process data
    with st.spinner("Processing coworker data..."):
        coworker_df, quality_info = process_coworker_data(
            transformed_df, 
            planned_df, 
            filter_settings
        )
    
    
    # Handle empty data
    if coworker_df.empty:
        st.warning("No coworker data available. Please check your data source and filters.")
        show_data_requirements()
        return
    
    # Show data quality information
    show_data_quality_info(quality_info)
    
    # For initial release, use simple defaults to ensure content renders immediately
    # Future enhancement: integrate with main dashboard filters or add dedicated coworker filters
    
    # Default to showing all data with "All coworkers" selected
    available_persons = coworker_df["person_name"].unique().tolist()
    default_person = "All coworkers" if "All coworkers" in available_persons else (available_persons[0] if available_persons else None)
    
    # Simple person selection without complex filtering for now
    st.subheader("👥 Person Selection")
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_person = st.selectbox(
            "Select Person",
            available_persons,
            index=available_persons.index(default_person) if default_person in available_persons else 0
        )
    
    # Apply simple person filter - use all data for the selected person
    if selected_person:
        filtered_df = coworker_df[coworker_df["person_name"] == selected_person].copy()
    else:
        filtered_df = coworker_df.copy()
    
    filter_info = {"person": selected_person}
    
    if filtered_df.empty:
        st.warning("No data matches the selected filters. Please adjust your filter criteria.")
        return
    
    # Remove debug info for production
    # st.write(f"Debug: Filtered data shape: {filtered_df.shape}, Selected person: {selected_person}")
    # if not filtered_df.empty:
    #     st.write(f"Debug: Available columns: {list(filtered_df.columns)}")
    #     st.write(f"Debug: Unique persons in filtered data: {filtered_df['Person'].unique().tolist()}")
    
    # Main dashboard content
    render_coworker_summary(filtered_df, selected_person)
    
    # Initialize chart type selection in session state
    if 'coworker_chart_type' not in st.session_state:
        st.session_state.coworker_chart_type = "Bar chart"
    
    # Chart type selection
    st.markdown('<div class="nav-tertiary">', unsafe_allow_html=True)
    chart_type = st.radio(
        "Chart Type",
        ["Bar chart", "Hours Flow", "Forecast", "Insights"],
        index=["Bar chart", "Hours Flow", "Forecast", "Insights"].index(st.session_state.coworker_chart_type),
        key='coworker_chart_type',
        horizontal=True
    )
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Render content based on selected chart type
    if chart_type == "Bar chart":
        render_comparison_section(filtered_df, selected_person)
    elif chart_type == "Hours Flow":
        render_hours_flow_section(filtered_df, selected_person)
    elif chart_type == "Forecast":
        render_forecast_section(filtered_df, selected_person)
    elif chart_type == "Insights":
        render_insights_section(filtered_df, selected_person, coworker_df)

def show_data_quality_info(quality_info: Dict[str, Any]):
    """Display data quality information and warnings."""
    if quality_info.get("status") == "error":
        st.error(f"Data processing error: {quality_info.get('message', 'Unknown error')}")
        return
    
    if quality_info.get("status") == "no_data":
        return
    
    # Show warnings in expander
    warnings = quality_info.get("warnings", [])
    if warnings:
        with st.expander("⚠️ Data Quality Warnings", expanded=False):
            for warning in warnings:
                if warning == "absence_data_missing":
                    st.warning("📅 Absence data not available - using estimates")
                elif warning == "schedule_data_estimated":
                    st.info("⏰ Schedule data estimated from working days")
    
    # Show data completeness
    completeness = quality_info.get("data_completeness", {})
    if completeness:
        with st.expander("📊 Data Completeness", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            for i, (field, rate) in enumerate(completeness.items()):
                col = [col1, col2, col3][i % 3]
                with col:
                    st.metric(
                        field.replace("_", " ").title(),
                        f"{rate:.1%}",
                        delta=None
                    )

def show_data_requirements():
    """Show information about data requirements for coworker analysis."""
    with st.expander("📋 Coworker Analysis Requirements", expanded=True):
        st.markdown("""
        **Current Data Sources:**
        - ✅ Hours worked (from Arkemy time tracking)
        - ✅ Billable hours (from Arkemy time tracking)
        - ✅ Planned hours (if available)
        
        **Enhanced Features Available With Additional Data:**
        - 📅 **Schedule Data**: Planned working hours per period
        - 🏥 **Absence Data**: Vacation, sick leave, holidays
        - ⏱️ **Registration Data**: Time logged vs time worked
        
        **Current Analysis Based On:**
        - Estimated capacity from working days
        - Project hours vs capacity ratios
        - Period-based performance trends
        """)

def render_coworker_summary(df: pd.DataFrame, selected_person: str):
    """Render summary metrics for the selected person/period."""
    if df.empty:
        return
    
    # Calculate summary metrics
    metrics = calculate_coworker_summary_metrics(df)
    
    # Display key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Periods Analyzed",
            metrics.get("total_periods", 0)
        )
    
    with col2:
        billable_rate = metrics.get("overall_billable_rate", 0)
        st.metric(
            "Overall Billable Rate",
            f"{billable_rate}%",
            delta=f"{billable_rate - 80:.1f}%" if billable_rate != 0 else None,
            delta_color="normal"
        )
    
    with col3:
        total_capacity = metrics.get("total_capacity", 0)
        st.metric(
            "Total Capacity",
            f"{total_capacity:.0f} hrs"
        )
    
    with col4:
        total_billable = metrics.get("total_project_hours", 0)
        st.metric(
            "Total Billable",
            f"{total_billable:.0f} hrs"
        )
    
    # Show date range if available
    if "date_range" in metrics:
        date_range = metrics["date_range"]
        st.caption(f"📅 Period: {date_range['start'].strftime('%b %Y')} - {date_range['end'].strftime('%b %Y')}")

def render_hours_flow_section(df: pd.DataFrame, selected_person: str):
    """Render the hours flow analysis section."""
    st.subheader("Hours Flow Analysis")
    st.write("This chart shows how hours flow from scheduled capacity through to billable and non-billable work.")
    
    if selected_person and selected_person != "All coworkers":
        # Individual analysis
        person_df = render_coworker_hours_flow_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    elif selected_person == "All coworkers":
        # For "All coworkers", show the aggregated flow chart
        person_df = render_coworker_hours_flow_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    else:
        st.info("Please select a person to view hours flow analysis.")

def render_comparison_section(df: pd.DataFrame, selected_person: str):
    """Render the comparison analysis section."""
    st.subheader("Performance Comparison")
    st.write("Compare different performance metrics across time periods.")
    
    if selected_person and selected_person != "All coworkers":
        # Individual comparison analysis
        person_df = render_coworker_comparison_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    elif selected_person == "All coworkers":
        # For "All coworkers", show the team comparison analysis
        person_df = render_coworker_comparison_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    else:
        # Team comparison fallback
        render_team_comparison(df)

def render_team_comparison(df: pd.DataFrame):
    """Render team-wide comparison when 'All coworkers' is selected."""
    st.subheader("Team Performance Overview")
    
    # Get ranking of all persons
    ranking_df = get_person_performance_ranking(df, metric="billable_rate")
    
    if not ranking_df.empty:
        st.subheader("📈 Team Performance Ranking")
        
        # Display ranking table
        display_df = ranking_df.copy()
        display_df.index.name = "Rank"
        
        # Format columns
        numeric_columns = ["Capacity/Period", "Project hours", "Billable rate (%)", "Utilization (%)"]
        for col in numeric_columns:
            if col in display_df.columns:
                display_df[col] = display_df[col].round(1)
        
        st.dataframe(display_df, use_container_width=True)
        
        # Quick insights
        if len(ranking_df) > 0:
            top_performer = ranking_df.iloc[0]
            avg_rate = ranking_df["Billable rate (%)"].mean()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Top Performer", top_performer["person_name"])
                st.metric("Top Rate", f"{top_performer['Billable rate (%)']}%")
            
            with col2:
                st.metric("Team Average", f"{avg_rate:.1f}%")
                st.metric("Team Members", len(ranking_df))

def render_forecast_section(df: pd.DataFrame, selected_person: str):
    """Render the forecast analysis section."""
    st.subheader("Forecast Analysis")
    st.write("Analyze trends and forecast future performance.")
    
    if selected_person and selected_person != "All coworkers":
        # Individual forecast analysis
        person_df = render_coworker_forecast_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    elif selected_person == "All coworkers":
        # For "All coworkers", show team forecast analysis
        person_df = render_coworker_forecast_chart(df, selected_person)
        
        # Show details
        render_coworker_details_section(person_df)
        
        # Show data table
        with st.expander("📊 Detailed Data", expanded=False):
            render_coworker_data_section(person_df)
    else:
        st.info("Please select a person to view forecast analysis.")

def render_insights_section(df: pd.DataFrame, selected_person: str, full_df: pd.DataFrame):
    """Render the insights and recommendations section."""
    st.subheader("💡 Insights & Recommendations")
    
    if not selected_person or selected_person == "All coworkers":
        st.info("Select a specific person to view personalized insights.")
        
        # Show team insights
        render_team_insights(full_df)
        return
    
    # Generate insights for selected person
    insights = generate_coworker_insights(df, selected_person)
    
    if insights:
        st.subheader(f"Analysis for {selected_person}")
        
        for insight in insights:
            st.write(insight)
    
    # Performance comparison with team
    render_person_team_comparison(df, selected_person, full_df)

def render_team_insights(df: pd.DataFrame):
    """Render team-level insights."""
    st.subheader("Team Overview")
    
    # Overall team metrics
    team_summary = calculate_coworker_summary_metrics(df)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Team Performance:**")
        if team_summary:
            billable_rate = team_summary.get("overall_billable_rate", 0)
            total_members = team_summary.get("unique_persons", 0)
            
            if billable_rate >= 75:
                st.success(f"✅ Strong team performance: {billable_rate}% billable rate across {total_members} members")
            elif billable_rate >= 60:
                st.warning(f"⚠️ Moderate team performance: {billable_rate}% billable rate - room for improvement")
            else:
                st.error(f"🔴 Low team performance: {billable_rate}% billable rate - requires attention")
    
    with col2:
        st.write("**Recommendations:**")
        st.write("• Review individual performance patterns")
        st.write("• Identify training opportunities")
        st.write("• Optimize capacity allocation")
        st.write("• Monitor absence trends")

def render_person_team_comparison(person_df: pd.DataFrame, person: str, team_df: pd.DataFrame):
    """Compare person performance against team averages."""
    st.subheader(f"Team Comparison")
    
    # Calculate person metrics
    person_metrics = calculate_coworker_summary_metrics(person_df)
    person_rate = person_metrics.get("overall_billable_rate", 0)
    
    # Calculate team metrics (excluding the person and "All coworkers")
    team_only_df = team_df[
        (team_df["person_name"] != person) & 
        (team_df["person_name"] != "All coworkers")
    ]
    
    if not team_only_df.empty:
        team_metrics = calculate_coworker_summary_metrics(team_only_df)
        team_rate = team_metrics.get("overall_billable_rate", 0)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(f"{person}", f"{person_rate:.1f}%")
        
        with col2:
            st.metric("Team Average", f"{team_rate:.1f}%")
        
        with col3:
            difference = person_rate - team_rate
            st.metric(
                "vs Team",
                f"{difference:+.1f}%",
                delta=f"{difference:+.1f}%",
                delta_color="normal"
            )
        
        # Performance assessment
        if difference > 5:
            st.success(f"🌟 {person} performs above team average")
        elif difference > -5:
            st.info(f"📊 {person} performs at team average")
        else:
            st.warning(f"📈 {person} has opportunity to improve relative to team")

def render_help_section():
    """Render help and documentation section."""
    st.subheader("📚 Help & Documentation")
    
    with st.expander("Understanding Coworker Metrics", expanded=False):
        st.markdown("""
        **Key Metrics Explained:**
        
        - **Billable Rate**: Project hours as percentage of capacity
        - **Capacity**: Available working hours (schedule minus absences)
        - **Utilization**: Registered hours as percentage of capacity
        - **Hours Flow**: Shows progression from schedule → capacity → billable/non-billable
        
        **Chart Types:**
        
        - **Hours Flow**: Sankey diagram showing hour allocation
        - **Comparison**: Bar charts comparing metrics over time
        - **Forecast**: Trend analysis and performance prediction
        """)
    
    with st.expander("Data Quality & Limitations", expanded=False):
        st.markdown("""
        **Current Implementation:**
        
        - Based on Arkemy time tracking data
        - Capacity estimated from working days (8 hrs/day)
        - Absence data set to zero (enhancement opportunity)
        
        **Enhanced Features (Future):**
        
        - Actual schedule data integration
        - Comprehensive absence tracking
        - Real-time registration vs worked hours
        """)

# Helper function for navigation integration
def should_show_coworker_dashboard(transformed_df: pd.DataFrame) -> bool:
    """
    Determine if coworker dashboard should be available based on data.
    
    Args:
        transformed_df: Main Arkemy dataframe
        
    Returns:
        bool: True if coworker analysis is viable
    """
    if transformed_df is None or transformed_df.empty:
        return False
    
    # Check for required columns
    required_columns = ["record_date", "person_name", "hours_used", "hours_billable"]
    return all(col in transformed_df.columns for col in required_columns)
# charts/capacity_charts.py
import streamlit as st
import pandas as pd
from utils.capacity_processors import calculate_person_capacity, calculate_capacity_summary

def render_capacity_tab(filtered_df=None, filter_settings=None, planned_df=None):
    """
    Render the capacity analysis tab with expanded absence categories and time records.
    Now supports filtering by date range and person.
    """
    st.header("Capacity Analysis")
    
    # Check if capacity data is available
    if st.session_state.get('capacity_summary_loaded', False) and st.session_state.get('capacity_summary_df') is not None:
        capacity_df = st.session_state.capacity_summary_df.copy()
        
        # Apply filters to capacity data
        if filter_settings:
            # Apply date filter
            if 'start_date' in filter_settings and 'end_date' in filter_settings:
                start_date = filter_settings['start_date']
                end_date = filter_settings['end_date']
                mask = (capacity_df['Date'].dt.date >= start_date) & (capacity_df['Date'].dt.date <= end_date)
                capacity_df = capacity_df[mask]
            
            # Apply person filters
            if 'included_persons' in filter_settings and filter_settings['included_persons']:
                capacity_df = capacity_df[capacity_df['Person'].isin(filter_settings['included_persons'])]
            
            if 'excluded_persons' in filter_settings and filter_settings['excluded_persons']:
                capacity_df = capacity_df[~capacity_df['Person'].isin(filter_settings['excluded_persons'])]
            
            # Apply person type filter if available
            if 'selected_person_type' in filter_settings and filter_settings['selected_person_type'] != 'all':
                if 'Person type' in capacity_df.columns:
                    person_type = filter_settings['selected_person_type']
                    capacity_df = capacity_df[capacity_df['Person type'].fillna('').str.lower() == person_type]
        
        # Expand capacity data to show individual absence categories
        expanded_capacity = expand_absence_categories(capacity_df)
        
        # Get time records and merge if available (use filtered data)
        if filtered_df is not None and not filtered_df.empty:
            from utils.capacity_processors import aggregate_time_records_to_weekly
            weekly_time_records = aggregate_time_records_to_weekly(filtered_df)
            
            # Merge time records with capacity data
            final_capacity = pd.merge(
                expanded_capacity,
                weekly_time_records,
                on=['Person', 'Date'],
                how='left'
            ).fillna(0)
        else:
            final_capacity = expanded_capacity
            # Add zero columns for time records if no data
            final_capacity['hours_used'] = 0
            final_capacity['hours_billable'] = 0
        
        # Add planned hours if available
        if planned_df is not None and not planned_df.empty:
            # Aggregate planned hours by person and week
            planned_df['Date'] = pd.to_datetime(planned_df['Date'])
            planned_df['Week_Start'] = planned_df['Date'].dt.to_period('W').dt.start_time
            
            planned_weekly = planned_df.groupby(['Person', 'Week_Start']).agg({
                'Planned hours': 'sum'
            }).reset_index()
            planned_weekly = planned_weekly.rename(columns={'Week_Start': 'Date'})
            
            # Merge planned hours with capacity data
            final_capacity = pd.merge(
                final_capacity,
                planned_weekly,
                on=['Person', 'Date'],
                how='left'
            )
            final_capacity['Planned hours'] = final_capacity['Planned hours'].fillna(0)
        else:
            final_capacity['Planned hours'] = 0
        
        if not final_capacity.empty:
            # Aggregate data by week for chart
            weekly_agg = final_capacity.groupby('Date').agg({
                'Scheduled_Hours': 'sum',
                'Absence_Hours': 'sum', 
                'hours_used': 'sum',
                'hours_billable': 'sum',
                'Planned hours': 'sum'
            }).reset_index()
            
            # Calculate available capacity
            weekly_agg['Available_Capacity'] = weekly_agg['Scheduled_Hours'] - weekly_agg['Absence_Hours']
            
            # Weekly Capacity vs Actual Chart (moved to top)
            if not weekly_agg.empty:
                st.subheader("Weekly Capacity vs Actual Performance")
                
                import plotly.express as px
                import plotly.graph_objects as go
                from plotly.subplots import make_subplots
                
                # Prepare data for grouped bar chart
                fig = go.Figure()
                
                # Add bars for each metric
                fig.add_trace(go.Bar(
                    name='Scheduled Hours',
                    x=weekly_agg['Date'],
                    y=weekly_agg['Scheduled_Hours'],
                    marker_color='#1f77b4'
                ))
                
                fig.add_trace(go.Bar(
                    name='Available Capacity', 
                    x=weekly_agg['Date'],
                    y=weekly_agg['Available_Capacity'],
                    marker_color='#ff7f0e'
                ))
                
                fig.add_trace(go.Bar(
                    name='Hours Worked',
                    x=weekly_agg['Date'], 
                    y=weekly_agg['hours_used'],
                    marker_color='#2ca02c'
                ))
                
                fig.add_trace(go.Bar(
                    name='Billable Hours',
                    x=weekly_agg['Date'],
                    y=weekly_agg['hours_billable'], 
                    marker_color='#d62728'
                ))
                
                fig.add_trace(go.Bar(
                    name='Planned Hours',
                    x=weekly_agg['Date'],
                    y=weekly_agg['Planned hours'], 
                    marker_color='#9467bd'
                ))
                
                # Update layout
                fig.update_layout(
                    title='Weekly Capacity Analysis',
                    xaxis_title='Week',
                    yaxis_title='Hours',
                    barmode='group',
                    height=500,
                    showlegend=True,
                    legend=dict(
                        orientation="h",
                        yanchor="bottom",
                        y=1.02,
                        xanchor="right", 
                        x=1
                    )
                )
                
                # Format x-axis to show dates nicely
                fig.update_xaxes(tickformat='%Y-%m-%d')
                
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("No data available for weekly chart")
            
            # Display summary metrics (moved to middle)
            summary_metrics = calculate_capacity_summary(capacity_df)
            
            if summary_metrics:
                st.subheader("Summary Metrics")
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total People", summary_metrics.get("total_people", 0))
                with col2:
                    st.metric("Total Scheduled Hours", f"{summary_metrics.get('total_scheduled_hours', 0):,.0f}")
                with col3:
                    st.metric("Total Available Capacity", f"{summary_metrics.get('total_available_capacity', 0):,.0f}")
                with col4:
                    st.metric("Overall Absence Rate", f"{summary_metrics.get('overall_absence_rate', 0):.1f}%")
            
            # Weekly data table in expander (moved to bottom)
            with st.expander("Weekly Capacity Data with Time Records"):
                st.dataframe(final_capacity, use_container_width=True)
        else:
            st.warning("No capacity data available after applying filters")
    else:
        st.info("Capacity data not available. Please upload capacity data to view reports.")
        st.markdown("""
        **Required data sources:**
        - Schedule data (Person, Date, Scheduled_Hours)
        - Absence data (Person, Date, Absence_Hours)
        - Or weekly source data with capacity configuration
        """)

def expand_absence_categories(capacity_df):
    """
    Expand capacity dataframe to show individual absence categories in separate columns.
    
    Args:
        capacity_df: Capacity summary dataframe
        
    Returns:
        DataFrame with individual absence category columns
    """
    expanded_df = capacity_df.copy()
    
    # Get absence config if available
    if st.session_state.get('capacity_config'):
        absence_types = st.session_state.capacity_config.get('absence_types', {})
        
        # Get original weekly data to extract individual absence values
        if st.session_state.get('weekly_source_df') is not None:
            weekly_df = st.session_state.weekly_source_df.copy()
            
            # Prepare merge keys
            weekly_df['merge_date'] = pd.to_datetime(weekly_df['Period from']).dt.date
            expanded_df['merge_date'] = expanded_df['Date'].dt.date
            
            # Create absence columns in weekly data with proper names
            for absence_id, absence_name in absence_types.items():
                absence_col = f"Absence {absence_id} hours"
                if absence_col in weekly_df.columns:
                    weekly_df[absence_name] = weekly_df[absence_col]
            
            # Merge instead of looping
            absence_columns = list(absence_types.values())
            merge_df = pd.merge(
                expanded_df, 
                weekly_df[['Person', 'merge_date'] + absence_columns],
                on=['Person', 'merge_date'],
                how='left'
            ).fillna(0)
            
            # Clean up
            expanded_df = merge_df.drop(columns=['merge_date'])
            
            # Reorder columns to show absence categories after main capacity columns
            base_columns = ['Date', 'Person', 'Scheduled_Hours', 'Absence_Hours', 'Available_Capacity', 'Target_Billable_Hours', 'Billable_Target', 'Absence_Type']
            other_columns = [col for col in expanded_df.columns if col not in base_columns + absence_columns]
            
            # Final column order
            final_columns = []
            for col in base_columns:
                if col in expanded_df.columns:
                    final_columns.append(col)
            final_columns.extend(absence_columns)
            final_columns.extend(other_columns)
            
            expanded_df = expanded_df[final_columns]
    
    return expanded_df
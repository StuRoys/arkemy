# customer_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def render_customer_tab(filtered_df, aggregate_by_customer, render_chart, get_category_colors):
    """
    Renders the customer analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_customer: Function to aggregate data by customer
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Customer Analysis")
    
    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)
    
    # Create columns for horizontal alignment
    col1, col2 = st.columns(2)
    
    with col1:
        selected_metric = st.selectbox(
            "Select metric to visualize:",
            options=metric_options,
            index=0,  # Default to Hours worked
            key="customer_metric_selector"
        )
    
    with col2:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]
        
        visualization_type = st.radio(
            "Visualization type:",
            options=visualization_options,
            index=0,  # Default to Treemap
            key="customer_visualization_selector",
            horizontal=True
        )
    
    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"
    
    # Aggregate by customer
    customer_agg = aggregate_by_customer(filtered_df)
    
    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_customer_agg = customer_agg[customer_agg[metric_column] != 0]
    else:
        filtered_customer_agg = customer_agg[customer_agg[metric_column] > 0]
    
    # Show warning if some customers were filtered out
    if len(filtered_customer_agg) < len(customer_agg):
        excluded_count = len(customer_agg) - len(filtered_customer_agg)
        if "profit" in selected_metric.lower():
            st.warning(f"{excluded_count} customers with zero {selected_metric} were excluded from visualization.")
        else:
            st.warning(f"{excluded_count} customers with zero {selected_metric} were excluded from visualization.")
    
    # Render visualization based on type
    if not filtered_customer_agg.empty:
        if visualization_type == "Treemap":
            # Customer treemap - using filtered data with standardized custom data
            fig = px.treemap(
                filtered_customer_agg,
                path=["Customer name"],
                values=metric_column,
                color=metric_column,
                color_continuous_scale="Purples",
                custom_data=create_standardized_customdata(filtered_customer_agg),
                title=f"Customer {selected_metric} Distribution"
            )
            render_chart(fig, "customer")
        
        elif visualization_type == "Bar chart":
            # Sort customers by selected metric in descending order
            sorted_customers = customer_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of customers to display
            if len(customer_agg) > 1:
                num_customers = st.slider(
                    "Number of customers to display:",
                    min_value=1,
                    max_value=min(1000, len(customer_agg)),
                    value=min(10, len(customer_agg)),
                    step=1,
                    key="customer_count_slider"
                )
                # Limit the number of customers based on slider
                limited_customers = sorted_customers.head(num_customers)
            else:
                # If only one customer, no need for slider
                limited_customers = sorted_customers

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_customers,
                x="Customer name",
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Purples",
                title=f"{selected_metric} by Customer",
                custom_data=create_standardized_customdata(limited_customers)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart (this will apply styling from chart_styles)
            render_chart(fig_bar, "customer")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No customers have non-zero values for {selected_metric}.")
        else:
            st.error(f"No customers have values greater than zero for {selected_metric}.")


    # Display customer data table with all metrics in an expander
    with st.expander("Details"):
        # Sort by hours worked in descending order
        sorted_customer_agg = customer_agg.sort_values("hours_used", ascending=False)

        # Reorder columns for better presentation - include new cost/profit columns if they exist
        base_columns = ['Customer number', 'Customer name', 'Number of projects',
                       'hours_used', 'hours_billable', 'Non-billable hours', 'Billability %']

        financial_columns = []
        if 'Fee' in sorted_customer_agg.columns:
            financial_columns.append('Fee')
        if 'Total cost' in sorted_customer_agg.columns:
            financial_columns.append('Total cost')
        if 'Total profit' in sorted_customer_agg.columns:
            financial_columns.append('Total profit')
        if 'Profit margin %' in sorted_customer_agg.columns:
            financial_columns.append('Profit margin %')

        rate_columns = []
        if 'Billable rate' in sorted_customer_agg.columns:
            rate_columns.append('Billable rate')
        if 'Effective rate' in sorted_customer_agg.columns:
            rate_columns.append('Effective rate')

        # Combine all columns that exist
        display_columns = base_columns + financial_columns + rate_columns
        existing_columns = [col for col in display_columns if col in sorted_customer_agg.columns]

        sorted_customer_agg = sorted_customer_agg[existing_columns]

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_customer_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_customer_agg)
        )
# price_model_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def render_price_model_tab(filtered_df, aggregate_by_price_model, render_chart, get_category_colors):
    """
    Renders the price model analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_price_model: Function to aggregate data by price model
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    
    # Check if Price model column exists
    if "price_model_type" in filtered_df.columns:
        # Get metric options from centralized function
        metric_options = get_metric_options(has_planned_data=False)
        
        # Create columns for horizontal alignment
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metric = st.selectbox(
                "Select metric to visualize:",
                options=metric_options,
                index=0,  # Default to Hours worked
                key="price_model_metric_selector"
            )
        
        with col2:
            # Add visualization type selection
            visualization_options = ["Treemap", "Bar chart"]
            
            visualization_type = st.radio(
                "Visualization type:",
                options=visualization_options,
                index=0,  # Default to Treemap
                key="price_model_visualization_selector",
                horizontal=True
            )
        
        # Translate display names to column names if needed
        metric_column = selected_metric
        if selected_metric == "Hours worked":
            metric_column = "hours_used"
        elif selected_metric == "Billable hours":
            metric_column = "hours_billable"
        
        # Aggregate by price model
        price_model_agg = aggregate_by_price_model(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_price_model_agg = price_model_agg[price_model_agg[metric_column] != 0]
        else:
            filtered_price_model_agg = price_model_agg[price_model_agg[metric_column] > 0]
        
        # Show warning if some price models were filtered out
        if len(filtered_price_model_agg) < len(price_model_agg):
            excluded_count = len(price_model_agg) - len(filtered_price_model_agg)
            if "profit" in selected_metric.lower():
                st.warning(f"{excluded_count} price models with zero {selected_metric} were excluded from visualization.")
            else:
                st.warning(f"{excluded_count} price models with zero {selected_metric} were excluded from visualization.")
        
        # Render visualization based on type
        if not filtered_price_model_agg.empty:
            if visualization_type == "Treemap":
                # Price model treemap - using filtered data with standardized custom data
                fig = px.treemap(
                    filtered_price_model_agg,
                    path=["price_model_type"],
                    values=metric_column,
                    color=metric_column,
                    color_continuous_scale="YlOrRd",  # Different color scheme than Phase
                    custom_data=create_standardized_customdata(filtered_price_model_agg),
                    title=f"Price Model {selected_metric} Distribution"
                )
                render_chart(fig, "price_model")
            
            elif visualization_type == "Bar chart":
                # Sort price models by selected metric in descending order
                sorted_models = price_model_agg.sort_values(metric_column, ascending=False)

                # Add a slider to control number of price models to display
                if len(price_model_agg) > 1:
                    num_models = st.slider(
                        "Number of price models to display:",
                        min_value=1,
                        max_value=min(1000, len(price_model_agg)),
                        value=min(10, len(price_model_agg)),
                        step=1,
                        key="price_model_count_slider"
                    )
                    # Limit the number of price models based on slider
                    limited_models = sorted_models.head(num_models)
                else:
                    # If only one price model, no need for slider
                    limited_models = sorted_models

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_models,
                    x="price_model_type",
                    y=metric_column,
                    color=metric_column,
                    color_continuous_scale="YlOrRd",  # Different color scheme than Phase
                    title=f"{selected_metric} by Price Model",
                    custom_data=create_standardized_customdata(limited_models)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "price_model")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No price models have non-zero values for {selected_metric}.")
            else:
                st.error(f"No price models have values greater than zero for {selected_metric}.")
        

        # Display price model data table with all metrics
        st.subheader("Price Model Data Table")
        
        # Sort by hours worked in descending order
        sorted_price_model_agg = price_model_agg.sort_values("hours_used", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_price_model_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_price_model_agg)
        )
    else:
        st.warning("Price model information is not available in the data.")
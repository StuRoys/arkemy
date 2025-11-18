# price_model_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
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
                # Build hierarchical structure for go.Treemap
                ids = ["root"]
                labels = ["All Price Models"]
                parents = [""]
                values_list = [0]  # Will be summed from children
                customdata_list = [[0] * 19]  # Root customdata placeholder

                # Add all price models as children of root
                root_total = 0
                for idx, row in filtered_price_model_agg.iterrows():
                    price_model_type = str(row["price_model_type"])
                    ids.append(f"model_{price_model_type}")
                    labels.append(price_model_type)
                    parents.append("root")
                    val = row[metric_column]
                    values_list.append(val)
                    root_total += val

                # Set root value to sum of children
                values_list[0] = root_total if root_total > 0 else 1

                # Build customdata for all items
                customdata_for_root = [0] * 19
                customdata_list = [customdata_for_root]

                # Add customdata for each price model
                custom_data_arrays = create_standardized_customdata(filtered_price_model_agg)
                for i in range(len(filtered_price_model_agg)):
                    row_customdata = [arr[i] if i < len(arr) else 0 for arr in custom_data_arrays]
                    customdata_list.append(row_customdata)

                # Create color array using Plotly's color scale
                min_val = filtered_price_model_agg[metric_column].min()
                max_val = filtered_price_model_agg[metric_column].max()

                # Normalize values for color mapping (clamp to [0, 1])
                if max_val > min_val:
                    normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
                else:
                    normalized = [0.5] * len(values_list)

                # Get YlOrRd color scale
                colors_scale = pc.sample_colorscale("YlOrRd", normalized)

                # Create treemap using graph_objects
                fig = go.Figure(data=[go.Treemap(
                    ids=ids,
                    labels=labels,
                    parents=parents,
                    values=values_list,
                    customdata=customdata_list,
                    marker=dict(
                        colors=colors_scale,
                        line=dict(width=2, color="white")
                    ),
                    textposition="middle center",
                    branchvalues="total"
                )])

                fig.update_layout(
                    title=f"Price Model {selected_metric} Distribution",
                    height=420,
                    margin=dict(l=20, r=20, t=40, b=20)
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


        # Display price model data table with all metrics in an expander
        with st.expander("Details"):
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
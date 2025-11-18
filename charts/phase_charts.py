# phase_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options, create_treemap_hovertemplate

def render_phase_tab(filtered_df, aggregate_by_phase, render_chart, get_category_colors):
    """
    Renders the phase analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_phase: Function to aggregate data by phase
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Phase Analysis")
    
    # Check if Phase column exists
    if "phase_tag" in filtered_df.columns:
        # Get metric options from centralized function
        metric_options = get_metric_options(has_planned_data=False)
        
        # Create columns for horizontal alignment
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metric = st.selectbox(
                "Select metric to visualize:",
                options=metric_options,
                index=0,  # Default to Hours worked
                key="phase_metric_selector"
            )
        
        with col2:
            # Add visualization type selection
            visualization_options = ["Treemap", "Bar chart"]
            
            visualization_type = st.radio(
                "Visualization type:",
                options=visualization_options,
                index=0,  # Default to Treemap
                key="phase_visualization_selector",
                horizontal=True
            )
        
        # Translate display names to column names if needed
        metric_column = selected_metric
        if selected_metric == "Hours worked":
            metric_column = "hours_used"
        elif selected_metric == "Billable hours":
            metric_column = "hours_billable"
        
        # Aggregate by phase
        phase_agg = aggregate_by_phase(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_phase_agg = phase_agg[phase_agg[metric_column] != 0]
        else:
            filtered_phase_agg = phase_agg[phase_agg[metric_column] > 0]
        
        # Show warning if some phases were filtered out
        if len(filtered_phase_agg) < len(phase_agg):
            excluded_count = len(phase_agg) - len(filtered_phase_agg)
            if "profit" in selected_metric.lower():
                st.warning(f"{excluded_count} phases with zero {selected_metric} were excluded from visualization.")
            else:
                st.warning(f"{excluded_count} phases with zero {selected_metric} were excluded from visualization.")
        
        # Render visualization based on type
        if not filtered_phase_agg.empty:
            if visualization_type == "Treemap":
                # Build hierarchical structure for go.Treemap
                ids = ["root"]
                labels = ["All Phases"]
                parents = [""]
                values_list = [0]  # Will be summed from children
                customdata_list = [[0] * 19]  # Root customdata placeholder

                # Add all phases as children of root
                for idx, row in filtered_phase_agg.iterrows():
                    phase_tag = str(row["phase_tag"])
                    ids.append(f"phase_{phase_tag}")
                    labels.append(phase_tag)
                    parents.append("root")
                    values_list.append(row[metric_column])

                # Build customdata for all items
                customdata_for_root = [0] * 19
                customdata_list = [customdata_for_root]

                # Add customdata for each phase
                custom_data_arrays = create_standardized_customdata(filtered_phase_agg)
                for i in range(len(filtered_phase_agg)):
                    row_customdata = [arr[i] if i < len(arr) else 0 for arr in custom_data_arrays]
                    customdata_list.append(row_customdata)

                # Create color array using Plotly's color scale
                min_val = filtered_phase_agg[metric_column].min()
                max_val = filtered_phase_agg[metric_column].max()

                # Normalize values for color mapping (clamp to [0, 1])
                if max_val > min_val:
                    normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
                else:
                    normalized = [0.5] * len(values_list)

                # Get Purples color scale
                colors_scale = pc.sample_colorscale("Purples", normalized)

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
                    hovertemplate=create_treemap_hovertemplate("phase"),
                    branchvalues="total"
                )])

                fig.update_layout(
                    title=f"Phase {selected_metric} Distribution",
                    height=420,
                    margin=dict(l=20, r=20, t=40, b=20)
                )

                render_chart(fig, "phase")
            
            elif visualization_type == "Bar chart":
                # Sort phases by selected metric in descending order
                sorted_phases = phase_agg.sort_values(metric_column, ascending=False)

                # Add a slider to control number of phases to display
                if len(phase_agg) > 1:
                    num_phases = st.slider(
                        "Number of phases to display:",
                        min_value=1,
                        max_value=min(1000, len(phase_agg)),
                        value=min(10, len(phase_agg)),
                        step=1,
                        key="phase_count_slider"
                    )
                    # Limit the number of phases based on slider
                    limited_phases = sorted_phases.head(num_phases)
                else:
                    # If only one phase, no need for slider
                    limited_phases = sorted_phases

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_phases,
                    x="phase_tag",
                    y=metric_column,
                    color=metric_column,
                    color_continuous_scale="Purples",
                    title=f"{selected_metric} by Phase",
                    custom_data=create_standardized_customdata(limited_phases)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "phase")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No phases have non-zero values for {selected_metric}.")
            else:
                st.error(f"No phases have values greater than zero for {selected_metric}.")


        # Display phase data table with all metrics in an expander
        with st.expander("Details"):
            # Sort by hours worked in descending order
            sorted_phase_agg = phase_agg.sort_values("hours_used", ascending=False)

            # Use the column configuration from chart_styles
            from utils.chart_styles import create_column_config

            # Display the table with column configurations
            st.dataframe(
                sorted_phase_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_phase_agg)
            )
    else:
        st.warning("Phase information is not available in the data.")
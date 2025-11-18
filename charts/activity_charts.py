# activity_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def render_activity_tab(filtered_df, aggregate_by_activity, render_chart, get_category_colors):
    """
    Renders the activity analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_activity: Function to aggregate data by activity
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Activity Analysis")
    
    # Check if Activity column exists
    if "activity_tag" in filtered_df.columns:
        # Get metric options from centralized function
        metric_options = get_metric_options(has_planned_data=False)
        
        # Create columns for horizontal alignment
        col1, col2 = st.columns(2)
        
        with col1:
            selected_metric = st.selectbox(
                "Select metric to visualize:",
                options=metric_options,
                index=0,  # Default to Hours worked
                key="activity_metric_selector"
            )
        
        with col2:
            # Add visualization type selection
            visualization_options = ["Treemap", "Bar chart"]
            
            visualization_type = st.radio(
                "Visualization type:",
                options=visualization_options,
                index=0,  # Default to Treemap
                key="activity_visualization_selector",
                horizontal=True
            )
        
        # Translate display names to column names if needed
        metric_column = selected_metric
        if selected_metric == "Hours worked":
            metric_column = "hours_used"
        elif selected_metric == "Billable hours":
            metric_column = "hours_billable"
        
        # Aggregate by activity
        activity_agg = aggregate_by_activity(filtered_df)
        
        # Filter based on selected metric - special handling for profit which can be negative
        if "profit" in selected_metric.lower():
            filtered_activity_agg = activity_agg[activity_agg[metric_column] != 0]
        else:
            filtered_activity_agg = activity_agg[activity_agg[metric_column] > 0]
        
        # Show warning if some activities were filtered out
        if len(filtered_activity_agg) < len(activity_agg):
            excluded_count = len(activity_agg) - len(filtered_activity_agg)
            if "profit" in selected_metric.lower():
                st.warning(f"{excluded_count} activities with zero {selected_metric} were excluded from visualization.")
            else:
                st.warning(f"{excluded_count} activities with zero {selected_metric} were excluded from visualization.")
        
        # Render visualization based on type
        if not filtered_activity_agg.empty:
            if visualization_type == "Treemap":
                # Build hierarchical structure for go.Treemap
                ids = ["root"]
                labels = ["All Activities"]
                parents = [""]
                values_list = [0]  # Will be summed from children
                customdata_list = [[0] * 19]  # Root customdata placeholder

                # Add all activities as children of root
                root_total = 0
                for idx, row in filtered_activity_agg.iterrows():
                    activity_tag = str(row["activity_tag"])
                    ids.append(f"activity_{activity_tag}")
                    labels.append(activity_tag)
                    parents.append("root")
                    val = row[metric_column]
                    values_list.append(val)
                    root_total += val

                # Set root value to sum of children
                values_list[0] = root_total if root_total > 0 else 1

                # Build customdata for all items
                customdata_for_root = [0] * 19
                customdata_list = [customdata_for_root]

                # Add customdata for each activity
                custom_data_arrays = create_standardized_customdata(filtered_activity_agg)
                for i in range(len(filtered_activity_agg)):
                    row_customdata = [arr.iloc[i] if i < len(arr) else 0 for arr in custom_data_arrays]
                    customdata_list.append(row_customdata)

                # Create color array using Plotly's color scale
                min_val = filtered_activity_agg[metric_column].min()
                max_val = filtered_activity_agg[metric_column].max()

                # Normalize values for color mapping (clamp to [0, 1])
                if max_val > min_val:
                    normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
                else:
                    normalized = [0.5] * len(values_list)

                # Get Reds color scale
                colors_scale = pc.sample_colorscale("Reds", normalized)

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
                    title=f"Activity {selected_metric} Distribution",
                    height=420,
                    margin=dict(l=20, r=20, t=40, b=20)
                )

                render_chart(fig, "activity")
            
            elif visualization_type == "Bar chart":
                # Sort activities by selected metric in descending order
                sorted_activities = activity_agg.sort_values(metric_column, ascending=False)

                # Add a slider to control number of activities to display
                if len(activity_agg) > 1:
                    num_activities = st.slider(
                        "Number of activities to display:",
                        min_value=1,
                        max_value=min(1000, len(activity_agg)),
                        value=min(10, len(activity_agg)),
                        step=1,
                        key="activity_count_slider"
                    )
                    # Limit the number of activities based on slider
                    limited_activities = sorted_activities.head(num_activities)
                else:
                    # If only one activity, no need for slider
                    limited_activities = sorted_activities

                # Create the bar chart with standardized custom data
                fig_bar = px.bar(
                    limited_activities,
                    x="activity_tag",
                    y=metric_column,
                    color=metric_column,
                    color_continuous_scale="Reds",
                    title=f"{selected_metric} by Activity",
                    custom_data=create_standardized_customdata(limited_activities)
                )

                # Improve layout for better readability
                fig_bar.update_layout(
                    xaxis_title="",
                    yaxis_title=selected_metric,
                    xaxis={'categoryorder':'total descending'}
                )

                # Render the chart (this will apply styling from chart_styles)
                render_chart(fig_bar, "activity")
        else:
            if "profit" in selected_metric.lower():
                st.error(f"No activities have non-zero values for {selected_metric}.")
            else:
                st.error(f"No activities have values greater than zero for {selected_metric}.")

        # Display activity data table with all metrics in an expander
        with st.expander("Details"):
            # Sort by hours worked in descending order
            sorted_activity_agg = activity_agg.sort_values("hours_used", ascending=False)

            # Use the column configuration from chart_styles
            from utils.chart_styles import create_column_config

            # Display the table with column configurations
            st.dataframe(
                sorted_activity_agg,
                use_container_width=True,
                hide_index=True,
                column_config=create_column_config(sorted_activity_agg)
            )
    else:
        st.warning("Activity information is not available in the data.")
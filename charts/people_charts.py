# people_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def render_people_tab(filtered_df, aggregate_by_person, render_chart, get_category_colors):
    """
    Renders the people analysis tab with visualizations and metrics.
    
    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_person: Function to aggregate data by person
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("People Analysis")
    
    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)
    
    # Create columns for horizontal alignment
    col1, col2 = st.columns(2)
    
    with col1:
        selected_metric = st.selectbox(
            "Select metric to visualize:",
            options=metric_options,
            index=0,  # Default to Hours worked
            key="people_metric_selector"
        )
    
    with col2:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]
        
        visualization_type = st.radio(
            "Visualization type:",
            options=visualization_options,
            index=0,  # Default to Treemap
            key="people_visualization_selector",
            horizontal=True
        )
    
    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"
    
    # Aggregate by person
    person_agg = aggregate_by_person(filtered_df)
    
    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_person_agg = person_agg[person_agg[metric_column] != 0]
    else:
        filtered_person_agg = person_agg[person_agg[metric_column] > 0]
    
    # Show warning if some people were filtered out
    if len(filtered_person_agg) < len(person_agg):
        excluded_count = len(person_agg) - len(filtered_person_agg)
        if "profit" in selected_metric.lower():
            st.warning(f"{excluded_count} people with zero {selected_metric} were excluded from visualization.")
        else:
            st.warning(f"{excluded_count} people with zero {selected_metric} were excluded from visualization.")
    
    # Render visualization based on type
    if not filtered_person_agg.empty:
        if visualization_type == "Treemap":
            # Build hierarchical structure for go.Treemap
            ids = ["root"]
            labels = ["All People"]
            parents = [""]
            values_list = [0]  # Will be summed from children
            customdata_list = [[0] * 19]  # Root customdata placeholder

            # Add all people as children of root
            root_total = 0
            for idx, row in filtered_person_agg.iterrows():
                person_name = str(row["person_name"])
                ids.append(f"person_{person_name}")
                labels.append(person_name)
                parents.append("root")
                val = row[metric_column]
                values_list.append(val)
                root_total += val

            # Set root value to sum of children
            values_list[0] = root_total if root_total > 0 else 1

            # Build customdata for all items
            customdata_for_root = [0] * 19
            customdata_list = [customdata_for_root]

            # Add customdata for each person
            custom_data_arrays = create_standardized_customdata(filtered_person_agg)
            for i in range(len(filtered_person_agg)):
                row_customdata = []
                for arr in custom_data_arrays:
                    if i < len(arr):
                        val = arr.iloc[i] if isinstance(arr, pd.Series) else arr[i]
                        row_customdata.append(val)
                    else:
                        row_customdata.append(0)
                customdata_list.append(row_customdata)

            # Create color array using Plotly's color scale
            min_val = filtered_person_agg[metric_column].min()
            max_val = filtered_person_agg[metric_column].max()

            # Normalize values for color mapping (clamp to [0, 1])
            if max_val > min_val:
                normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
            else:
                normalized = [0.5] * len(values_list)

            # Get Blues color scale
            colors_scale = pc.sample_colorscale("Blues", normalized)

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
                title=f"People {selected_metric} Distribution",
                height=420,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            render_chart(fig, "person")
        
        elif visualization_type == "Bar chart":
            # Sort people by selected metric in descending order
            sorted_people = person_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of people to display
            if len(person_agg) > 1:
                num_people = st.slider(
                    "Number of people to display:",
                    min_value=1,
                    max_value=min(1000, len(person_agg)),
                    value=min(10, len(person_agg)),
                    step=1,
                    key="people_count_slider"
                )
                # Limit the number of people based on slider
                limited_people = sorted_people.head(num_people)
            else:
                # If only one person, no need for slider
                limited_people = sorted_people

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_people,
                x="person_name",
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Blues",
                title=f"{selected_metric} by Person",
                custom_data=create_standardized_customdata(limited_people)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart (this will apply styling from chart_styles)
            render_chart(fig_bar, "person")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No people have non-zero values for {selected_metric}.")
        else:
            st.error(f"No people have values greater than zero for {selected_metric}.")


    # Display people data table with all metrics in an expander
    with st.expander("Details"):
        # Sort by hours worked in descending order
        sorted_person_agg = person_agg.sort_values("hours_used", ascending=False)

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            sorted_person_agg,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(sorted_person_agg)
        )
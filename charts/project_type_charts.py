# project_type_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options
from utils.processors import get_project_tag_columns, aggregate_by_project_tag, get_project_tag_columns_with_labels
from utils.tag_manager import get_tag_display_name

def get_widget_key(base_key: str, nav_context: str = "project_types") -> str:
    """Generate stable widget keys for project type charts"""
    # Use static keys to preserve widget state across reruns
    return f"{nav_context}_{base_key}"

def render_project_type_tab(filtered_df, aggregate_by_project_type, render_chart, get_category_colors):
    """
    Renders the project type analysis tab with visualizations and metrics.

    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_project_type: Function to aggregate data by project type (deprecated, kept for compatibility)
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Get available project tag columns
    available_tags = get_project_tag_columns(filtered_df)

    if not available_tags:
        st.warning("Project tag information is not available in the data.")
        return

    # Get tag mappings from session state (populated by unified_data_loader)
    tag_mappings = st.session_state.get('tag_mappings', {})

    # Get available project tags with labels
    tag_columns_with_labels = get_project_tag_columns_with_labels(filtered_df, tag_mappings)

    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)

    # Create columns for horizontal alignment (3 columns)
    col1, col2, col3 = st.columns(3)

    with col1:
        # Tag dimension selector - only show if multiple tags exist
        if len(available_tags) > 1:
            # Use column names as values, but display labels to user via format_func
            selected_tag_column = st.selectbox(
                label="",
                options=available_tags,
                format_func=lambda col: tag_columns_with_labels.get(col, col),
                index=0,
                key=get_widget_key("tag_selector")
            )
        else:
            # Only one tag available, use it automatically
            selected_tag_column = available_tags[0]

    with col2:
        selected_metric = st.selectbox(
            label="",
            options=metric_options,
            index=0,  # Default to Hours worked
            key=get_widget_key("metric_selector")
        )

    with col3:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]

        visualization_type = st.selectbox(
            label="",
            options=visualization_options,
            index=0,  # Default to Treemap
            key=get_widget_key("visualization_selector")
        )

    # Get display label for selected tag column
    selected_tag_display_name = get_tag_display_name(selected_tag_column, tag_mappings)

    # Aggregate by selected project tag - this will be used for all visualizations
    project_type_agg = aggregate_by_project_tag(filtered_df, tag_column=selected_tag_column)

    # Add percentage columns for sum metrics (for treemap display)
    from utils.chart_styles import SUM_METRICS
    from utils.processors import add_percentage_columns
    project_type_agg = add_percentage_columns(project_type_agg, SUM_METRICS)

    # Check if we have any data after aggregation
    if project_type_agg.empty:
        st.error("No project type data available after filtering.")
        return

    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"
    
    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_project_type_agg = project_type_agg[project_type_agg[metric_column] != 0]
    else:
        filtered_project_type_agg = project_type_agg[project_type_agg[metric_column] > 0]
    
    # Show warning if some project types were filtered out
    if len(filtered_project_type_agg) < len(project_type_agg):
        excluded_count = len(project_type_agg) - len(filtered_project_type_agg)
        if "profit" in selected_metric.lower():
            st.warning(f"{excluded_count} project types with zero {selected_metric} were excluded from visualization.")
        else:
            st.warning(f"{excluded_count} project types with zero {selected_metric} were excluded from visualization.")
    
    # Render visualization based on type
    if not filtered_project_type_agg.empty:
        if visualization_type == "Treemap":
            # Build hierarchical structure for go.Treemap
            ids = [f"root"]
            labels = [f"All {selected_tag_display_name}"]
            parents = [""]
            values_list = [0]  # Will be summed from children
            customdata_list = [[0] * 19]  # Root customdata placeholder

            # Add all project tags as children of root
            root_total = 0
            for idx, row in filtered_project_type_agg.iterrows():
                tag_value = str(row[selected_tag_column])
                ids.append(f"tag_{tag_value}")
                labels.append(tag_value)
                parents.append("root")
                val = row[metric_column]
                values_list.append(val)
                root_total += val

            # Set root value to sum of children
            values_list[0] = root_total if root_total > 0 else 1

            # Build customdata for all items (root + tags)
            customdata_for_root = [0] * 20
            customdata_list = [customdata_for_root]

            # Add customdata for each tag
            custom_data_arrays = create_standardized_customdata(filtered_project_type_agg)
            for i in range(len(filtered_project_type_agg)):
                row_customdata = []
                for arr in custom_data_arrays:
                    if i < len(arr):
                        val = arr.iloc[i] if isinstance(arr, pd.Series) else arr[i]
                        row_customdata.append(val)
                    else:
                        row_customdata.append(0)
                customdata_list.append(row_customdata)

            # Create color array using Plotly's color scale
            import plotly.colors as pc
            min_val = filtered_project_type_agg[metric_column].min()
            max_val = filtered_project_type_agg[metric_column].max()

            # Normalize values for color mapping (clamp to [0, 1])
            if max_val > min_val:
                normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
            else:
                normalized = [0.5] * len(values_list)

            # Get Greens color scale
            colors_scale = pc.sample_colorscale("Greens", normalized)

            # Build text template based on whether percentage exists
            from utils.chart_helpers import build_treemap_texttemplate
            pct_column = f'{metric_column}_pct'
            has_percentage = pct_column in filtered_project_type_agg.columns
            texttemplate = build_treemap_texttemplate(metric_column, has_percentage)

            # Create treemap using graph_objects
            fig = go.Figure(data=[go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values_list,
                customdata=customdata_list,
                texttemplate=texttemplate,  # Show percentages on tiles for sum metrics
                marker=dict(
                    colors=colors_scale,
                    line=dict(width=2, color="white")
                ),
                textposition="middle center",
                branchvalues="total"
            )])

            fig.update_layout(
                title=f"{selected_tag_display_name} {selected_metric} Distribution",
                height=420,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            render_chart(fig, "project_type")

        elif visualization_type == "Bar chart":
            # Sort project types by selected metric in descending order
            sorted_project_types = project_type_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of project types to display (only if 10+ items)
            if len(project_type_agg) >= 10:
                num_project_types = st.slider(
                    label="",
                    min_value=1,
                    max_value=min(1000, len(project_type_agg)),
                    value=min(10, len(project_type_agg)),
                    step=1,
                    key=get_widget_key("count_slider")
                )
                # Limit the number of project types based on slider
                limited_project_types = sorted_project_types.head(num_project_types)
            else:
                # If fewer than 10 items, show all
                limited_project_types = sorted_project_types

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_project_types,
                x=selected_tag_column,
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Greens",
                title=f"{selected_metric} by {selected_tag_display_name}",
                custom_data=create_standardized_customdata(limited_project_types)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart
            render_chart(fig_bar, "project_type")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No project types have non-zero values for {selected_metric}.")
        else:
            st.error(f"No project types have values greater than zero for {selected_metric}.")

    # Display project type data table with all metrics in an expander
    with st.expander("Details"):
        # Sort by hours worked in descending order
        sorted_project_type_agg = project_type_agg.sort_values("hours_used", ascending=False)

        # Rename the selected tag column to show its display name
        display_df = sorted_project_type_agg.copy()
        display_df = display_df.rename(columns={selected_tag_column: selected_tag_display_name})

        # Use the column configuration from chart_styles
        from utils.chart_styles import create_column_config

        # Display the table with column configurations
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(display_df)
        )
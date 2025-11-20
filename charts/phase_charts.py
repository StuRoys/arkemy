# phase_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.colors as pc
from utils.chart_helpers import create_standardized_customdata, build_treemap_texttemplate
from utils.chart_styles import get_metric_options, initialize_analytics_metric_state, SUM_METRICS, create_column_config
from utils.processors import get_all_tag_columns, aggregate_by_project_tag, get_project_tag_columns_with_labels, add_percentage_columns
from utils.tag_manager import get_tag_display_name

def get_phase_tag_columns(df: pd.DataFrame) -> list:
    """
    Get only phase_tag* and phase_tag* columns from all tag columns.

    Args:
        df: DataFrame to search

    Returns:
        List of phase tag columns only
        Example: ['phase_tag', 'phase_tag_1', 'phase_tag_2', 'phase_tag_3']
    """
    all_tags = get_all_tag_columns(df)
    return [col for col in all_tags if col.startswith('phase_tag')]

def get_widget_key(base_key: str, nav_context: str = "phases") -> str:
    """Generate stable widget keys for phase charts"""
    # Use static keys to preserve widget state across reruns
    return f"{nav_context}_{base_key}"

def render_phase_tab(filtered_df, aggregate_by_phase, render_chart, get_category_colors):
    """
    Renders the phase analysis tab with visualizations and metrics.

    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_phase: Function to aggregate data by phase (deprecated, kept for compatibility)
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    # Get available phase tag columns
    available_tags = get_phase_tag_columns(filtered_df)

    # Filter out columns that are completely empty (all null/NaN or empty strings)
    available_tags = [
        col for col in available_tags
        if filtered_df[col].notna().any() and
           (filtered_df[col].astype(str).str.strip() != '').any()
    ]

    if not available_tags:
        st.warning("Phase tag information is not available in the data.")
        return

    # Get tag mappings from session state (populated by unified_data_loader)
    tag_mappings = st.session_state.get('tag_mappings', {})

    # Get available phase tags with labels
    tag_columns_with_labels = get_project_tag_columns_with_labels(filtered_df, tag_mappings)

    # Initialize shared metric state (persists across tabs)
    initialize_analytics_metric_state()

    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)

    # Get current index from session state (with fallback if metric not in options)
    try:
        current_metric_index = metric_options.index(st.session_state.analytics_selected_metric)
    except ValueError:
        current_metric_index = 0  # Fallback to first option if current selection not available

    # Create columns for horizontal alignment (3 columns)
    col1, col2, col3 = st.columns(3)

    with col1:
        # Tag dimension selector - only show if multiple tags exist
        if len(available_tags) > 1:
            # Use column names as values, but display labels to user via format_func
            selected_tag_column = st.selectbox(
                label="Tag dimension",
                label_visibility="collapsed",
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
            label="Metric",
            label_visibility="collapsed",
            options=metric_options,
            index=current_metric_index,
            key=get_widget_key("metric_selector")
        )
        st.session_state.analytics_selected_metric = selected_metric

    with col3:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]

        visualization_type = st.selectbox(
            label="Chart type",
            label_visibility="collapsed",
            options=visualization_options,
            index=0,  # Default to Treemap
            key=get_widget_key("visualization_selector")
        )

    # Get display label for selected tag column
    selected_tag_display_name = get_tag_display_name(selected_tag_column, tag_mappings)

    # Aggregate by selected phase tag - this will be used for all visualizations
    phase_agg = aggregate_by_project_tag(filtered_df, tag_column=selected_tag_column)

    # Add percentage columns for sum metrics (for treemap display)
    phase_agg = add_percentage_columns(phase_agg, SUM_METRICS)

    # Check if we have any data after aggregation
    if phase_agg.empty:
        st.error("No phase data available after filtering.")
        return

    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"

    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_phase_agg = phase_agg[phase_agg[metric_column] != 0]
    else:
        filtered_phase_agg = phase_agg[phase_agg[metric_column] > 0]

    # Render visualization based on type
    if not filtered_phase_agg.empty:
        if visualization_type == "Treemap":
            # Build hierarchical structure for go.Treemap
            ids = [f"root"]
            labels = [f"All {selected_tag_display_name}"]
            parents = [""]
            values_list = [0]  # Will be summed from children
            customdata_list = [[0] * 19]  # Root customdata placeholder

            # Add all phase tags as children of root
            root_total = 0
            for _, row in filtered_phase_agg.iterrows():
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
            custom_data_arrays = create_standardized_customdata(filtered_phase_agg)
            for i in range(len(filtered_phase_agg)):
                row_customdata = []
                for arr in custom_data_arrays:
                    if i < len(arr):
                        val = arr.iloc[i] if isinstance(arr, pd.Series) else arr[i]
                        row_customdata.append(val)
                    else:
                        row_customdata.append(0)
                customdata_list.append(row_customdata)

            # Add percentage values if they exist (index [19])
            pct_column = f'{metric_column}_pct'
            if pct_column in filtered_phase_agg.columns:
                for i, pct_val in enumerate(filtered_phase_agg[pct_column], 1):  # Start from 1 to skip root
                    if i < len(customdata_list):
                        customdata_list[i][19] = pct_val

            # Create color array using Plotly's color scale
            min_val = filtered_phase_agg[metric_column].min()
            max_val = filtered_phase_agg[metric_column].max()

            # Normalize values for color mapping (clamp to [0, 1])
            if max_val > min_val:
                normalized = [max(0, min(1, (v - min_val) / (max_val - min_val))) for v in values_list]
            else:
                normalized = [0.5] * len(values_list)

            # Get Reds color scale for phases
            colors_scale = pc.sample_colorscale("Reds", normalized)

            # Build text template based on whether percentage exists
            pct_column = f'{metric_column}_pct'
            has_percentage = pct_column in filtered_phase_agg.columns
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
                title="",
                height=420,
                margin=dict(l=20, r=20, t=40, b=20)
            )

            render_chart(fig, "phase")

        elif visualization_type == "Bar chart":
            # Sort phases by selected metric in descending order
            sorted_phases = phase_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of phases to display (only if 10+ items)
            if len(phase_agg) >= 10:
                num_phases = st.slider(
                    label="",
                    min_value=1,
                    max_value=min(1000, len(phase_agg)),
                    value=min(10, len(phase_agg)),
                    step=1,
                    key=get_widget_key("count_slider")
                )
                # Limit the number of phases based on slider
                limited_phases = sorted_phases.head(num_phases)
            else:
                # If fewer than 10 items, show all
                limited_phases = sorted_phases

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_phases,
                x=selected_tag_column,
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Reds",
                title="",
                custom_data=create_standardized_customdata(limited_phases)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart
            render_chart(fig_bar, "phase")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No phases have non-zero values for {selected_metric}.")
        else:
            st.error(f"No phases have values greater than zero for {selected_metric}.")

    # Display activity data table with all metrics in an expander
    with st.expander("Details"):
        # Sort by hours worked in descending order
        sorted_phase_agg = phase_agg.sort_values("hours_used", ascending=False)

        # Rename the selected tag column to show its display name
        display_df = sorted_phase_agg.copy()
        display_df = display_df.rename(columns={selected_tag_column: selected_tag_display_name})

        # Display the table with column configurations
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config=create_column_config(display_df)
        )

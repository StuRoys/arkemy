# customer_group_charts.py
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.chart_helpers import create_standardized_customdata
from utils.chart_styles import get_metric_options

def render_customer_group_tab(filtered_df, aggregate_by_customer_group, render_chart, get_category_colors):
    """
    Renders the customer group analysis tab with visualizations and metrics.

    Args:
        filtered_df: DataFrame with filtered time record data
        aggregate_by_customer_group: Function to aggregate data by customer group
        render_chart: Function to render charts with consistent styling
        get_category_colors: Function to get consistent color schemes
    """
    #st.subheader("Customer Group Analysis")

    # Get metric options from centralized function
    metric_options = get_metric_options(has_planned_data=False)

    # Create columns for horizontal alignment
    col1, col2 = st.columns(2)

    with col1:
        selected_metric = st.selectbox(
            "Select metric to visualize:",
            options=metric_options,
            index=0,  # Default to Hours worked
            key="customer_group_metric_selector"
        )

    with col2:
        # Add visualization type selection
        visualization_options = ["Treemap", "Bar chart"]

        visualization_type = st.radio(
            "Visualization type:",
            options=visualization_options,
            index=0,  # Default to Treemap
            key="customer_group_visualization_selector",
            horizontal=True
        )

    # Translate display names to column names if needed
    metric_column = selected_metric
    if selected_metric == "Hours worked":
        metric_column = "hours_used"
    elif selected_metric == "Billable hours":
        metric_column = "hours_billable"

    # Aggregate by customer group
    customer_group_agg = aggregate_by_customer_group(filtered_df)

    # Check if customer_group_agg is empty (customer_group column doesn't exist)
    if customer_group_agg.empty:
        st.warning("No customer group data available. The 'customer_group' column is not present in the dataset.")
        return

    # Filter based on selected metric - special handling for profit which can be negative
    if "profit" in selected_metric.lower():
        filtered_group_agg = customer_group_agg[customer_group_agg[metric_column] != 0]
    else:
        filtered_group_agg = customer_group_agg[customer_group_agg[metric_column] > 0]

    # Show warning if some customer groups were filtered out
    if len(filtered_group_agg) < len(customer_group_agg):
        excluded_count = len(customer_group_agg) - len(filtered_group_agg)
        if "profit" in selected_metric.lower():
            st.warning(f"{excluded_count} customer groups with zero {selected_metric} were excluded from visualization.")
        else:
            st.warning(f"{excluded_count} customer groups with zero {selected_metric} were excluded from visualization.")

    # Render visualization based on type
    if not filtered_group_agg.empty:
        if visualization_type == "Treemap":
            # Create hierarchical treemap with customer groups and underlying customers
            # Group by both customer_group and customer_name to build hierarchy
            customer_level_data = filtered_df.groupby(["customer_group", "customer_name"]).agg({
                metric_column: "sum" if metric_column in ["hours_used", "hours_billable", "Fee", "Total cost", "Total profit"] else "first"
            }).reset_index()

            # Build treemap data structure with proper ids, labels, parents, values
            ids = ["ROOT"]
            labels = ["Total"]
            parents = [""]
            values = [0]  # Will be calculated from children

            # Track which customer groups we've added
            group_totals = {}
            group_ids = {}

            # First pass: add all customer groups and their customers
            for _, row in customer_level_data.iterrows():
                group = row["customer_group"]
                customer = row["customer_name"]
                metric_value = row[metric_column]

                # Add customer group if not already added
                if group not in group_ids:
                    group_id = f"group_{group}"
                    group_ids[group] = group_id
                    ids.append(group_id)
                    labels.append(str(group))
                    parents.append("ROOT")
                    group_totals[group] = 0
                    values.append(0)  # Will be filled in with children sum

                # Add customer under group
                customer_id = f"customer_{group}_{customer}"
                ids.append(customer_id)
                labels.append(str(customer))
                parents.append(group_ids[group])
                values.append(metric_value)
                group_totals[group] += metric_value

            # Update group totals in values list
            for i, id_ in enumerate(ids):
                if id_.startswith("group_"):
                    group_name = id_.replace("group_", "")
                    if group_name in group_totals:
                        values[i] = group_totals[group_name]

            # Update root value
            values[0] = sum(group_totals.values())

            # Build color values (for continuous color scale)
            color_values = values.copy()

            # Create hierarchical treemap using graph_objects
            fig = go.Figure(data=[go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                marker=dict(
                    colors=color_values,
                    colorscale="Blues",
                    cmid=None,
                    line=dict(width=1)
                ),
                textposition="middle center",
                maxdepth=2  # Show customer groups at first, then customers on click
            )])

            fig.update_layout(
                title=f"Customer Group {selected_metric} Distribution",
                height=600,
                margin=dict(l=0, r=0, t=40, b=0)
            )

            render_chart(fig, "customer_group")

        elif visualization_type == "Bar chart":
            # Sort customer groups by selected metric in descending order
            sorted_groups = customer_group_agg.sort_values(metric_column, ascending=False)

            # Add a slider to control number of customer groups to display
            if len(customer_group_agg) > 1:
                num_groups = st.slider(
                    "Number of customer groups to display:",
                    min_value=1,
                    max_value=min(1000, len(customer_group_agg)),
                    value=min(10, len(customer_group_agg)),
                    step=1,
                    key="customer_group_count_slider"
                )
                # Limit the number of customer groups based on slider
                limited_groups = sorted_groups.head(num_groups)
            else:
                # If only one customer group, no need for slider
                limited_groups = sorted_groups

            # Create the bar chart with standardized custom data
            fig_bar = px.bar(
                limited_groups,
                x="customer_group",
                y=metric_column,
                color=metric_column,
                color_continuous_scale="Blues",
                title=f"{selected_metric} by Customer Group",
                custom_data=create_standardized_customdata(limited_groups)
            )

            # Improve layout for better readability
            fig_bar.update_layout(
                xaxis_title="",
                yaxis_title=selected_metric,
                xaxis={'categoryorder':'total descending'}
            )

            # Render the chart (this will apply styling from chart_styles)
            render_chart(fig_bar, "customer_group")
    else:
        if "profit" in selected_metric.lower():
            st.error(f"No customer groups have non-zero values for {selected_metric}.")
        else:
            st.error(f"No customer groups have values greater than zero for {selected_metric}.")


    # Display customer group data table with all metrics
    st.subheader("Customer Group Data Table")

    # Sort by hours worked in descending order
    sorted_group_agg = customer_group_agg.sort_values("hours_used", ascending=False)

    # Reorder columns for better presentation - include new cost/profit columns if they exist
    base_columns = ['customer_group', 'Number of projects',
                   'hours_used', 'hours_billable', 'Non-billable hours', 'Billability %']

    financial_columns = []
    if 'Fee' in sorted_group_agg.columns:
        financial_columns.append('Fee')
    if 'Total cost' in sorted_group_agg.columns:
        financial_columns.append('Total cost')
    if 'Total profit' in sorted_group_agg.columns:
        financial_columns.append('Total profit')
    if 'Profit margin %' in sorted_group_agg.columns:
        financial_columns.append('Profit margin %')

    rate_columns = []
    if 'Billable rate' in sorted_group_agg.columns:
        rate_columns.append('Billable rate')
    if 'Effective rate' in sorted_group_agg.columns:
        rate_columns.append('Effective rate')

    # Combine all columns that exist
    display_columns = base_columns + financial_columns + rate_columns
    existing_columns = [col for col in display_columns if col in sorted_group_agg.columns]

    sorted_group_agg = sorted_group_agg[existing_columns]

    # Use the column configuration from chart_styles
    from utils.chart_styles import create_column_config

    # Display the table with column configurations
    st.dataframe(
        sorted_group_agg,
        use_container_width=True,
        hide_index=True,
        column_config=create_column_config(sorted_group_agg)
    )

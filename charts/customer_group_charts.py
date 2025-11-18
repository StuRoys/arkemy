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
            # Aggregate ALL metrics for customer level (for hover templates)
            customer_level_data = filtered_df.groupby(["customer_group", "customer_name"]).agg({
                "hours_used": "sum",
                "hours_billable": "sum",
                "project_number": "nunique"
            }).reset_index()

            # Calculate additional metrics for customers
            customer_level_data["Billability %"] = (customer_level_data["hours_billable"] / customer_level_data["hours_used"] * 100).fillna(0).round(2)

            # Add fee
            if "fee_record" in filtered_df.columns:
                fee_by_customer = filtered_df.groupby(["customer_group", "customer_name"])["fee_record"].sum().reset_index(name="Fee")
                customer_level_data = pd.merge(customer_level_data, fee_by_customer, on=["customer_group", "customer_name"])
            else:
                customer_level_data["Fee"] = 0

            # Add cost
            if "cost_record" in filtered_df.columns:
                cost_by_customer = filtered_df.groupby(["customer_group", "customer_name"])["cost_record"].sum().reset_index(name="Total cost")
                customer_level_data = pd.merge(customer_level_data, cost_by_customer, on=["customer_group", "customer_name"])
            else:
                customer_level_data["Total cost"] = 0

            # Add profit
            if "profit_record" in filtered_df.columns:
                profit_by_customer = filtered_df.groupby(["customer_group", "customer_name"])["profit_record"].sum().reset_index(name="Total profit")
                customer_level_data = pd.merge(customer_level_data, profit_by_customer, on=["customer_group", "customer_name"])
            else:
                customer_level_data["Total profit"] = 0

            # Calculate rates
            customer_level_data["Billable rate"] = 0
            mask = customer_level_data["hours_billable"] > 0
            customer_level_data.loc[mask, "Billable rate"] = customer_level_data.loc[mask, "Fee"] / customer_level_data.loc[mask, "hours_billable"]

            customer_level_data["Effective rate"] = 0
            mask = customer_level_data["hours_used"] > 0
            customer_level_data.loc[mask, "Effective rate"] = customer_level_data.loc[mask, "Fee"] / customer_level_data.loc[mask, "hours_used"]

            # Calculate profit margin
            customer_level_data["Profit margin %"] = 0.0
            mask = customer_level_data["Fee"] > 0
            customer_level_data.loc[mask, "Profit margin %"] = (customer_level_data.loc[mask, "Total profit"] / customer_level_data.loc[mask, "Fee"] * 100).round(2)

            # Add percentage columns for sum metrics at customer level
            from utils.chart_styles import SUM_METRICS
            from utils.processors import add_percentage_columns
            customer_level_data = add_percentage_columns(customer_level_data, SUM_METRICS)

            # Build treemap data structure with proper ids, labels, parents, values, AND customdata
            # Start with ROOT node to enable proper depth control
            ids = ["ROOT"]
            labels = ["All Groups"]
            parents = [""]
            values = [0]  # Will be calculated from children
            customdata_list = []  # Will hold customdata for each node

            # Track which customer groups we've added
            group_totals = {}
            group_ids = {}
            group_metrics = {}  # Store aggregated metrics for each group

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
                    parents.append("ROOT")  # Parent is ROOT node
                    group_totals[group] = 0
                    values.append(0)  # Will be filled in with children sum
                    # Initialize group metrics accumulator
                    group_metrics[group] = {
                        "hours_used": 0,
                        "hours_billable": 0,
                        "project_number": 0,
                        "Fee": 0,
                        "Total cost": 0,
                        "Total profit": 0
                    }

                # Accumulate metrics for the group
                group_metrics[group]["hours_used"] += row["hours_used"]
                group_metrics[group]["hours_billable"] += row["hours_billable"]
                group_metrics[group]["project_number"] += row["project_number"]
                group_metrics[group]["Fee"] += row["Fee"]
                group_metrics[group]["Total cost"] += row["Total cost"]
                group_metrics[group]["Total profit"] += row["Total profit"]

                # Add customer under group (customdata will be added later to ensure order matches)
                customer_id = f"customer_{group}_{customer}"
                ids.append(customer_id)
                labels.append(str(customer))
                parents.append(group_ids[group])
                values.append(metric_value)

                group_totals[group] += metric_value

            # Build final customdata list matching the exact order of ids
            # Strategy: Build a map of id -> customdata, then construct final list in id order
            customdata_map = {}

            # ROOT customdata
            customdata_map["ROOT"] = [0] * 19

            # Group customdata (calculate for each group)
            for group_name in group_ids.keys():
                gm = group_metrics[group_name]
                billability = (gm["hours_billable"] / gm["hours_used"] * 100) if gm["hours_used"] > 0 else 0
                billable_rate = gm["Fee"] / gm["hours_billable"] if gm["hours_billable"] > 0 else 0
                effective_rate = gm["Fee"] / gm["hours_used"] if gm["hours_used"] > 0 else 0
                profit_margin = (gm["Total profit"] / gm["Fee"] * 100) if gm["Fee"] > 0 else 0

                group_customdata = [
                    gm["hours_used"],
                    gm["hours_billable"],
                    billability,
                    gm["project_number"],
                    billable_rate,
                    effective_rate,
                    gm["Fee"],
                    0, 0, 0, 0, 0, 0, 0, 0, 0,
                    gm["Total cost"],
                    gm["Total profit"],
                    profit_margin
                ]
                customdata_map[group_ids[group_name]] = group_customdata

            # Now rebuild customdata_list as a map for customers
            # Reset and rebuild properly mapped to customer IDs
            customer_customdata_map = {}
            for _, row in customer_level_data.iterrows():
                group = row["customer_group"]
                customer = row["customer_name"]
                customer_id = f"customer_{group}_{customer}"

                # Get percentage if it exists, otherwise 0
                pct_value = row.get(f'{metric_column}_pct', 0) if f'{metric_column}_pct' in customer_level_data.columns else 0

                customer_customdata_map[customer_id] = [
                    row["hours_used"],              # [0]
                    row["hours_billable"],          # [1]
                    row["Billability %"],           # [2]
                    row["project_number"],          # [3]
                    row["Billable rate"],           # [4]
                    row["Effective rate"],          # [5]
                    row["Fee"],                     # [6]
                    0, 0, 0, 0, 0, 0, 0, 0, 0,     # [7-15] planned/variance (not used)
                    row["Total cost"],              # [16]
                    row["Total profit"],            # [17]
                    row["Profit margin %"],         # [18]
                    pct_value                       # [19] percentage for treemap display
                ]

            customdata_map.update(customer_customdata_map)

            # Build final_customdata in the exact same order as ids list
            final_customdata = [customdata_map.get(id_, [0]*20) for id_ in ids]

            # Update group values in the values list
            for i, id_ in enumerate(ids):
                if id_.startswith("group_"):
                    group_name = id_.replace("group_", "")
                    if group_name in group_totals:
                        values[i] = group_totals[group_name]

            # Calculate ROOT value from all groups
            root_total = sum(group_totals.values())
            values[0] = root_total if root_total > 0 else 1  # Ensure it's not zero

            # Build discrete color assignment for better visual separation
            # Assign colors: darker shades to customer groups, lighter to customers within
            base_colors = px.colors.qualitative.Set2  # Soft, distinct colors

            color_map = {}
            unique_groups = list(group_totals.keys())

            # Assign a base color to each customer group
            for i, group in enumerate(unique_groups):
                base_color = base_colors[i % len(base_colors)]
                color_map[f"group_{group}"] = base_color

            # Assign lighter shades to customers (derive from group color)
            for id_ in ids:
                if id_.startswith("customer_"):
                    # Extract group from customer_id format: "customer_{group}_{customer}"
                    parts = id_.split("_", 2)
                    if len(parts) >= 2:
                        group = parts[1]
                        group_id = f"group_{group}"
                        if group_id in color_map:
                            color_map[id_] = color_map[group_id]  # Same color family

            # ROOT gets neutral color
            color_map["ROOT"] = "lightgray"

            # Build colors list matching ids order
            colors_list = [color_map.get(id_, "lightgray") for id_ in ids]

            # Create hierarchical treemap using graph_objects with discrete colors
            # Build text template based on whether percentage exists
            from utils.chart_helpers import build_treemap_texttemplate
            pct_column = f'{metric_column}_pct'
            has_percentage = pct_column in customer_level_data.columns
            texttemplate = build_treemap_texttemplate(metric_column, has_percentage)

            # Let apply_chart_style() handle marker styling (cornerradius, padding)
            fig = go.Figure(data=[go.Treemap(
                ids=ids,
                labels=labels,
                parents=parents,
                values=values,
                branchvalues="total",  # Calculate parent values from children
                customdata=final_customdata,  # Add full customdata for hover templates
                texttemplate=texttemplate,  # Show percentages on tiles for sum metrics
                marker=dict(
                    colors=colors_list,  # Discrete colors per tile
                    line=dict(width=2, color="white")  # White borders for separation
                ),
                textposition="middle center",
                maxdepth=2  # Show customer groups at depth 1, customers at depth 2 when drilling
            )])

            fig.update_layout(
                height=600,
                margin=dict(l=0, r=0, t=0, b=0)  # Remove top margin since no title
            )

            # Note: Click events don't work reliably with go.Treemap in Streamlit
            # The native drill-down functionality is available by clicking tiles
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


    # Display customer group data table with all metrics in an expander
    with st.expander("Details"):
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

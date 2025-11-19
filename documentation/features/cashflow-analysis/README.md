# Cashflow Analysis Feature

**When to use this guide**: Working on Cashflow Analysis feature, modifying Sankey diagram, debugging KPI calculations, or understanding cashflow metrics.

**Reference this file with**: `@documentation/features/cashflow-analysis/README.md`

---

## Overview

The Cashflow Analysis feature provides company-wide financial flow visualization showing how income flows to costs and profit, with year-over-year comparison. Supports grouping by Project, Customer, Person, or Price Model.

**Page**: `pages/7_Cashflow_Analysis.py`
**Chart Module**: `period_charts/cashflow_analysis.py`

## Key Features

### 1. Entity-Based Grouping
View cashflow grouped by different dimensions using `st.pills` selector:
- **Project** - Flow by individual projects (default)
- **Customer** - Flow by customers
- **Person** - Flow by team members
- **Price Model** - Flow by pricing model type

### 2. Sankey Diagram
Visual flow of financial data showing top entities flowing to total income, then to costs and profit:
```
Project 1 ──┐
Project 2 ──┤
   ...      ├──→ Total Income ──→ Profit
Project N ──┤                  └──→ Costs
Other ──────┘
```

Shows top 10 entities individually, groups remaining as "Other"

### 3. Period Selection
Time period options using `st.pills`:
- **1M** - Last complete month
- **3M** - Last 3 complete months
- **6M** - Last 6 complete months
- **YTD** - Year to date (Jan 1 to last complete month)
- **1Y** - Last 12 complete months
- **All** - All available data (no year-over-year comparison)

**Period Calculation**: Based on current date, always shows last complete month (current month - 1)

### 4. Year-Over-Year Comparison
KPI cards show current period vs same period last year with delta indicators:
- **Income** (e.g., "OCT 2025 - OCT 2025" vs "OCT 2024 - OCT 2024")
- **Cost** (inverse delta coloring: lower is better)
- **Profit**

Dynamic date labels show actual period ranges instead of generic labels.

### 5. Company-Wide View
Uses unfiltered `transformed_df` - **overrides all sidebar filters** for true company-wide perspective.

## Architecture

### Data Source

**Input**: `st.session_state.transformed_df` (time_records only)

**Why time_records only?**
- Cashflow analysis is about ACTUAL money flow
- Not forecasting or planning
- Historical financial performance only

**Bypasses Filters**:
```python
df_copy = st.session_state.transformed_df.copy()
# Uses original df, not filtered version from sidebar
```

**Why bypass filters?**
- Cashflow is company-wide financial metric
- Not project-specific or person-specific
- Shows total business health

### Period Calculation

**Key Principle**: Periods are based on **current date** (`pd.Timestamp.now()`), not dataset max date. This ensures consistent behavior regardless of dataset completeness.

**Last Complete Month** (`period_charts/cashflow_analysis.py:66-73`):
```python
# Calculate periods based on CURRENT date (today), not max_date in dataset
current_date = pd.Timestamp.now()

# Find last complete month (current month - 1)
last_month_end = current_date.replace(day=1) - pd.DateOffset(days=1)
last_complete_month_end = last_month_end.replace(day=1) + pd.offsets.MonthEnd(0)
```

**Current Period** (`period_charts/cashflow_analysis.py:75-125`):
```python
if selected_period_value == "all":
    current_start = min_date
    current_end = max_date
    current_period_df = df_copy.copy()
elif selected_period_value == "ytd":
    # YTD: January 1st to end of last complete month
    year_start = pd.Timestamp(year=current_date.year, month=1, day=1)
    current_start = year_start
    current_end = last_complete_month_end
    current_period_df = df_copy[
        (df_copy['record_date'] >= current_start) &
        (df_copy['record_date'] <= current_end)
    ]
else:
    # Month-based periods: N months ending at last complete month
    months = selected_period_value
    current_end = last_complete_month_end
    current_start = (current_end.replace(day=1) - pd.DateOffset(months=months-1))
    current_period_df = df_copy[
        (df_copy['record_date'] >= current_start) &
        (df_copy['record_date'] <= current_end)
    ]
```

**Year-Over-Year Comparison** (for comparison period):
```python
# Comparison period: same period last year
comparison_start = current_start - pd.DateOffset(years=1)
comparison_end = current_end - pd.DateOffset(years=1)
comparison_period_df = df_copy[
    (df_copy['record_date'] >= comparison_start) &
    (df_copy['record_date'] <= comparison_end)
]
has_comparison = not comparison_period_df.empty
```

**Examples**:
- **Viewing on Nov 19, 2025, selecting 1M**:
  - Current period: OCT 2025 (Oct 1 - Oct 31, 2025)
  - Comparison period: OCT 2024 (Oct 1 - Oct 31, 2024)
- **Viewing on Nov 19, 2025, selecting 3M**:
  - Current period: AUG 2025 - OCT 2025 (Aug 1 - Oct 31, 2025)
  - Comparison period: AUG 2024 - OCT 2024 (Aug 1 - Oct 31, 2024)
- **Selecting YTD (Year to Date)**:
  - Current period: JAN 2025 - OCT 2025 (Jan 1 - Oct 31, 2025)
  - Comparison period: JAN 2024 - OCT 2024 (Jan 1 - Oct 31, 2024)

## Metrics Calculation

### Function: `calculate_cashflow_metrics(df, entity_type="Project")`

**Location**: `period_charts/cashflow_analysis.py:157-212`

**Inputs**:
- `df`: DataFrame with time_records data
- `entity_type`: Type of entity to group by ("Project", "Customer", "Person", or "Price Model")

**Outputs**: Dictionary with cashflow metrics

**Entity Column Mapping** (`period_charts/cashflow_analysis.py:176-182`):
```python
entity_column_map = {
    "Project": "project_name",
    "Customer": "customer_name",
    "Person": "person_name",
    "Price Model": "price_model_type"
}
entity_column = entity_column_map.get(entity_type, "project_name")
```

**Entity-Level Fees** (`period_charts/cashflow_analysis.py:186-196`):
```python
# Calculate entity-level fees
project_fees = []
if entity_column in df.columns and 'fee_record' in df.columns:
    entity_groups = df.groupby(entity_column)['fee_record'].sum()
    # Filter out entities with 0 fees and sort by fee amount (descending)
    project_fees = [
        {'name': name, 'fee': fee}
        for name, fee in entity_groups.items()
        if fee > 0
    ]
    project_fees.sort(key=lambda x: x['fee'], reverse=True)
```

**Aggregate Metrics**:
```python
# Total income (sum of all fees)
total_income = df['fee_record'].sum()

# Total cost
total_cost = df['cost_record'].sum()

# Total profit (calculated as income - cost to ensure they add up to 100%)
total_profit = total_income - total_cost
```

**Returned Dictionary**:
```python
{
    'total_income': float,
    'total_cost': float,
    'total_profit': float,
    'project_fees': [  # Entity-level breakdown
        {'name': 'Project A', 'fee': 150000},
        {'name': 'Project B', 'fee': 120000},
        ...
    ]
}
```

## Sankey Diagram Implementation

### Function: `render_sankey_diagram(metrics, top_n_projects=10)`

**Location**: `period_charts/cashflow_analysis.py:215-367`

**Purpose**: Visualize cashflow from individual entities (projects, customers, persons, or price models) through total income to profit and costs.

### Entity Grouping (`period_charts/cashflow_analysis.py:230-241`)

Shows top N entities individually, groups remaining as "Other":
```python
# Split projects into top N and others
if len(project_fees) > top_n_projects:
    top_projects = project_fees[:top_n_projects]
    other_projects = project_fees[top_n_projects:]

    # Calculate total for "Other"
    other_total = sum(p['fee'] for p in other_projects)

    # Add "Other" as a single node
    display_projects = top_projects + [{'name': f'Other ({len(other_projects)})', 'fee': other_total}]
else:
    display_projects = project_fees
```

### Node Structure

**Dynamic Node Count**: N entities + 3 nodes (Total Income, Profit, Costs)

**Node Types**:
- **0 to N-1**: Individual entities (projects, customers, persons, or price models)
- **N**: Total Income (Standard blue: `#1f77b4`)
- **N+1**: Profit (Green: `#4caf50`)
- **N+2**: Costs (Red: `#e64a45`)

**Node Labels with Percentages** (`period_charts/cashflow_analysis.py:247-266`):
```python
# Add project nodes with percentages
for project in display_projects:
    percentage = (project['fee'] / total_income * 100) if total_income > 0 else 0
    label_with_percentage = f"{project['name']} ({percentage:.1f}%)"
    node_labels.append(label_with_percentage)

# Add Total Income, Profit, Costs nodes with percentages
profit_percentage = (total_profit / total_income * 100) if total_income > 0 else 0
cost_percentage = (total_cost / total_income * 100) if total_income > 0 else 0

node_labels.extend([
    "Total Income (100%)",
    f"Profit ({profit_percentage:.1f}%)",
    f"Costs ({cost_percentage:.1f}%)"
])
```

### Link Structure

**Entity Links**: Each entity → Total Income
**Breakdown Links**: Total Income → Profit, Total Income → Costs

```python
# Projects → Total Income
for i, project in enumerate(display_projects):
    link_sources.append(i)
    link_targets.append(total_income_idx)
    link_values.append(project['fee'])

# Total Income → Profit
if total_profit > 0:
    link_sources.append(total_income_idx)
    link_targets.append(profit_idx)
    link_values.append(total_profit)

# Total Income → Costs
if total_cost > 0:
    link_sources.append(total_income_idx)
    link_targets.append(costs_idx)
    link_values.append(total_cost)
```

### Plotly Configuration

**Key Settings**:
```python
fig = go.Figure(data=[go.Sankey(
    arrangement="snap",  # Auto-arrange nodes
    node=dict(
        pad=40,           # Spacing between nodes
        thickness=30,     # Node width
        label=node_labels,
        color=node_colors,
        customdata=formatted_values,  # For hover display
        hovertemplate='%{label}<br>%{customdata}<extra></extra>'
    ),
    link=dict(
        source=[...],  # Source node indices
        target=[...],  # Target node indices
        value=[...],   # Flow values
        color=[...]    # Link colors (semi-transparent node colors)
    )
)])
```

**Layout**:
```python
fig.update_layout(
    font_size=12,
    height=500,
    margin=dict(l=20, r=20, t=40, b=20),
    paper_bgcolor='rgba(255,255,255,0.9)'
)
```

### Color Scheme

**Node Colors** (`period_charts/cashflow_analysis.py:272-294`):
- Entity nodes: Cycle through blue shades palette
- "Other" node: Gray (`#9ca3af`)
- Total Income: Standard blue (`#1f77b4`)
- Profit: Green (`#4caf50`)
- Costs: Red (`#e64a45`)

**Link Colors**:
- Use source node color with 30% opacity: `rgba(r, g, b, 0.3)`
- Provides visual flow continuity from entity to total income
- Profit link: Green with transparency `rgba(76, 175, 80, 0.3)`
- Cost link: Red with transparency `rgba(230, 74, 69, 0.3)`

## KPI Cards Implementation

### Function: `render_kpi_cards(current_metrics, comparison_metrics, has_comparison, current_start, current_end, comparison_start, comparison_end)`

**Location**: `period_charts/cashflow_analysis.py:370-461`

**Purpose**: Display year-over-year comparison with dynamic date labels

### Layout Structure

**3 Columns (Income, Cost, Profit)**:

Each container has 2 metric cards:
```
#### Income
[OCT 2025 - OCT 2025]  ← Current period with delta
[OCT 2024 - OCT 2024]  ← Comparison period (same period last year)

#### Cost
[OCT 2025 - OCT 2025]  ← Current period with delta (inverse coloring)
[OCT 2024 - OCT 2024]  ← Comparison period

#### Profit
[OCT 2025 - OCT 2025]  ← Current period with delta
[OCT 2024 - OCT 2024]  ← Comparison period
```

### Dynamic Date Labels (`period_charts/cashflow_analysis.py:390-392`)

```python
# Format date labels
current_label = f"{current_start.strftime('%b %Y').upper()} - {current_end.strftime('%b %Y').upper()}"
comparison_label = f"{comparison_start.strftime('%b %Y').upper()} - {comparison_end.strftime('%b %Y').upper()}"
```

**Examples**:
- 1M period: "OCT 2025 - OCT 2025" vs "OCT 2024 - OCT 2024"
- 3M period: "AUG 2025 - OCT 2025" vs "AUG 2024 - OCT 2024"
- YTD period: "JAN 2025 - OCT 2025" vs "JAN 2024 - OCT 2024"

### Metric Cards

**Current Period Card** (with delta):
```python
st.metric(
    label=current_label,  # Dynamic date range
    value=format_currency(current_metrics['total_income'], decimals=0),
    delta=format_currency(income_delta, decimals=0) if has_comparison else None,
    delta_color="normal"  # Green up, red down
)
```

**Comparison Period Card** (no delta):
```python
if has_comparison:
    st.metric(
        label=comparison_label,  # Dynamic date range
        value=format_currency(comparison_metrics['total_income'], decimals=0)
    )
else:
    st.metric(
        label=comparison_label,
        value="N/A"  # When "All" period selected (no year-over-year data)
    )
```

### Delta Calculation (`period_charts/cashflow_analysis.py:385-388`)

```python
income_delta = current_metrics['total_income'] - comparison_metrics['total_income']
cost_delta = current_metrics['total_cost'] - comparison_metrics['total_cost']
profit_delta = current_metrics['total_profit'] - comparison_metrics['total_profit']
```

### Delta Color Logic

**Income and Profit**:
- `delta_color="normal"` - Higher is good (green ↑), lower is bad (red ↓)

**Cost**:
- `delta_color="inverse"` - Higher is bad (red ↑), lower is good (green ↓)

## File Structure

```
pages/
  └── 7_Cashflow_Analysis.py          # Page entry point

period_charts/
  └── cashflow_analysis.py            # Main feature logic
      ├── render_cashflow_analysis()  # Main render function
      ├── calculate_cashflow_metrics()  # Metrics calculation
      ├── render_sankey_diagram()      # Sankey chart
      └── render_kpi_cards()           # KPI comparison cards
```

## Data Requirements

### Required DataFrame Columns

**From `transformed_df` (time_records)**:
- `record_date` - Date of the record (datetime)
- `fee_record` - Revenue/fees generated (float)
- `cost_record` - Total cost (float)

**Entity Columns** (at least one required):
- `project_name` - Project identifier (for Project view)
- `customer_name` - Customer identifier (for Customer view)
- `person_name` - Person identifier (for Person view)
- `price_model_type` - Price model identifier (for Price Model view)

### Column Usage

**`record_date`**:
- Used for period filtering
- Must be datetime type
- Critical for year-over-year comparison calculation

**`fee_record`**:
- Total revenue for the record
- Summed to get total income
- Grouped by selected entity type

**`cost_record`**:
- Total cost for the record
- Summed to get total costs
- Subtracted from income to get profit

**Entity Columns**:
- Used for grouping cashflow by entity
- Determines Sankey diagram source nodes
- Each entity type has dedicated column (see entity_column_map above)

## Implementation Notes

### Currency Formatting

**Uses**: `utils/currency_formatter.py:format_currency()`

**Settings**:
```python
format_currency(value, decimals=0)
# No decimal places for cashflow metrics
# Includes thousand separators
# Uses currency from st.session_state.currency
```

### UI Controls with Pills Widget

**Streamlit Feature**: `st.pills()` (introduced in Streamlit 1.30)

**Why pills instead of radio/selectbox?**
- Cleaner UI
- Better visual hierarchy
- Horizontal layout saves space
- Modern look and feel

**Period Selection** (`period_charts/cashflow_analysis.py:38-54`):
```python
period_options = {
    "1M": 1,
    "3M": 3,
    "6M": 6,
    "YTD": "ytd",
    "1Y": 12,
    "All": "all"
}

selected_period_key = st.pills(
    "Period",
    options=list(period_options.keys()),
    default="1M",
    label_visibility="visible"
)

selected_period_value = period_options.get(selected_period_key, 1)  # Default to 1 month if None
```

**Entity Selection** (`period_charts/cashflow_analysis.py:56-64`):
```python
entity_options = ["Project", "Customer", "Person", "Price Model"]

selected_entity = st.pills(
    "View",
    options=entity_options,
    default="Project",
    label_visibility="visible"
)
```

### Empty State Handling

**No comparison period** (when "All" is selected):
```python
has_comparison = False
comparison_metrics = {
    'total_income': 0,
    'total_cost': 0,
    'total_profit': 0,
    'project_fees': []
}
# KPI cards show "N/A" for comparison period
```

**No data in period**:
```python
if df.empty:
    return {
        'total_income': 0,
        'total_cost': 0,
        'total_profit': 0,
        'project_fees': []
    }
# All metrics show as 0
```

## Troubleshooting

### Issue: Sankey diagram not showing

**Possible causes**:
- All metrics are 0 (no data in period)
- Missing required entity column
- Data type issues (ensure floats, not strings)
- No entities with positive fees

**Debug**:
```python
st.write("Metrics:", current_metrics)
st.write("Data shape:", current_period_df.shape)
st.write("Columns:", current_period_df.columns.tolist())
st.write("Project fees:", current_metrics['project_fees'])
```

### Issue: Incorrect flow values

**Check**:
- Selected entity column exists in dataframe
- No NULL values in `fee_record` or `cost_record`
- Data is not pre-filtered incorrectly
- Entity names are valid (not all NaN)

**Verify**:
```python
st.write("Selected entity:", selected_entity)
st.write("Entity column:", entity_column)
st.write("Unique entities:", df[entity_column].unique())
st.write("Fee sum:", df['fee_record'].sum())
st.write("Cost sum:", df['cost_record'].sum())
```

### Issue: Year-over-year comparison showing wrong dates

**Check**:
- `record_date` is datetime type
- Current date calculation is correct
- Year offset calculation is working
- Comparison period has data

**Debug**:
```python
st.write("Current date:", current_date)
st.write("Last complete month end:", last_complete_month_end)
st.write("Current start:", current_start)
st.write("Current end:", current_end)
st.write("Comparison start:", comparison_start)
st.write("Comparison end:", comparison_end)
st.write("Current period records:", len(current_period_df))
st.write("Comparison period records:", len(comparison_period_df))
```

### Issue: Pills widget returning None

**Possible cause**:
- Widget not fully initialized on first render

**Fix**:
Use `.get()` with default value instead of direct dictionary access:
```python
# Instead of:
selected_period_value = period_options[selected_period_key]

# Use:
selected_period_value = period_options.get(selected_period_key, 1)
```

## Future Enhancements

**Potential additions**:
- Monthly trend line chart (income/cost/profit over time)
- Export cashflow data to CSV
- Customizable period ranges (date picker)
- Drill-down capability (click entity to see breakdown)
- Multi-year comparison (compare 2025 vs 2024 vs 2023)

## Related Documentation

- Data architecture: [../../architecture/data-architecture.md](../../architecture/data-architecture.md)
- Session state: [../../architecture/session-state-management.md](../../architecture/session-state-management.md)
- Currency formatting: `utils/currency_formatter.py`
- Plotly Sankey docs: https://plotly.com/python/sankey-diagram/

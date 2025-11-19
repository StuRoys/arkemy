# Cashflow Analysis Feature

**When to use this guide**: Working on Cashflow Analysis feature, modifying Sankey diagram, debugging KPI calculations, or understanding cashflow metrics.

**Reference this file with**: `@documentation/features/cashflow-analysis/README.md`

---

## Overview

The Cashflow Analysis feature provides company-wide financial flow visualization showing how income (hourly + fixed-price fees) flows to costs and profit, with period-over-period comparison.

**Page**: `pages/7_Cashflow_Analysis.py`
**Chart Module**: `period_charts/cashflow_analysis.py`

## Key Features

### 1. Sankey Diagram
Visual flow of financial data:
```
Hourly Rate Fees ──┐
                   ├──→ Total Income ──→ Costs
Fixed Price Fees ──┘                 └──→ Profit
```

### 2. Period Selection
Time period options using `st.pills`:
- **1M** - Last 1 month
- **3M** - Last 3 months
- **6M** - Last 6 months
- **1Y** - Last 1 year
- **All** - All available data (no comparison)

### 3. KPI Comparison
Side-by-side metrics with delta indicators:
- **Income** (Current vs Preceding period)
- **Cost** (Current vs Preceding period, inverse delta coloring)
- **Profit** (Current vs Preceding period)

### 4. Company-Wide View
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

**Current Period** (`period_charts/cashflow_analysis.py:52-74`):
```python
max_date = df_copy['record_date'].max()

if selected_period_value == "all":
    current_period_df = df_copy.copy()
else:
    months = selected_period_value  # e.g., 1, 3, 6, 12
    current_start = max_date - pd.DateOffset(months=months)
    current_period_df = df_copy[df_copy['record_date'] >= current_start]
```

**Preceding Period** (for comparison):
```python
# Same duration as current period, but shifted back in time
preceding_start = current_start - pd.DateOffset(months=months)
preceding_period_df = df_copy[
    (df_copy['record_date'] >= preceding_start) &
    (df_copy['record_date'] < current_start)
]
```

**Example**:
- Current period: Last 3 months (Oct 1 - Dec 31)
- Preceding period: 3 months before that (Jul 1 - Sep 30)

## Metrics Calculation

### Function: `calculate_cashflow_metrics(df)`

**Location**: `period_charts/cashflow_analysis.py:100-148`

**Inputs**: DataFrame with time_records data

**Outputs**: Dictionary with cashflow metrics

**Metrics**:

```python
# Separate fees by price model
hourly_fees = df[price_model_type == 'hourly_rate']['fee_record'].sum()
fixed_fees = df[price_model_type == 'fixed_price']['fee_record'].sum()

# Total income
total_income = hourly_fees + fixed_fees

# Costs and profit
total_cost = df['cost_record'].sum()
total_profit = total_income - total_cost
```

**Returned Dictionary**:
```python
{
    'total_income': float,
    'total_cost': float,
    'total_profit': float,
    'hourly_fees': float,
    'fixed_fees': float
}
```

## Sankey Diagram Implementation

### Function: `render_sankey_diagram(metrics)`

**Location**: `period_charts/cashflow_analysis.py:151-246`

### Node Structure

**5 Nodes**:
0. Hourly Rate Fees (Deep blue: `#5b7fa7`)
1. Fixed Price Fees (Light blue: `#88b1df`)
2. Total Income (Standard blue: `#1f77b4`)
3. Costs (Red: `#e64a45`)
4. Profit (Green: `#4caf50`)

### Link Structure

**4 Links** (flow connections):
1. Hourly Rate Fees → Total Income
2. Fixed Price Fees → Total Income
3. Total Income → Costs
4. Total Income → Profit

**Link Data Structure**:
```python
links = [
    {"source": 0, "target": 2, "value": hourly_fees},    # Hourly → Income
    {"source": 1, "target": 2, "value": fixed_fees},     # Fixed → Income
    {"source": 2, "target": 3, "value": total_cost},     # Income → Cost
    {"source": 2, "target": 4, "value": total_profit}    # Income → Profit
]
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

**Node Colors**:
- Income nodes: Blue shades (deep → light → standard)
- Cost node: Red
- Profit node: Green

**Link Colors**:
- Use node color with 30% opacity: `rgba(r, g, b, 0.3)`
- Provides visual flow continuity

## KPI Cards Implementation

### Function: `render_kpi_cards(current_metrics, preceding_metrics, has_preceding)`

**Location**: `period_charts/cashflow_analysis.py:249-334`

### Layout Structure

**3 Rows × 2 Columns**:

```
#### Income
[Current Period]  [Preceding Period]

#### Cost
[Current Period]  [Preceding Period]

#### Profit
[Current Period]  [Preceding Period]
```

### Metric Cards

**Current Period Card** (with delta):
```python
st.metric(
    label="Current Period",
    value=format_currency(current_metrics['total_income'], decimals=0),
    delta=format_currency(income_delta, decimals=0) if has_preceding else None,
    delta_color="normal"  # Green up, red down
)
```

**Preceding Period Card** (no delta):
```python
if has_preceding:
    st.metric(
        label="Preceding Period",
        value=format_currency(preceding_metrics['total_income'], decimals=0)
    )
else:
    st.metric(
        label="Preceding Period",
        value="N/A"  # When "All" period selected
    )
```

### Delta Calculation

```python
income_delta = current_metrics['total_income'] - preceding_metrics['total_income']
cost_delta = current_metrics['total_cost'] - preceding_metrics['total_cost']
profit_delta = current_metrics['total_profit'] - preceding_metrics['total_profit']
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
- `price_model_type` - "hourly_rate" or "fixed_price"
- `fee_record` - Revenue/fees generated (float)
- `cost_record` - Total cost (float)

### Column Usage

**`price_model_type`**:
- Used to separate hourly fees from fixed price fees
- Critical for Sankey diagram source nodes
- Must be one of: "hourly_rate", "fixed_price"

**`fee_record`**:
- Total revenue for the record
- Summed to get total income
- Split by price model type

**`cost_record`**:
- Total cost for the record
- Summed to get total costs
- Subtracted from income to get profit

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

### Period Pills Widget

**Streamlit Feature**: `st.pills()` (introduced in Streamlit 1.30)

**Why pills instead of radio/selectbox?**
- Cleaner UI
- Better visual hierarchy
- Horizontal layout saves space
- Modern look and feel

**Configuration**:
```python
selected_period_key = st.pills(
    "Period",
    options=list(period_options.keys()),  # ["1M", "3M", "6M", "1Y", "All"]
    default="1M",
    label_visibility="collapsed"  # Hide label, use section header instead
)
```

### Empty State Handling

**No preceding period** (when "All" is selected):
```python
has_preceding = False
preceding_metrics = {
    'total_income': 0,
    'total_cost': 0,
    'total_profit': 0,
    'hourly_fees': 0,
    'fixed_fees': 0
}
# KPI cards show "N/A" for preceding period
```

**No data in period**:
```python
if df.empty:
    return {
        'total_income': 0,
        'total_cost': 0,
        'total_profit': 0,
        'hourly_fees': 0,
        'fixed_fees': 0
    }
# All metrics show as 0
```

## Troubleshooting

### Issue: Sankey diagram not showing

**Possible causes**:
- All metrics are 0 (no data in period)
- Missing required columns
- Data type issues (ensure floats, not strings)

**Debug**:
```python
st.write("Metrics:", current_metrics)
st.write("Data shape:", current_period_df.shape)
st.write("Columns:", current_period_df.columns.tolist())
```

### Issue: Incorrect flow values

**Check**:
- `price_model_type` values are correct ("hourly_rate" or "fixed_price")
- No NULL values in `fee_record` or `cost_record`
- Data is not pre-filtered incorrectly

**Verify**:
```python
st.write("Unique price models:", df['price_model_type'].unique())
st.write("Fee sum:", df['fee_record'].sum())
st.write("Cost sum:", df['cost_record'].sum())
```

### Issue: Period comparison showing wrong dates

**Check**:
- `record_date` is datetime type
- Max date is correct
- Offset calculation is working

**Debug**:
```python
st.write("Max date:", df['record_date'].max())
st.write("Current start:", current_start)
st.write("Preceding start:", preceding_start)
st.write("Current period records:", len(current_period_df))
st.write("Preceding period records:", len(preceding_period_df))
```

## Future Enhancements

**Potential additions**:
- Monthly trend line chart (income/cost/profit over time)
- Breakdown by customer or project (top contributors)
- Year-over-year comparison
- Export cashflow data to CSV
- Customizable period ranges (date picker)

## Related Documentation

- Data architecture: [../../architecture/data-architecture.md](../../architecture/data-architecture.md)
- Session state: [../../architecture/session-state-management.md](../../architecture/session-state-management.md)
- Currency formatting: `utils/currency_formatter.py`
- Plotly Sankey docs: https://plotly.com/python/sankey-diagram/

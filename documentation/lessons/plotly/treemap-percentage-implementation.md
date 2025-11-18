# Treemap Percentage Display Implementation

## Overview

This document describes the implementation of dynamic percentage display on Plotly treemap tiles across all chart categories in Arkemy. The solution provides a generalized approach to calculating and displaying percentages for sum metrics without duplicating logic across multiple chart modules.

### Problem Statement
- Users need to see what percentage each category represents of the total
- Percentages should appear on treemap tiles alongside labels
- Display format: "Label\nXX.X%"
- Solution must work across 8 chart categories with different structures
- Some charts use hierarchical treemaps (drill-down enabled)

### Solution Approach
Instead of hardcoding percentage calculations in each chart module, the solution:
1. Calculates percentages in the data layer (processors.py) using a shared helper
2. Extends customdata array to include percentage at index [19]
3. Uses conditional texttemplate that only displays percentages for sum metrics
4. Applies consistently across both simple and hierarchical treemaps

### Key Benefits
- Single source of truth for sum metrics (SUM_METRICS constant)
- Avoids code duplication across 8 chart modules
- Conditional display: percentages only appear when data supports them
- Works with hierarchical treemaps requiring custom drill-down logic

---

## Architecture

### Core Components

#### 1. SUM_METRICS Constant
**File**: `utils/chart_styles.py:11-17`

```python
SUM_METRICS = [
    "hours_used",
    "hours_billable",
    "Fee",
    "Total cost",
    "Total profit"
]
```

Single source of truth for metrics that should display percentages. Any metric in this list gets percentage calculations added to aggregated data.

#### 2. add_percentage_columns() Helper
**File**: `utils/processors.py:9-36`

```python
def add_percentage_columns(df: pd.DataFrame, sum_metrics: List[str]) -> pd.DataFrame:
    result_df = df.copy()
    for metric in sum_metrics:
        if metric in result_df.columns:
            total = result_df[metric].sum()
            if total > 0:
                result_df[f'{metric}_pct'] = (result_df[metric] / total) * 100
            else:
                result_df[f'{metric}_pct'] = 0
    return result_df
```

Calculates percentages for all sum metrics. Creates new columns named `{metric}_pct` (e.g., `hours_used_pct`, `Fee_pct`).

**Key points:**
- Operates at the dataframe level, after aggregation
- Adds new columns without modifying original data
- Handles zero totals gracefully
- Called by all 8 aggregation functions

#### 3. Customdata Array Extension
**File**: `utils/chart_helpers.py:155-158`

`create_standardized_customdata()` returns 20 elements:
- Indices [0-18]: Standard metrics (hours, rates, costs, profits, variances)
- Index [19]: Percentage placeholder (populated dynamically)

All treemap implementations must use 20-element customdata arrays to support percentage display.

#### 4. build_treemap_texttemplate() Helper
**File**: `utils/chart_helpers.py:10-27`

```python
def build_treemap_texttemplate(metric, has_percentage_column):
    if has_percentage_column:
        return '%{label}<br>%{customdata[19]:.1f}%'
    else:
        return '%{label}'
```

Returns appropriate texttemplate based on whether percentage data exists. Only shows percentages when `{metric}_pct` column is present.

#### 5. create_single_metric_chart() for Simple Treemaps
**File**: `utils/chart_helpers.py:270-424`

Handles both bar charts and treemaps. For treemaps:
- Builds hierarchical structure (root → items)
- Populates customdata with percentage values (lines 382-386)
- Automatically detects and applies percentage display

```python
# Add percentage values if they exist (index [19])
if has_percentage:
    for i, pct_val in enumerate(df[pct_column], 1):  # Start from 1 to skip root
        if i < len(customdata_list):
            customdata_list[i][19] = pct_val
```

---

## Implementation Patterns

### Pattern 1: Simple Treemaps (7 Chart Modules)

**Used by**: customer, people, phase, activity, price_model, project_type (basic), and project charts

**How it works**:
1. Call `aggregate_by_[category]()` to get aggregated data
2. `add_percentage_columns()` called inside aggregation function (e.g., line 428 in processors.py)
3. For treemaps, call `create_single_metric_chart()` helper
4. Percentage display handled automatically

**Example from people_charts.py**:
```python
# Aggregation includes percentages
person_agg = aggregate_by_person(filtered_df)

# For treemaps, use centralized helper
if visualization_type == "Treemap":
    fig = create_single_metric_chart(
        filtered_person_agg,
        metric_column,
        f"People {selected_metric} Distribution",
        chart_type="treemap",
        x_field="person_name"
    )
    render_chart(fig, "person")
```

### Pattern 2: Hierarchical Treemaps (2 Chart Modules)

**Used by**: customer_group_charts (groups → customers) and project_type_charts (when drill-down needed)

**Differences from simple treemaps**:
1. Manual treemap building with go.Treemap()
2. Two or more hierarchy levels
3. Must manually populate customdata and percentages
4. Different percentage calculations for each level

#### customer_group_charts Example

**Three-step customdata building**:

1. **Root customdata** (line 190):
   ```python
   customdata_map["ROOT"] = [0] * 20
   ```

2. **Group customdata** (lines 200-214):
   ```python
   group_customdata = [
       # ... 19 standard metrics ...
       0  # [19] percentage (placeholder)
   ]
   customdata_map[group_ids[group_name]] = group_customdata
   ```

3. **Customer customdata** (lines 226-239):
   ```python
   customer_customdata_map[customer_id] = [
       # ... 19 standard metrics ...
       pct_value  # [19] percentage (from {metric}_pct column)
   ]
   ```

**Group percentage calculation** (lines 258-265):
```python
if root_total > 0:
    for group_name, group_total in group_totals.items():
        group_pct = (group_total / root_total) * 100
        group_id = group_ids[group_name]
        if group_id in customdata_map and len(customdata_map[group_id]) > 19:
            customdata_map[group_id][19] = group_pct
```

**Key insight**: Group percentages are calculated relative to root, while customer percentages come from the global percentage columns.

#### project_type_charts Example

**Percentage population** (lines 156-161):
```python
pct_column = f'{metric_column}_pct'
if pct_column in filtered_project_type_agg.columns:
    for i, pct_val in enumerate(filtered_project_type_agg[pct_column], 1):
        if i < len(customdata_list):
            customdata_list[i][19] = pct_val
```

Populates percentages for all items, with root getting 0 (skip via enumerate start=1).

---

## Customdata Array Structure

All treemaps use 20-element customdata arrays. Each index represents:

```
[0]  hours_used
[1]  hours_billable
[2]  Billability %
[3]  Number of projects (or similar count)
[4]  Billable rate
[5]  Effective rate
[6]  Fee
[7-15] Variance metrics (planned/actual comparisons)
[16] Total cost
[17] Total profit
[18] Profit margin %
[19] Metric percentage (for treemap display)
```

### Why Size Matters
- Texttemplate references `%{customdata[19]}`
- All items in customdata array must have same length
- If any item has fewer elements, Plotly shows raw template code
- Always ensure **all nodes** have 20-element customdata

### Common Mistake
In hierarchical treemaps, forgetting to add element [19]:
```python
# ❌ WRONG - only 19 elements
group_customdata = [hours, billable, ..., margin]

# ✅ CORRECT - 20 elements
group_customdata = [hours, billable, ..., margin, 0]  # 0 for percentage placeholder
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Array Size Mismatch
**Symptom**: Raw texttemplate code appears on tiles: `%{label}<br>%{customdata[19]:.1f}%`

**Root cause**: Some customdata items have 19 elements, others have 20

**Solution**:
```python
# Ensure ALL items in customdata list have 20 elements
# Root node
customdata_list = [[0] * 20]

# Child items
for item in items:
    item_data = [... 20 elements ...]
    customdata_list.append(item_data)
```

**Affected files fixed**:
- customer_group_charts.py: Root (line 190) and groups (line 212)
- project_type_charts.py: Root handled at line 141

### Pitfall 2: Missing Percentage Population
**Symptom**: All tiles show 0.0% even though data supports percentages

**Root cause**: Percentage columns calculated but not transferred to customdata[19]

**Solution**: Always populate index [19] after building customdata:
```python
# After building customdata arrays
pct_column = f'{metric_column}_pct'
if pct_column in df.columns:
    for i, pct_val in enumerate(df[pct_column], 1):
        if i < len(customdata_list):
            customdata_list[i][19] = pct_val
```

**Affected files fixed**:
- project_type_charts.py: Lines 156-161
- customer_group_charts.py: Customer percentages already correct (line 238)

### Pitfall 3: Hierarchical Level Percentage Timing
**Symptom**: Group tiles show 0.0% instead of group percentages

**Root cause**: Group percentage calculation happens before group totals are known

**Solution**: Calculate parent-level percentages AFTER computing all totals:
```python
# Step 1: Compute root total
root_total = sum(group_totals.values())

# Step 2: NOW calculate group percentages relative to root
if root_total > 0:
    for group_name, group_total in group_totals.items():
        group_pct = (group_total / root_total) * 100
        customdata_map[group_id][19] = group_pct
```

**Affected files fixed**:
- customer_group_charts.py: Lines 258-265

### Pitfall 4: Percentage Calculation Method
**Symptom**: Percentages don't add up to 100%

**Root cause**: Using different denominators (e.g., some items sum globally, others locally)

**Solution**: Be consistent about baseline:
```
Simple treemaps: percentage = item_value / total_all_items * 100
Hierarchical:    group_pct = group_total / root_total * 100
                 item_pct = item_value / total_all_items * 100
```

Child-level percentages should reference global totals, parent-level percentages reference their parent's total.

---

## File Reference Map

### Modified Files

| File | Change | Lines | Purpose |
|------|--------|-------|---------|
| utils/chart_styles.py | Added SUM_METRICS | 11-17 | Define which metrics get percentages |
| utils/processors.py | Added add_percentage_columns() | 9-36 | Calculate percentages |
| utils/processors.py | Update 8 aggregation functions | Various | Call add_percentage_columns() |
| utils/chart_helpers.py | Added build_treemap_texttemplate() | 10-27 | Build conditional texttemplate |
| utils/chart_helpers.py | Extended customdata to [19] | 155-158 | Add percentage placeholder |
| utils/chart_helpers.py | Update create_single_metric_chart() | 382-386 | Populate percentage for simple treemaps |
| charts/customer_charts.py | Replaced with create_single_metric_chart() | 75-83 | Use centralized helper |
| charts/people_charts.py | Replaced with create_single_metric_chart() | 74-83 | Use centralized helper |
| charts/phase_charts.py | Replaced with create_single_metric_chart() | 77-85 | Use centralized helper |
| charts/activity_charts.py | Replaced with create_single_metric_chart() | 78-85 | Use centralized helper |
| charts/price_model_charts.py | Replaced with create_single_metric_chart() | 77-84 | Use centralized helper |
| charts/project_type_charts.py | Populate percentages manually | 156-161 | Handle manual treemap structure |
| charts/customer_group_charts.py | Ensure customdata size + populate | Multiple | Handle two-level hierarchy |

### Aggregation Functions Updated

All 8 functions now call `add_percentage_columns()`:

1. `aggregate_by_customer()` - processors.py:428
2. `aggregate_by_customer_group()` - processors.py:494
3. `aggregate_by_project()` - processors.py:573
4. `aggregate_by_project_tag()` - processors.py:649
5. `aggregate_by_phase()` - processors.py:728
6. `aggregate_by_price_model()` - processors.py:798
7. `aggregate_by_activity()` - processors.py:869
8. `aggregate_by_person()` - processors.py:936

---

## Data Flow Diagram

```
Raw Data (filtered_df)
    ↓
[Aggregation Function]
    ├─ Groups data by category
    ├─ Calculates metrics (hours, fees, rates, etc.)
    └─ Calls add_percentage_columns(df, SUM_METRICS)
        ↓
    [add_percentage_columns()]
        ├─ For each metric in SUM_METRICS
        ├─ Calculates: {metric}_pct = (value / total) * 100
        └─ Returns df with new pct columns
    ↓
Aggregated DataFrame with Percentages
    ↓
[Chart Rendering]
    ├─ Simple treemaps: use create_single_metric_chart()
    │   └─ Automatically finds {metric}_pct columns
    │   └─ Populates customdata[19]
    │   └─ Applies texttemplate
    │
    └─ Hierarchical treemaps: manual customdata building
        └─ Manually populate customdata[19] from {metric}_pct columns
        └─ Calculate parent-level percentages
        └─ Apply texttemplate
    ↓
Treemap with Percentage Display
```

---

## Testing Checklist

### Visual Verification
- [ ] Navigate to each chart category (customer, people, phase, activity, price_model, project_type, customer_group, project)
- [ ] Switch to Treemap visualization
- [ ] Verify percentages display on tiles in format: "Label\nXX.X%"
- [ ] Select different sum metrics (Hours worked, Billable hours, Fee, Total cost, Total profit)
- [ ] Verify percentages update with metric selection
- [ ] Verify percentages add up to ~100% (allowing for rounding)

### Hierarchical Treemap Testing (customer_group_charts)
- [ ] Verify group tiles show percentages (% of root)
- [ ] Verify customer tiles show percentages (% of global)
- [ ] Verify percentages still display after drill-down (clicking on group)
- [ ] Verify raw texttemplate code does NOT appear

### Edge Cases
- [ ] When metric selected = non-sum metric (should show no percentages)
- [ ] When all values are zero (should show 0.0% or no percentages)
- [ ] When filtering leaves only one category (should show 100%)

### Performance
- [ ] Page loads without lag
- [ ] Metric selection doesn't cause delay
- [ ] Drill-down in hierarchical treemaps is smooth

---

## Future Considerations

### Multi-Level Drill-Down Architecture
Currently, project_type_charts has the infrastructure for drill-down but only one hierarchy level. Future enhancement:
- Project charts: Projects → Activities
- Customer charts: Customers → Projects
- Person charts: People → Projects/Activities

Would require:
1. Extending hierarchy to multiple levels
2. Different percentage calculations per level (local vs global)
3. Click handlers to navigate drill-down

### Extending to Other Metric Types
Current implementation only handles sum metrics. Could extend for:
- **Average metrics**: Show average value distribution
- **Ratio metrics**: Show relative rates or margins
- **Variance metrics**: Show planned vs actual divergence

Would need:
1. New metric category constants
2. Different percentage calculation logic
3. Potentially different texttemplate formats

### Performance Optimization
For very large datasets (10,000+ items):
1. Consider pre-aggregating percentages in data loading
2. Implement percentage caching layer
3. Evaluate rendering performance with deep hierarchies

### Consistency Across Frameworks
If expanding visualization to other libraries (Tableau, PowerBI, etc.):
1. Establish percentage calculation standards
2. Document texttemplate equivalent syntax
3. Create percentage calculation utility for reuse

---

## Related Documentation

- @.claude/docs/architecture.md - Overall Arkemy architecture
- @.claude/docs/data-model.md - Data types and aggregation patterns
- @.claude/docs/plotly.md - Plotly-specific guidelines
- CLAUDE.md (project root) - Development workflow

---

**Last Updated**: 2025-11-18
**Status**: Complete - All treemap percentages working across 8 chart categories

# Plotly Reference Guide

## Treemap Visualizations

### Key Insights for Hierarchical Treemaps

#### `branchvalues="total"` Behavior
This parameter is critical for hierarchical treemaps and its behavior is counterintuitive:

**What it DOES:**
- Tells Plotly that parent node values represent the **sum of their children**
- When set to "total", parent values are treated as aggregates, not independent values
- Plotly will use parent values directly (does NOT calculate them automatically)

**What it DOES NOT do:**
- Does NOT calculate parent values from children
- Does NOT auto-populate missing parent values
- Despite being called "total", it doesn't compute anything

**Critical Requirement:**
With `branchvalues="total"`, parent nodes **MUST have numeric values** or rendering will fail silently. Setting a parent value to 0 causes Plotly to fail without error messages or warnings.

**Example of Silent Failure:**
```python
# This will render nothing - no errors, no output
ids = ["ROOT", "A", "B"]
labels = ["All", "Group A", "Group B"]
parents = ["", "ROOT", "ROOT"]
values = [0, 100, 200]  # ROOT value is 0 - silent failure!

fig = go.Treemap(
    ids=ids, labels=labels, parents=parents, values=values,
    branchvalues="total"  # Expects ROOT to have numeric value
)
```

**Correct Implementation:**
```python
# ROOT value calculated from children - renders successfully
group_totals = {"A": 100, "B": 200}
root_total = sum(group_totals.values())  # 300

ids = ["ROOT", "A", "B"]
labels = ["All", "Group A", "Group B"]
parents = ["", "ROOT", "ROOT"]
values = [root_total if root_total > 0 else 1, 100, 200]  # ROOT has numeric value

fig = go.Treemap(
    ids=ids, labels=labels, parents=parents, values=values,
    branchvalues="total"  # Works because ROOT value is 300
)
```

#### `maxdepth` Parameter
Controls the **maximum visible depth** in the treemap hierarchy:
- `maxdepth=1` - Shows only ROOT level (prevents drill-down to any children)
- `maxdepth=2` - Shows up to 2 levels (ROOT → Groups, can drill to see Groups and their children)
- `maxdepth=3` - Shows up to 3 levels, etc.

**Important:** `maxdepth` is not an "initial depth" setting. It's a hard limit. With `maxdepth=1`, users cannot drill down at all.

For hierarchical drill-down experiences (showing top level initially, then showing children on click):
- Set `maxdepth` to accommodate full hierarchy depth
- Plotly automatically handles drill-down visualization
- Users navigate with pathbar or by clicking tiles

#### Pathbar Navigation
```python
pathbar=dict(visible=True)  # Show breadcrumb navigation
```
Enables click-based navigation showing the path to current view, making drill-down exploration intuitive.

### Customer Groups Treemap Example

The customer groups treemap uses a 3-level hierarchy:

```
ROOT ("All Groups")
├── Customer Group A
│   ├── Customer A1
│   ├── Customer A2
├── Customer Group B
│   ├── Customer B1
    └── Customer B2
```

**Configuration:**
- `branchvalues="total"` - Parent values are sums of children
- `maxdepth=2` - Allows drill-down to show customer groups and their customers
- `pathbar=dict(visible=True)` - Breadcrumb navigation for easier UX

**Data Structure:**
```python
ids = ["ROOT", "group_A", "customer_A_A1", "customer_A_A2", ...]
labels = ["All Groups", "A", "A1", "A2", ...]
parents = ["", "ROOT", "group_A", "group_A", ...]
values = [300, 100, 50, 50, ...]  # ROOT = sum of all groups
```

### Debugging Treemap Rendering Issues

**Symptom: Treemap not visible (takes space but no rendering)**
- **Cause:** Parent node values are 0 or invalid with `branchvalues="total"`
- **Solution:** Ensure parent values are calculated from children and never zero

**Symptom: Can't see drill-down children**
- **Cause:** `maxdepth` too low or hierarchy structure wrong
- **Solution:** Check `maxdepth` value and verify parent-child relationships in ids/parents arrays

**Symptom: Both levels always visible (no drill-down)**
- **Cause:** Misunderstanding of `maxdepth` - it controls maximum, not initial depth
- **Solution:** This is expected behavior; Plotly auto-handles which level shows based on user interaction

### References
- [Plotly Treemap Documentation](https://plotly.com/python/treemaps/)
- [Plotly Graph Objects Treemap](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Treemap.html)

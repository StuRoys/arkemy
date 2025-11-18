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

**Symptom: Hovertemplate shows random/incorrect values**
- **Cause:** Customdata array order doesn't match ids array order
- **Solution:** See "Customdata and Hovertemplate" section below

## Customdata and Hovertemplate

### Critical Requirement: Index Alignment

When using `customdata` with `hovertemplate` in treemaps (or any Plotly chart), **the customdata array must be in the exact same order as the ids array**. Plotly uses array indices to match nodes with their customdata.

**How it Works:**
```python
ids = ["ROOT", "group_A", "customer_1", "customer_2"]
customdata = [
    [0, 0, 0],           # customdata[0] for ids[0] ("ROOT")
    [100, 80, 20],       # customdata[1] for ids[1] ("group_A")
    [50, 40, 10],        # customdata[2] for ids[2] ("customer_1")
    [50, 40, 10]         # customdata[3] for ids[3] ("customer_2")
]

# When hovering over "group_A", Plotly looks up:
# - Find index of "group_A" in ids → index 1
# - Use customdata[1] → [100, 80, 20]
# - Apply hovertemplate: "Hours: %{customdata[0]}" → "Hours: 100"
```

### Common Pitfall: Building Customdata Out of Order

**WRONG - Customdata built separately, order may not match:**
```python
ids = ["ROOT"]
customdata = []

# Add groups
for group in groups:
    ids.append(f"group_{group}")
    # ... later ...

# Add customers
for customer in customers:
    ids.append(f"customer_{customer}")

# Build customdata separately (wrong order!)
customdata.append([0] * 19)  # ROOT
for group in group_ids.keys():  # Dictionary iteration order != insertion order
    customdata.append(calculate_group_data(group))
for customer in customers:
    customdata.append(calculate_customer_data(customer))
```

**Result:** Hovering shows random values because `customdata[i]` doesn't correspond to `ids[i]`.

### Correct Implementation: ID-to-Customdata Mapping

**RIGHT - Use dictionary to guarantee alignment:**
```python
ids = ["ROOT"]
labels = ["All Groups"]
parents = [""]
values = [0]

# Build ids list first
for group in groups:
    ids.append(f"group_{group}")
    # ...

for customer in customers:
    ids.append(f"customer_{customer}")
    # ...

# Build customdata using a map
customdata_map = {}
customdata_map["ROOT"] = [0] * 19

for group in groups:
    customdata_map[f"group_{group}"] = calculate_group_metrics(group)

for customer in customers:
    customdata_map[f"customer_{customer}"] = calculate_customer_metrics(customer)

# Construct final customdata in exact same order as ids
final_customdata = [customdata_map.get(id_, [0]*19) for id_ in ids]

# Now customdata[i] is guaranteed to match ids[i]
fig = go.Treemap(
    ids=ids,
    labels=labels,
    parents=parents,
    values=values,
    customdata=final_customdata,
    hovertemplate="<b>%{label}</b><br>Hours: %{customdata[0]:,.1f}<extra></extra>"
)
```

### Hovertemplate Syntax

```python
hovertemplate = """
<b>%{label}</b><br>
Hours worked: %{customdata[0]:,.1f}<br>
Fee: %{customdata[6]:,.0f}<br>
Profit margin: %{customdata[18]:,.1f}%
<extra></extra>
"""
```

**Key Points:**
- `%{label}` - Node label from labels array
- `%{customdata[i]}` - Access customdata array at index i
- `:,.1f` - Format with thousand separators and 1 decimal
- `<extra></extra>` - Hide secondary hover box

### Debugging Customdata Issues

**Verify alignment:**
```python
print("ID to Customdata mapping:")
for i, id_ in enumerate(ids):
    print(f"  {i}: {id_} → customdata[0]={final_customdata[i][0]}")
```

**Test with simple data:**
```python
# Temporarily use simple test values
customdata = [[i] * 19 for i in range(len(ids))]
# Hover should show index numbers matching node position
```

**Check for dictionary iteration issues:**
- Python 3.7+ maintains dict insertion order, but be explicit
- Use list comprehension over ids list, not dictionary keys
- Never assume dictionary iteration order matches insertion order in older Python

### References
- [Plotly Treemap Documentation](https://plotly.com/python/treemaps/)
- [Plotly Graph Objects Treemap](https://plotly.com/python-api-reference/generated/plotly.graph_objects.Treemap.html)
- [Plotly Hovertemplate Reference](https://plotly.com/python/hover-text-and-formatting/)

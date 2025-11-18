# format_func Pattern for Display Label Translation

## What is format_func?

`format_func` is a **native Streamlit parameter** available in `st.selectbox` and other widgets. It transforms how option values are displayed to the user without changing the underlying value stored by the widget.

**Key concept**: The widget stores technical values internally, but shows user-friendly labels in the UI.

## Why Use format_func?

**Problem**: You need to display user-friendly labels (e.g., "Prosjektfase") but use technical column names (e.g., "project_tag_2") in your data operations.

**Bad Solution** ❌:
```python
# Store display labels, then reverse lookup to find technical value
display_labels = ["Prosjektfase", "TEAM", "Offentlig eller privat"]
selected_label = st.selectbox("Select", display_labels)
# Now you need complex reverse lookup to get column name
column_name = [k for k, v in mapping.items() if v == selected_label][0]
```

**Good Solution** ✅:
```python
# Store technical values, display friendly labels
column_names = ["project_tag_2", "project_tag_4", "project_tag_1"]
selected_column = st.selectbox(
    "Select",
    options=column_names,
    format_func=lambda col: label_mapping.get(col, col)
)
# selected_column is already the technical value you need!
```

## Implementation in Arkemy

### Location
[charts/project_type_charts.py:48-54](charts/project_type_charts.py#L48-L54)

### Code
```python
selected_tag_column = st.selectbox(
    label="",
    options=available_tags,  # ['project_tag_1', 'project_tag_2', ...]
    format_func=lambda col: tag_columns_with_labels.get(col, col),
    index=0,
    key=get_widget_key("tag_selector")
)
```

### What Happens
1. **options**: List of technical column names
   - `['project_tag_1', 'project_tag_2', 'project_tag_3', 'project_tag_4']`

2. **format_func**: Lambda that translates for display
   - `lambda col: tag_columns_with_labels.get(col, col)`
   - For `'project_tag_1'` → returns `'Offentlig eller privat'`
   - For `'project_tag_2'` → returns `'Prosjektfase'`
   - For missing keys → returns the column name (fallback)

3. **Result**:
   - Widget stores: `'project_tag_2'` (technical value)
   - User sees: `'Prosjektfase'` (friendly label)
   - No reverse lookup needed!

## Complete Data Flow

### Step 1: Extract Labels from Parquet
**File**: [utils/unified_data_loader.py:171-172](utils/unified_data_loader.py#L171-L172)
```python
# During data load
tag_mappings = extract_tag_mappings(df)
st.session_state['tag_mappings'] = tag_mappings
```

**Result**:
```python
{
    'project_tag_1': 'Offentlig eller privat',
    'project_tag_2': 'Prosjektfase',
    'project_tag_3': 'Prosjekttagger',
    'project_tag_4': 'TEAM'
}
```

### Step 2: Retrieve Mappings in UI
**File**: [charts/project_type_charts.py:33](charts/project_type_charts.py#L33)
```python
tag_mappings = st.session_state.get('tag_mappings', {})
```

### Step 3: Build Column-to-Label Dict
**File**: [charts/project_type_charts.py:36](charts/project_type_charts.py#L36)
```python
tag_columns_with_labels = get_project_tag_columns_with_labels(filtered_df, tag_mappings)
```

**Result**: Same as `tag_mappings` but only includes columns that exist in dataframe

### Step 4: Use in Selectbox
**File**: [charts/project_type_charts.py:48-54](charts/project_type_charts.py#L48-L54)
```python
selected_tag_column = st.selectbox(
    label="",
    options=available_tags,
    format_func=lambda col: tag_columns_with_labels.get(col, col),
    index=0,
    key=get_widget_key("tag_selector")
)
```

### Step 5: Get Display Label for Chart Titles
**File**: [charts/project_type_charts.py:71](charts/project_type_charts.py#L71)
```python
selected_tag_display_name = get_tag_display_name(selected_tag_column, tag_mappings)
```

### Step 6: Use Both Values
```python
# Use technical column name for data operations
project_type_agg = aggregate_by_project_tag(filtered_df, tag_column=selected_tag_column)

# Use display label for UI
fig = px.treemap(
    project_type_agg,
    path=[selected_tag_column],  # Technical name for data
    title=f"{selected_tag_display_name} Hours worked Distribution"  # Label for UI
)
```

## Benefits

### 1. Simplicity
- No complex reverse lookups
- No manual session state management
- No callback functions needed
- Widget value IS the technical value you need

### 2. Performance
- `format_func` is evaluated efficiently by Streamlit
- No list comprehensions on every rerun
- Clean, maintainable code

### 3. Reliability
- Widget state managed by Streamlit natively
- Type-safe: widget value is always a column name
- Fallback behavior built-in (returns column name if label missing)

### 4. Separation of Concerns
- Display logic: `format_func` handles translation
- Data logic: Uses technical column names
- No mixing of concerns

## Pattern Template

Use this template for any future display label mapping needs:

```python
# 1. Get technical values
technical_values = get_technical_values()  # ['value_1', 'value_2', ...]

# 2. Get label mapping
label_mapping = get_label_mapping()  # {'value_1': 'Label 1', 'value_2': 'Label 2'}

# 3. Create selectbox with format_func
selected_value = st.selectbox(
    "Choose option",
    options=technical_values,
    format_func=lambda val: label_mapping.get(val, val),  # Fallback to value if no label
    key="unique_widget_key"
)

# 4. Get display label if needed for UI
display_label = label_mapping.get(selected_value, selected_value)

# 5. Use technical value for data operations
result = process_data(df, column=selected_value)

# 6. Use display label for UI text
st.write(f"Showing results for {display_label}")
```

## Common Pitfalls to Avoid

### ❌ Don't: Store display labels as options
```python
# BAD - Now you need reverse lookup
labels = ["Label 1", "Label 2"]
selected_label = st.selectbox("Choose", labels)
value = reverse_lookup(selected_label, mapping)  # Complex!
```

### ❌ Don't: Use complex callbacks
```python
# BAD - Unnecessary complexity
def on_change():
    label = st.session_state['widget_key']
    st.session_state['actual_value'] = reverse_lookup(label)

selected = st.selectbox("Choose", labels, on_change=on_change)
```

### ❌ Don't: Try to modify widget value
```python
# BAD - Fighting Streamlit's model
selected_label = st.selectbox("Choose", labels)
# Trying to convert to value elsewhere in code
# This creates confusion and bugs
```

### ✅ Do: Use format_func with technical values
```python
# GOOD - Simple and clean
selected_value = st.selectbox(
    "Choose",
    options=technical_values,
    format_func=lambda v: mapping.get(v, v)
)
# selected_value is already what you need!
```

## Testing the Implementation

When testing format_func implementation:

1. **Verify dropdown displays labels**: User should see "Prosjektfase", not "project_tag_2"
2. **Verify widget stores technical value**: `selected_tag_column` should be "project_tag_2"
3. **Verify data operations work**: Charts and tables should aggregate by correct column
4. **Verify UI shows labels**: Chart titles should show "Prosjektfase"
5. **Test fallback**: If label missing, should show column name without errors

## Related Files

- **Tag extraction**: [utils/tag_manager.py](utils/tag_manager.py)
- **Data loading**: [utils/unified_data_loader.py:171-172](utils/unified_data_loader.py#L171-L172)
- **UI implementation**: [charts/project_type_charts.py:48-54](charts/project_type_charts.py#L48-L54)
- **Helper function**: [utils/processors.py - get_project_tag_columns_with_labels()](utils/processors.py)
- **Guidelines**: [~/.claude/streamlit-guidelines.md](~/.claude/streamlit-guidelines.md)

## Streamlit Documentation

Official Streamlit docs for format_func:
- [st.selectbox API Reference](https://docs.streamlit.io/library/api-reference/widgets/st.selectbox)

## Summary

**format_func is the correct Streamlit pattern for display label translation.**

Key principles:
- Options = technical values (what you need in code)
- format_func = display transformation (what user sees)
- Widget value = technical value (no translation needed)
- Simple, clean, maintainable

When in doubt, use `format_func` instead of complex state management or reverse lookups.

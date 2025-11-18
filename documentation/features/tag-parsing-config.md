# Branch: tag-parsing-config

## Overview
This branch implements support for **multiple project tag dimensions** with **user-friendly label translation** in the Project tags analysis tab. Users can now dynamically switch between different tag categorizations, and see client-defined labels instead of technical column names.

## Key Changes

### 1. Tag Translation System (`utils/tag_manager.py`) - NEW FILE

#### Purpose
Extracts and manages user-friendly tag labels from parquet metadata row for display in UI.

#### Key Functions
- **`extract_tag_mappings(df)`**: Extracts tag labels from metadata row (`record_type='tag_group_mapping'`)
- **`get_tag_display_name(tag_column, tag_mappings)`**: Translates column name to display label with fallback

#### Data Source
Tag labels are embedded in the parquet file as a metadata row:
```python
# Metadata row structure (from ETL)
record_type: 'tag_group_mapping'
project_tag_1: 'Offentlig eller privat'
project_tag_2: 'Prosjektfase'
project_tag_3: 'Prosjekttagger'
project_tag_4: 'TEAM'
# ... all other columns are null
```

#### Storage
- Extracted on data load in `unified_data_loader.py`
- Stored in `st.session_state['tag_mappings']`
- Used throughout UI for display

### 2. Data Processing Layer (`utils/processors.py`)

#### New Functions

**`get_project_tag_columns(df)`**
- **Purpose**: Detect all project tag columns in the dataframe
- **Behavior**:
  - Handles legacy `project_tag` column (single tag)
  - Handles indexed `project_tag_1`, `project_tag_2`, `project_tag_3`, etc.
  - Returns columns in order: `['project_tag', 'project_tag_1', 'project_tag_2', ...]`
- **Usage**: Called in `project_type_charts.py` to populate tag selector dropdown

**`get_project_tag_columns_with_labels(df, tag_mappings)`** - NEW
- **Purpose**: Get project tag columns with their display labels
- **Returns**: `{'project_tag_1': 'Prosjektfase', 'project_tag_2': 'TEAM', ...}`
- **Usage**: Provides mapping for `format_func` in selectbox widgets

#### Refactored Function: `aggregate_by_project_tag(df, tag_column="project_tag")`
- **Old name**: `aggregate_by_project_type()` (deprecated, kept for backward compatibility)
- **New signature**: Accepts `tag_column` parameter to specify which tag dimension to aggregate by
- **Backward compatibility**: Default parameter `tag_column="project_tag"` maintains compatibility with legacy data
- **Returns**: Aggregated dataframe with standard metrics (hours, billable hours, fee, cost, profit, rates)

#### Deprecated Function: `aggregate_by_project_type()`
- Kept as wrapper around `aggregate_by_project_tag()` for backward compatibility
- Do NOT use in new code; use `aggregate_by_project_tag()` directly

### 3. Data Loading Layer (`utils/unified_data_loader.py`)

#### Tag Mapping Extraction
- Calls `extract_tag_mappings(df)` during data load
- Stores result in `st.session_state['tag_mappings']`
- Metadata row is automatically filtered out (not in schema record types)
- Debug mode shows extracted mappings

### 4. UI Layer (`charts/project_type_charts.py`)

#### Updated Tab Name
- Changed in `ui/dashboard.py` line 153: "Typologies" → "Project tags"

#### 3-Column Control Layout
Three dropdowns in a single row, no labels (self-evident):
1. **Column 1 - Tag Selector** (conditional)
   - Only shown if multiple tags exist (len > 1)
   - Auto-selects first tag if only one available
   - Uses `get_project_tag_columns()` to populate options
   - **Uses `format_func` for label display** (Streamlit best practice)
   - Widget value = column name, user sees = friendly label

2. **Column 2 - Metric Selector**
   - Standard metrics: Hours worked, Billable hours, Fee, Cost, Profit, etc.
   - Uses existing `get_metric_options()` function

3. **Column 3 - Visualization Type**
   - Dropdown (changed from radio buttons)
   - Options: Treemap, Bar chart

#### Label Translation Implementation
Uses Streamlit's native `format_func` pattern for clean, simple translation:
```python
selected_tag_column = st.selectbox(
    label="",
    options=available_tags,  # ['project_tag_1', 'project_tag_2', ...]
    format_func=lambda col: tag_columns_with_labels.get(col, col),
    index=0,
    key=get_widget_key("tag_selector")
)
```

Benefits:
- Widget stores actual column names (technical values)
- User sees friendly labels (Norwegian names)
- No complex reverse lookups or session state management
- Simple, maintainable code

#### Dynamic Chart Rendering
- **Chart titles** use display labels: `f"{selected_tag_display_name} {selected_metric} Distribution"`
- **Chart axes** use column names: `path=[selected_tag_column]` for treemap, `x=selected_tag_column` for bar chart
- **Data table heading** shows display label: `st.subheader(f"Data for {selected_tag_display_name}")`

#### Conditional Bar Chart Slider
- **Only appears** if dataset has 10+ items
- **Auto-shows all** if fewer than 10 items
- Label removed (empty string) for cleaner UI

### 3. Supporting Files

#### `charts/summary_charts.py` - `get_project_type_insights()`
- Updated to use `get_project_tag_columns()` and `aggregate_by_project_tag()`
- Automatically uses first available tag column for summary insights
- Simplified logic by leveraging generic aggregation function

## Implementation Pattern

When the user opens the Project tags tab:

```
1. Call get_project_tag_columns(filtered_df)
   ↓ Returns: ['project_tag_1', 'project_tag_2', 'project_tag_3', 'project_tag_4']

2. User selects tag dimension from dropdown (col1)
   ↓ selected_tag_column = 'project_tag_2'

3. User selects metric from dropdown (col2)
   ↓ selected_metric = 'Fee'

4. User selects visualization from dropdown (col3)
   ↓ visualization_type = 'Treemap'

5. Call aggregate_by_project_tag(filtered_df, tag_column='project_tag_2')
   ↓ Returns aggregated data by project_tag_2

6. Render chart with selected dimensions
   ↓ Treemap showing Fee distribution across project_tag_2 values
```

## Data Requirements

### Input Data
- Dataframe with one or more `project_tag*` columns
- Each row must have a tag value (or NaN, which is handled)
- Standard metrics columns: `hours_used`, `hours_billable`, `fee_record`, `cost_record`, `profit_record`

### Output
- Aggregated dataframe grouped by selected tag column
- Columns: tag column, hours_used, hours_billable, Non-billable hours, Billability %, Fee, Total cost, Total profit, Billable rate, Effective rate, Profit margin %

## Backward Compatibility

✅ **Legacy data with only `project_tag` column still works**
- `get_project_tag_columns()` returns `['project_tag']`
- No tag selector shown (only one option)
- Everything uses `project_tag` by default

✅ **Old code calling `aggregate_by_project_type()` still works**
- Function is a wrapper around `aggregate_by_project_tag(df, tag_column="project_tag")`
- No breaking changes

## Testing Notes

Test with the provided parquet file:
```bash
/Users/roark/code/arkemy_app/arkemy/data/pka/pka_time_records_2007-01-01_2025-10-31.parquet
```

This file contains 4 tag columns: `project_tag_1`, `project_tag_2`, `project_tag_3`, `project_tag_4`

**Test scenarios:**
1. Open Project tags tab → selector dropdown appears
2. Select different tags → chart updates instantly
3. Select different metrics → chart updates
4. Select different visualizations → chart updates
5. Bar chart with 66+ items → slider appears and works
6. Bar chart with <10 items → no slider shown

## Label Translation Architecture

### ✅ IMPLEMENTED: Parquet Metadata Approach

Tag labels are embedded directly in the parquet file as a metadata row, eliminating the need for separate configuration files.

**Implementation**:
1. **ETL adds metadata row** with `record_type='tag_group_mapping'`
2. **App extracts labels** during data load via `extract_tag_mappings()`
3. **Labels stored** in session state for UI use
4. **UI displays** friendly labels via `format_func`

**Benefits over config file approach**:
- ✅ Single source of truth (data + metadata in one file)
- ✅ No file management overhead
- ✅ Metadata travels with data automatically
- ✅ Simpler deployment and backups
- ✅ Zero configuration required

## Other Future Enhancements

- Support for other tag types (person_tag_*, customer_tag_*)
- Multi-select tags (analyze combinations)
- Tag hierarchy/grouping

## Files Modified

| File | Changes |
|------|---------|
| **NEW** `utils/tag_manager.py` | Tag mapping extraction and label translation utilities |
| `utils/processors.py` | Added `get_project_tag_columns()`, `get_project_tag_columns_with_labels()`, renamed function, kept backward compat |
| `utils/unified_data_loader.py` | Extract and store tag mappings on data load |
| `charts/project_type_charts.py` | 3-column layout, label translation via `format_func`, static widget keys |
| `charts/project_charts.py` | Fixed widget keys (removed dynamic counter) |
| `charts/summary_charts.py` | Updated to use new functions |
| `ui/dashboard.py` | Tab label: "Typologies" → "Project tags" |
| `CLAUDE.md` | Added Streamlit guidelines reference, simplified docs |

## Summary

This branch successfully implements:
- ✅ Multiple project tag dimension support
- ✅ User-friendly label translation from parquet metadata
- ✅ Clean UI with `format_func` (Streamlit best practice)
- ✅ Backward compatibility with legacy single-tag data
- ✅ Static widget keys for stable state management
- ✅ Comprehensive Streamlit guidelines for future development

**Key Achievement**: Tag labels embedded in parquet metadata eliminate need for separate config files, simplifying data management and deployment.

## Merge Status

Branch: `tag-parsing-config`
Status: **Ready for merge to main**
Testing: ✅ Tested with pka client data (4 project tags with Norwegian labels)

## Notes for Future Development

1. **Do not modify function names** without updating all call sites
2. **The tag selector is conditional** - test with both single and multiple tags
3. **Widget keys are static** - do not add dynamic counters
4. **Slider appears conditionally** - check the 10+ item threshold
5. **Backward compatibility is critical** - always test with legacy `project_tag` column
6. **Use `format_func`** for any future display label mapping needs
7. **Follow Streamlit guidelines** in `~/.claude/streamlit-guidelines.md`

# Session State Management

**When to use this guide**: Debugging state issues, adding new features that need session state, understanding global data access, or troubleshooting page navigation.

**Reference this file with**: `@documentation/architecture/session-state-management.md`

---

## Overview

Streamlit session state (`st.session_state`) provides persistent storage across page reruns and navigation. Arkemy uses session state for:
- Global dataset storage
- User filter selections
- UI persistence (tab indices, selections)
- Feature availability flags
- Configuration settings

## Critical Session State Variables

### Data Storage

**`transformed_df`** (DataFrame)
- **Contains**: Actual time tracking data (time_records only)
- **Populated by**: Dataset Selection page or auto-load in production
- **Used by**: Analytics Dashboard, Cashflow Analysis, all data-dependent pages
- **Type**: Pandas DataFrame with unified schema
- **Cleared by**: Dataset reset button (localhost only)

**`transformed_planned_df`** (DataFrame)
- **Contains**: Planned hours/forecasting data (planned_records only)
- **Populated by**: Dataset Selection page or auto-load in production
- **Used by**: Project Report, Project Snapshot (for actual vs planned comparison)
- **Type**: Pandas DataFrame with unified schema
- **Cleared by**: Dataset reset button (localhost only)

**`csv_loaded`** (bool)
- **Purpose**: Flag indicating actual time data is loaded
- **Default**: `False`
- **Set to True**: After successful parquet/CSV load
- **Used by**: Conditional navigation in `main.py`
- **Critical**: Controls whether Dataset Selection page is shown (localhost mode)

**`planned_csv_loaded`** (bool)
- **Purpose**: Flag indicating planned data is loaded
- **Default**: `False`
- **Set to True**: After successful planned records load
- **Used by**: Features that compare actual vs planned

### Global Dataset Selection (Localhost Mode)

**`loaded_file_path`** (str)
- **Purpose**: Track which parquet file is currently loaded
- **Used by**: Dataset reset functionality, debugging
- **Example**: `/Users/roark/data/client_data_NOK.parquet`

**`coworker_available`** (bool)
- **Purpose**: Flag if coworker CSV file exists in dataset directory
- **Controls**: Whether Coworker Report page appears in navigation
- **Set by**: Dataset Selection page during CSV scanning

**`coworker_csv_path`** (str)
- **Purpose**: Path to coworker CSV file (if available)
- **Used by**: Coworker Report page to load data

**`sqm_available`** (bool)
- **Purpose**: Flag if hrs/sqm/phase CSV file exists in dataset directory
- **Controls**: Whether Hrs/m²/Phase page appears in navigation
- **Set by**: Dataset Selection page during CSV scanning

**`sqm_csv_path`** (str)
- **Purpose**: Path to hrs/sqm/phase CSV file (if available)
- **Used by**: Hrs/SQM/Phase page to load data

**`data_loading_attempted`** (bool)
- **Purpose**: Track if dataset loading has been attempted
- **Prevents**: Repeated auto-load attempts
- **Reset by**: Dataset reset button

### Currency and Configuration

**`currency`** (str)
- **Purpose**: Selected currency code for formatting
- **Default**: `'nok'` (Norwegian Krone)
- **Values**: Any supported currency code (50+ currencies)
- **Set by**: Filename detection or manual selection in Admin page
- **Used by**: Currency formatter throughout application

**`currency_selected`** (bool)
- **Purpose**: Flag if currency has been explicitly selected
- **Prevents**: Overwriting user's manual currency selection

**`data_version`** (str)
- **Purpose**: Dataset version selector
- **Values**: `"adjusted"` or `"regular"`
- **Default**: `"adjusted"` (preferred when available)
- **Used by**: Cache signatures, data loading
- **UI Control**: Sidebar toggle in Admin page

### Feature-Specific State

**`period_report_project_data`** (DataFrame)
- **Purpose**: Transformed project data for Project Report feature
- **Populated by**: `transform_dataframes_to_project_report()` function
- **Used by**: Project Report and Project Snapshot pages
- **Format**: Project Report CSV schema (not unified schema)

**`project_data`** (DataFrame)
- **Purpose**: Backward compatibility alias for `period_report_project_data`
- **Note**: Both point to same data, kept for legacy code support

**`tag_mappings`** (dict)
- **Purpose**: Tag parsing configuration from loaded dataset
- **Contains**: Tag field → project attribute mappings
- **Used by**: Tag-based filtering and analysis
- **Optional**: Not all datasets include tag mappings

### Reference Data

**`person_reference_df`** (DataFrame)
- **Purpose**: Person master data (names, IDs, metadata)
- **Used by**: Person-based reports and filtering
- **Optional**: Not always available

**`project_reference_df`** (DataFrame)
- **Purpose**: Project master data (names, IDs, metadata)
- **Used by**: Project-based reports and filtering
- **Optional**: Not always available

### Capacity Planning State

**`schedule_loaded`** (bool)
- **Purpose**: Flag if schedule data is loaded
- **Used by**: Capacity planning features

**`schedule_df`** (DataFrame)
- **Purpose**: Schedule data for capacity planning

**`absence_loaded`** (bool)
- **Purpose**: Flag if absence data is loaded

**`absence_df`** (DataFrame)
- **Purpose**: Absence/vacation data for capacity planning

**`capacity_config`** (dict)
- **Purpose**: Capacity planning configuration

**`capacity_summary_loaded`** (bool)
- **Purpose**: Flag if capacity summary is loaded

**`capacity_summary_df`** (DataFrame)
- **Purpose**: Capacity summary data

### Navigation and UI State

**`active_tab`** (int)
- **Purpose**: Track active tab index in tabbed interfaces
- **Default**: `0` (first tab)
- **Used by**: Multi-tab pages to persist selection across reruns

## Session State Initialization

### Where State is Initialized

**`main.py`** (Lines 73-104)
- Initializes all global session state variables
- Runs on every app startup
- Sets defaults for all critical variables

### Initialization Pattern

```python
if 'variable_name' not in st.session_state:
    st.session_state.variable_name = default_value
```

**Why this pattern?**
- Only initializes if variable doesn't exist
- Preserves existing values across reruns
- Prevents overwriting user data

## Global Dataset Selection System

### How It Works

**1. Startup** (`main.py:111-116`)
```python
if is_localhost() and not st.session_state.csv_loaded:
    # Show only Dataset Selection page
    pages = [st.Page("pages/0_Dataset_Selection.py", ...)]
```

**2. Dataset Selection** (`pages/0_Dataset_Selection.py`)
- User selects client and parquet file
- Loads data via `UnifiedDataLoader`
- Stores in `transformed_df` and `transformed_planned_df`
- Sets `csv_loaded = True`
- Scans for optional CSV files
- Sets availability flags
- Triggers rerun

**3. Post-Load Navigation** (`main.py:117-133`)
```python
else:
    # Show all available pages
    pages = [Analytics Dashboard, Project Report, ...]

    # Conditionally add CSV-dependent pages
    if st.session_state.get('coworker_available', False):
        pages.insert(1, Coworker Report)
```

**4. Data Access in Pages**
- Analytics Dashboard: Uses `transformed_df` directly
- Project Report: Transforms `transformed_df` to project format
- Cashflow Analysis: Uses `transformed_df` directly
- Coworker Report: Loads from `coworker_csv_path`

### Dataset Reset Flow

**Trigger** (`utils/dataset_reset.py:render_dataset_indicator()`):
- Button click in sidebar (localhost only)

**Clear** (`utils/dataset_reset.py:clear_dataset_session_state()`):
- Clears all data variables
- Clears file paths
- Resets currency to default
- Clears tag mappings
- Clears reference data
- Clears CSV availability flags
- Resets data loading flag

**Rerun**:
- Returns to Dataset Selection page
- User selects new dataset
- Cycle repeats

## State Sharing Between Pages

### Pattern 1: Global Read Access

Pages access shared data directly:

```python
# Any page can read global data
df = st.session_state.transformed_df

# Check if data exists first
if st.session_state.get('csv_loaded', False):
    df = st.session_state.transformed_df
    # Process data...
```

### Pattern 2: Transformation and Cache

Pages transform global data into page-specific format:

```python
# Check if already transformed
if st.session_state.project_data is None:
    # Transform from global data
    time_records = st.session_state.transformed_df
    planned_records = st.session_state.transformed_planned_df

    transformed = transform_dataframes_to_project_report(
        time_records, planned_records
    )

    # Cache in session state
    st.session_state.project_data = transformed
```

**Benefits**:
- Transformation happens once
- Subsequent page visits use cached data
- Reduces processing time

### Pattern 3: Filter State Persistence

Filters store selections in session state:

```python
# Store filter selection
selected_project = st.selectbox(
    "Select Project",
    options=projects,
    key="project_filter"  # Auto-saves to session state
)

# Or manually
st.session_state.selected_date_range = (start_date, end_date)
```

## Common Patterns and Best Practices

### Pattern: Safe Data Access

**Always check if data exists before using:**

```python
# Bad: Assumes data exists
df = st.session_state.transformed_df  # Error if not loaded

# Good: Check first
if st.session_state.get('csv_loaded', False):
    df = st.session_state.transformed_df
    # Process data...
else:
    st.error("No data loaded")
    st.stop()
```

### Pattern: Conditional Feature Availability

**Use flags to control feature visibility:**

```python
# In main.py
if st.session_state.get('coworker_available', False):
    pages.append(st.Page("pages/2_Coworker_Report.py", ...))
```

**Prevents**:
- 404 errors from unavailable features
- Broken pages when optional data is missing
- Confusing UI when features aren't supported

### Pattern: Cache Invalidation

**Include version in cache signatures:**

```python
@st.cache_data
def load_data(file_path, data_version):
    # Cache key includes data_version
    # Changing data_version invalidates cache
    return load_parquet(file_path, data_version)
```

**Why**: Prevents stale data when switching between regular/adjusted datasets

## Debugging Session State

### View Current State

```python
# In any page (for debugging)
if st.checkbox("Show Session State"):
    st.write(st.session_state)
```

### Check Specific Variables

```python
# Debug specific variable
st.write("CSV Loaded:", st.session_state.get('csv_loaded', False))
st.write("Data Version:", st.session_state.get('data_version', 'unknown'))
```

### Common Issues

**Data not available in page:**
- Check if `csv_loaded` is True
- Verify `transformed_df` is not None
- Confirm data loading happened before page access

**Page not appearing in navigation:**
- Check availability flags (`coworker_available`, `sqm_available`)
- Verify CSV scanning completed successfully
- Confirm paths are set (`coworker_csv_path`, `sqm_csv_path`)

**Stale data after dataset change:**
- Verify cache invalidation is working
- Check `data_version` is updated
- Confirm session state is cleared on dataset reset

**Filter selections not persisting:**
- Use `key` parameter in widgets
- Store complex selections manually in session state
- Verify keys are unique across pages

## Related Documentation

- Data architecture: [data-architecture.md](data-architecture.md)
- Dataset reset implementation: `utils/dataset_reset.py`
- Global data loading: `pages/0_Dataset_Selection.py`
- Conditional navigation: `main.py` lines 111-133

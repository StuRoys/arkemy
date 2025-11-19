# Data Architecture

**When to use this guide**: Understanding data types, modifying data handling, working with unified schema, or debugging data transformations.

**Reference this file with**: `@documentation/architecture/data-architecture.md`

---

## Core Data Types

### time_record (Actual Hours Worked)

**Purpose**: Track ACTUAL time spent on projects by team members

**Source**: Time tracking systems, timesheets, logged work hours

**Use Cases**:
- Profitability analysis
- Performance tracking
- Billable vs non-billable analysis
- Actual cost calculations

**Key Fields**:
- `hours_used` - Total hours worked on the record
- `hours_billable` - Billable hours within the record
- `billable_rate_record` - Hourly billing rate
- `cost_hour` - Cost per hour for the resource
- `fee_record` - Total revenue/fees generated
- `cost_record` - Total cost incurred
- `profit_record` - Calculated profit (fee - cost)

**Record Identification**:
- `record_type` = `"time_record"`
- Distinguished from planned records in unified files

### planned_record (Future Hours/Fees Planned)

**Purpose**: Track PLANNED/FORECASTED hours and fees for upcoming work

**Source**: Project planning, resource allocation, capacity planning systems

**Use Cases**:
- Workload forecasting
- Resource planning
- Budget comparison (planned vs actual)
- Capacity utilization analysis

**Key Fields**:
- `hours_used` - Planned hours (reuses same column name as time_record)
- `planned_hours` - Explicit planned hours field
- `planned_rate` - Planned hourly rate
- `planned_fee` - Forecasted revenue
- Cost projections

**Record Identification**:
- `record_type` = `"planned_record"`
- Separated from actual records in unified files

## Unified File Architecture

### Why Unified Files?

**Benefits**:
- **Simplified Data Management**: One file instead of multiple sources
- **Consistent Schema**: Same validation rules across both record types
- **Easy Comparison**: Analyze planned vs actual in single dashboard
- **Version Control**: Single source of truth for both actual and forecast data

### Unified File Structure

```
parquet_file
├── time_record rows (record_type = "time_record")
│   ├── Actual hours worked
│   ├── Actual fees collected
│   └── Actual costs incurred
└── planned_record rows (record_type = "planned_record")
    ├── Planned hours to be worked
    ├── Planned fees to be collected
    └── Planned cost projections
```

### Record Type Separation

**Loading Process** (see `utils/unified_data_loader.py`):

1. **Load unified parquet file** - Contains both record types
2. **Split by record_type column**:
   - `time_records_df` = rows where `record_type == "time_record"`
   - `planned_records_df` = rows where `record_type == "planned_record"`
3. **Store in separate session state variables**:
   - `st.session_state.transformed_df` - Actual time records only
   - `st.session_state.transformed_planned_df` - Planned records only

**Why Separate After Loading?**
- Different analysis needs (actual vs forecast)
- Different aggregation patterns
- Different UI visualizations
- Some pages only need actual data (Analytics Dashboard, Cashflow)
- Some pages need both (Project Report, Project Snapshot)

## Schema Management

### Schema-Driven System

**Central Schema**: `utils/arkemy_schema.yaml`

**What the Schema Defines**:
- Field names and data types
- Required vs optional fields per record type
- Validation rules
- Type coercion rules

**Schema-Driven Benefits**:
- No code changes needed for schema updates
- Consistent validation across all data loading
- Self-documenting data structure
- Easy to add new record types or fields

### Schema Validation

**Validation Process**:
1. Load parquet file
2. Check for `record_type` column
3. Separate by record type
4. Validate each record type against schema requirements
5. Type coercion based on schema definitions
6. Error reporting for missing required fields

**See**: `utils/schema_manager.py` for implementation

## Data Flow Patterns

### Pattern 1: Direct Usage (Analytics Dashboard, Cashflow)

```
Unified Parquet
    ↓
Load & Split by record_type
    ↓
time_records → transformed_df → Use directly in charts
```

**Pages using this pattern**:
- Analytics Dashboard (`pages/1_Analytics_Dashboard.py`)
- Cashflow Analysis (`pages/7_Cashflow_Analysis.py`)

**Why**: These pages only analyze actual historical data

### Pattern 2: Transformation (Project Report, Project Snapshot)

```
Unified Parquet
    ↓
Load & Split by record_type
    ↓
time_records + planned_records
    ↓
Transform via transform_dataframes_to_project_report()
    ↓
Project Report Format → Project-specific charts
```

**Pages using this pattern**:
- Project Report (`pages/3_Project_Report.py`)
- Project Snapshot (`pages/6_Project_Snapshot.py`)

**Why**: These pages compare actual vs planned at project level

**Transformation** (`period_processors/project_report.py:transform_dataframes_to_project_report()`):
- Groups by project + month
- Merges actual and planned data
- Renames columns to Project Report expected format
- Fills missing values with 0

### Pattern 3: CSV Loading (Coworker Report, Hrs/SQM/Phase)

```
CSV Files (optional)
    ↓
Load separately if available
    ↓
Domain-specific processing
```

**Files**:
- `*coworker*.csv` - Coworker-specific data
- `*hrs_sqm_phase*.csv` - Square meter analysis data

**Why**: These are optional supplementary datasets with different schemas

## Data Processing Modules

### Core Aggregation (`utils/processors.py`)

Standard aggregation functions following consistent pattern:

```python
def aggregate_by_[domain](df, metric_column):
    # Input validation
    # Group by domain
    # Calculate standard metrics
    # Return consistent column structure
```

**Functions**:
- `aggregate_by_customer()` - Customer-level aggregation
- `aggregate_by_project()` - Project-level aggregation
- `aggregate_by_person()` - Person-level aggregation
- `aggregate_by_tag()` - Tag-level aggregation
- More domain-specific aggregations...

**Standard Metrics**:
- Hours worked (total hours used)
- Billable hours
- Fee (revenue)
- Cost
- Profit
- Hourly rates (average, effective)

### Filtering System (`utils/filters.py`, `utils/date_filter.py`)

**Multi-Dimensional Filtering**:
- Date ranges (start/end dates)
- Project selection (include/exclude patterns)
- Customer selection (include/exclude patterns)
- Person selection (include/exclude patterns)
- Tag filtering

**Filter Integration**:
Charts receive pre-filtered data via `render_sidebar_filters()` which applies all active filters and returns both filtered dataframes and filter settings for display.

## Currency System

### Multi-Currency Support

**Built-in**: 50+ currencies with proper formatting

**Features**:
- Symbol positioning (prefix vs suffix)
- Locale-specific separators (comma vs period)
- Thousands separators
- Decimal places control

**Currency Detection**:
1. **Filename detection**: Extract currency code from filename (e.g., `data_NOK.parquet` → NOK)
2. **Manual selection**: Admin page currency selector
3. **Default**: Norwegian Krone (NOK)

**Storage**: `st.session_state.currency`

**Formatting**: `utils/currency_formatter.py`

## Dataset Versioning

### Dual Dataset System

**Regular Values** (`*_regular.parquet`):
- Standard financial metrics
- Original rates, costs, and profits
- Baseline for comparison

**Adjusted Values** (`*_adjusted.parquet`):
- Modified rates (rate adjustments for special pricing)
- Adjusted costs (cost reallocations or corrections)
- Recalculated profits

**Adjusted Data Columns**:
- `fee_record_adjust` - Adjusted fees/revenue
- `cost_hour_adjust` - Adjusted cost per hour
- `cost_record_adjust` - Adjusted total cost
- `profit_hour_adjust` - Adjusted profit per hour
- `profit_record_adjust` - Adjusted total profit

**Dataset Selection**:
- Default preference: Adjusted values (when available)
- Smart fallback to single dataset operation
- Cache invalidation ensures proper dataset switching
- Session state: `st.session_state.data_version` ("adjusted" or "regular")

**UI Control**:
- Sidebar provides clear indication of active dataset
- Toggle between regular and adjusted in Admin page
- Graceful handling of single vs multiple dataset scenarios

## Performance Considerations

### Caching Strategy

**Streamlit Caching**:
- `@st.cache_data` for data loading operations
- Cache signatures include `data_version` parameter to prevent stale data
- Automatic cache invalidation on dataset switches

### Memory Management

**Large Datasets**:
- Garbage collection for large datasets
- Lazy loading: Only load data when needed
- Shared session state across pages reduces redundant loads

### Optimization Tips

**DO**:
- Use vectorized operations on DataFrames
- Group data once, reuse aggregations
- Filter early in the pipeline
- Use appropriate data types (int vs float vs string)

**DON'T**:
- Use `.iterrows()` - extremely slow
- Load same data multiple times
- Create unnecessary DataFrame copies
- Use object dtype when specific type is known

## Related Documentation

- Schema definition: `utils/arkemy_schema.yaml`
- Session state guide: [session-state-management.md](session-state-management.md)
- Data loading implementation: `utils/unified_data_loader.py`
- Processing functions: `utils/processors.py`
- Project Report transformation: `period_processors/project_report.py`

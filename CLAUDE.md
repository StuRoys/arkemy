# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL - READ FIRST
- **Project Location**: `~/code/arkemy/` (standard professional location)
- **NEVER commit directly to main branch** (production-only)
- **Current development**: Work in `develop` branch for safety
- **Test command**: `streamlit run main.py`
- **Repository name**: `arkemy` (clean, professional)

## Common Development Commands

**Run the application:**
```bash
streamlit run main.py
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Architecture Overview

### Application Structure
This is a Streamlit-based data analytics dashboard called "Arkemy" (v1.3.3) for analyzing architecture project data. The app automatically loads Parquet files from the project root and provides comprehensive analytics across multiple business dimensions.

### Core Data Flow
1. **Data Loading**: Automatic Parquet file detection and loading from project root
2. **Validation & Transformation**: Schema validation and data type conversion via `utils/data_validation.py`
3. **Enrichment**: Optional person/project reference data integration
4. **Filtering**: Multi-dimensional filtering system via sidebar
5. **Aggregation**: Domain-specific data aggregation functions in `utils/processors.py`
6. **Visualization**: Modular chart system with consistent styling

### Key Components

**Entry Point:**
- `main.py` - Application bootstrap, auto-loads Parquet files, manages session state

**UI Layer:**
- `ui/dashboard.py` - Main dashboard orchestrator with hierarchical navigation
- `ui/sidebar.py` - Filter interface and data selection
- `ui/parquet_processor.py` - Data loading and transformation pipeline

**Charts Module:**
- Domain-specific chart modules (summary, project, customer, people, etc.)
- Consistent render function pattern: `render_[domain]_tab(filtered_df, aggregate_func, render_chart, get_colors)`
- Each module handles metric selection, aggregation, and multiple visualization types

**Utils Module:**
- `processors.py` - Core aggregation functions (`aggregate_by_customer`, `aggregate_by_project`, etc.)
- `filters.py` / `date_filter.py` - Advanced filtering system with include/exclude patterns
- `data_validation.py` - Schema validation and transformation
- `chart_styles.py` - Centralized styling and formatting
- `currency_formatter.py` - Multi-currency support (50+ currencies)

### Data Processing Patterns

**Standard Aggregation Pattern:**
All aggregation functions follow the same signature and return standardized dataframes:
```python
def aggregate_by_[domain](df, metric_column):
    # Input validation
    # Group by domain
    # Calculate standard metrics (Hours worked, Billable hours, Fee, etc.)
    # Return consistent column structure
```

**Filter Integration:**
Charts receive pre-filtered data via `render_sidebar_filters()` which applies all active filters and returns both filtered dataframes and filter settings for display.

**Planned vs Actual Data:**
The system supports dual data streams - actual timesheet data and planned hours data - with variance calculations and time-based forecasting.

### Session State Management
Critical session state variables:
- `transformed_df` - Main processed dataframe
- `transformed_planned_df` - Planned hours dataframe  
- `currency` - Selected currency for formatting
- `data_version` - Dataset version selector ("adjusted" or "regular")
- Navigation states for UI persistence
- Filter states for sidebar persistence
- `debug_mode` - Toggle for debug information display

### Currency System
Built-in support for 50+ currencies with proper formatting, symbol positioning, and locale-specific separators. Currency detection from filename (e.g., `data_NOK.parquet`) or manual selection.

### Development Notes

**File Naming Convention:**
- Data files should include currency code in filename for auto-detection
- Parquet files are automatically detected in project root
- Dataset versioning: `*_regular.parquet` for regular values, `*_adjusted.parquet` for adjusted values
- App supports single or dual dataset operation with automatic detection

**Adding New Chart Modules:**
1. Create render function following established pattern
2. Add aggregation function to `processors.py` if needed
3. Import and wire into `dashboard.py` navigation
4. Use shared utilities from `chart_styles.py` and `chart_helpers.py`

**Data Requirements:**
- Core schema defined in `data_validation.py` with required columns (Date, Person, Project, Hours worked, etc.)
- Optional planned data schema in `planned_validation.py`
- Reference data for person types and project metadata enrichment
- Adjusted data columns: `fee_record_adjust`, `cost_hour_adjust`, `cost_record_adjust`, `profit_hour_adjust`, `profit_record_adjust`

### Dataset Toggle System
**Dual Dataset Support:**
- Regular values dataset (`*_regular.parquet`) - Standard financial metrics
- Adjusted values dataset (`*_adjusted.parquet`) - Modified rates, costs, and profits
- Default preference: Adjusted values (when available)
- Smart fallback to single dataset operation
- Cache invalidation ensures proper dataset switching
- Debug mode available for troubleshooting data loading

**Key Implementation Notes:**
- Cache signatures include `data_version` parameter to prevent stale data
- Session state management ensures UI persistence across dataset switches
- Sidebar provides clear indication of active dataset
- Graceful handling of single vs multiple dataset scenarios

## Production Deployment

### Environment Configuration
Set the following environment variable to disable debug mode in production:
```bash
export ARKEMY_DEBUG=false
```

### Data Volume Setup
- **Data location**: Mount data files to `/data` directory in production
- **File format**: Parquet files with currency code in filename (e.g., `data_NOK.parquet`)
- **Dataset versioning**: Use `*_regular.parquet` and `*_adjusted.parquet` for dual dataset support
- **Upload functionality**: Manual upload feature can be removed in production - app loads from `/data` automatically

### Security Considerations
- All unsafe HTML usage is for internal styling only (no user input)
- Print statements replaced with proper logging
- Debug mode controlled via environment variable
- No hardcoded credentials or sensitive data exposure

### Performance
- Application uses Streamlit caching for data operations
- Memory management with garbage collection for large datasets
- Automatic Parquet file detection and loading
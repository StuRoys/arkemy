# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL - READ FIRST
- **Project Location**: `~/code/arkemy_app/arkemy`
- **NEVER commit directly to main branch** (production-only)
- **Current development**: Work in `develop` branch for safety
- **Test command**: `streamlit run main.py`
- **Repository name**: `arkemy` (clean, professional)

## 🚀 GIT WORKFLOW - PRODUCTION SAFETY
**User is vibe coding, not a Git person - I handle ALL git operations**

### Branch Strategy
- **main** = Production branch (end users see this)
- **develop** = Development branch (work happens here)
- **ALWAYS work on develop branch unless explicitly merging to production**

### Production Deployment Rules
**ONLY push to main branch when user says EXACTLY:**
- "Ship to production"
- "Deploy to prod" 
- "Push to main"
- "Ready for users"

**ALL other feedback stays on develop:**
- "This works" ≠ production ready
- "Looks good" = keep on develop
- "Test this" = keep on develop
- Any other positive feedback = keep on develop

### My Git Responsibilities
1. **Always check current branch** before any operations
2. **Always work on develop branch** unless merging to main
3. **Test locally first** before any main branch merge
4. **Ask for confirmation** if production intent is unclear
5. **Handle all git commands** - user never needs to know Git
6. **NEVER deploy without explicit permission** - see Deployment Rules below

### Session Start Checklist
- [ ] Check current branch: `git rev-parse --abbrev-ref HEAD`
- [ ] Switch to develop if not already: `git checkout develop`
- [ ] Proceed with development work

## 🚨 DEPLOYMENT RULES - CRITICAL
**Railway deployments automatically commit and push to Git - NEVER deploy without permission**

### Testing Workflow (MANDATORY)
1. **ALWAYS test locally first**: `streamlit run main.py`
2. **Get explicit user permission** before ANY deployment
3. **Separate confirmations required**:
   - "Can I commit these changes to Git?"
   - "Can I deploy to Railway?"

### Railway Deployment Commands
⚠️ **WARNING**: `railway up` automatically commits and pushes to Git repository

**NEVER run these without explicit user permission:**
- `railway up` - Commits, pushes to Git, AND deploys
- `railway deploy` - May also trigger Git operations
- Any Railway deployment command

### Safe Testing Commands
**These are safe to run without permission:**
- `streamlit run main.py` - Local testing only
- `railway logs` - View deployment logs
- `railway status` - Check deployment status
- Git read operations (`git status`, `git log`, etc.)

### Deployment Approval Process
Before ANY Railway deployment:
1. Show user what changes will be committed
2. Ask: "Ready to commit and deploy these changes?"
3. Wait for explicit "yes" or similar confirmation
4. Only then run deployment commands

**REMEMBER**: User wants to test first, commit second, deploy third - all with explicit approval

## Communication Style
- **Chat summaries should be sober, concise and factual**
- **User does not need flair, emojis, or success messages**
- **Avoid phrases like "Perfect!", "Great!", "🚀" or similar excitement**
- **Focus on technical facts and what was accomplished**

## Common Development Commands

**Run the application:**
```bash
streamlit run main.py
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## Railway MCP Commands (Available via MCP Server)

**Project Management:**
- `mcp__railway__list-projects` - List all Railway projects
- `mcp__railway__create-project-and-link` - Create and link a project to current directory

**Service Management:**
- `mcp__railway__list-services` - List services in a project
- `mcp__railway__link-service` - Link a service to current directory
- `mcp__railway__deploy` - Deploy a service
- `mcp__railway__deploy-template` - Deploy a template from Railway's library

**Environment Management:**
- `mcp__railway__create-environment` - Create a new environment
- `mcp__railway__link-environment` - Link an environment to current directory

**Configuration & Variables:**
- `mcp__railway__list-variables` - List environment variables
- `mcp__railway__set-variables` - Set environment variables
- `mcp__railway__generate-domain` - Generate a railway.app domain

**Monitoring:**
- `mcp__railway__get-logs` - Retrieve build or deployment logs

**MCP Server Setup:**
```json
{
  "mcpServers": {
    "railway-mcp-server": {
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"]
    }
  }
}
```

**Note:** If Railway MCP tools are not available, restart Claude Code to reload MCP servers.

## 🎯 BUSINESS PURPOSE - CRITICAL UNDERSTANDING

### What is Arkemy?
Arkemy is a **project profitability analytics dashboard** for architecture firms that need to:
- **Track actual time spent** on projects vs planned hours
- **Analyze project profitability** in real-time
- **Forecast resource allocation** and capacity planning
- **Compare planned vs actual performance** across projects, people, and time periods

### Core Business Concepts:
- **time_records**: ACTUAL hours worked by people on projects (historical data)
- **planned_records**: FUTURE hours/fees planned for projects (forecasting data)
- **Unified Loading**: Both record types loaded from same file for simplified data management

## Architecture Overview

### Application Structure
This is a Streamlit-based project profitability dashboard called "Arkemy" for architecture firms. The app uses a unified schema-driven system to load and analyze both actual time tracking data and planned hours/forecasting data from single parquet files.

### Core Data Flow (Unified Schema-Driven System)
1. **Unified Data Loading**: Single parquet file contains both time_records and planned_records
2. **Record Type Separation**: Uses `record_type` column to distinguish actual vs planned data
3. **Schema-Driven Validation**: YAML schema in `utils/arkemy_schema.yaml` drives all validation
4. **Data Processing**: Separate dataframes for analysis (`transformed_df` + `transformed_planned_df`)
5. **Filtering**: Multi-dimensional filtering system via sidebar
6. **Aggregation**: Domain-specific data aggregation functions in `utils/processors.py`
7. **Analytics**: Compare actual vs planned across multiple business dimensions
8. **Visualization**: Modular chart system with consistent styling

## 📊 DATA TYPES - FUNDAMENTAL UNDERSTANDING

### time_record (Actual Hours Worked)
- **Purpose**: Track ACTUAL time spent on projects by team members
- **Source**: Time tracking systems, timesheets, logged work hours
- **Use Cases**: Profitability analysis, performance tracking, billing
- **Key Fields**: `hours_used`, `hours_billable`, `billable_rate_record`, `cost_hour`

### planned_record (Future Hours/Fees Planned)
- **Purpose**: Track PLANNED/FORECASTED hours and fees for upcoming work
- **Source**: Project planning, resource allocation, capacity planning
- **Use Cases**: Workload forecasting, resource planning, budget comparison
- **Key Fields**: `hours_used` (planned hours), `planned_rate`, cost projections

### Unified File Benefits
- **Simplified Data Management**: One file instead of multiple sources
- **Consistent Schema**: Same validation rules across both record types
- **Easy Comparison**: Analyze planned vs actual in single dashboard

### Key Components

**Entry Point:**
- `main.py` - Application bootstrap, auto-loads Parquet files, manages session state

**UI Layer:**
- `ui/dashboard.py` - Main dashboard orchestrator with hierarchical navigation
- `ui/sidebar.py` - Filter interface and data selection
- `pages/1_Analytics_Dashboard.py` - Unified data loading with hybrid volume/upload support
- `pages/3_Project_Report.py` - Project Report page with period-based analytics

**Data Management:**
- `utils/unified_data_loader.py` - Schema-driven unified data loading system
- `utils/schema_manager.py` - YAML schema management and validation
- `utils/arkemy_schema.yaml` - Central schema definition for all data types

**Charts Module:**
- Domain-specific chart modules (summary, project, customer, people, etc.)
- Consistent render function pattern: `render_[domain]_tab(filtered_df, aggregate_func, render_chart, get_colors)`
- Each module handles metric selection, aggregation, and multiple visualization types

**Project Report Module:**
- `period_processors/project_report.py` - Main Project Report functionality with parquet-to-CSV transformation
- `period_charts/project_hours.py` - Hours analysis charts (actual vs planned)
- `period_charts/project_fees.py` - Fees analysis charts with treemap and bar visualizations
- `period_charts/project_rate.py` - Hourly rate analysis and comparisons
- `period_utils/project_utils.py` - Project-specific utility functions
- `period_utils/chart_utils.py` - Chart creation and formatting utilities

**Utils Module:**
- `processors.py` - Core aggregation functions (`aggregate_by_customer`, `aggregate_by_project`, etc.)
- `filters.py` / `date_filter.py` - Advanced filtering system with include/exclude patterns
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

**Actual vs Planned Analysis:**
The system analyzes two fundamental data types:
- **time_records**: Historical data of actual time spent on projects
- **planned_records**: Forecasting data for planned hours and fees
- **Variance Analysis**: Compare planned vs actual performance across projects, people, and time periods

### Session State Management
Critical session state variables:
- `transformed_df` - **Actual time tracking data** (time_records only)
- `transformed_planned_df` - **Planned hours/forecasting data** (planned_records only)
- `currency` - Selected currency for formatting
- `data_version` - Dataset version selector ("adjusted" or "regular")
- `csv_loaded` - Flag indicating actual time data is loaded
- `planned_csv_loaded` - Flag indicating planned data is loaded
- Navigation states for UI persistence
- Filter states for sidebar persistence
- `debug_mode` - Toggle for debug information display

### Currency System
Built-in support for 50+ currencies with proper formatting, symbol positioning, and locale-specific separators. Currency detection from filename (e.g., `data_NOK.parquet`) or manual selection.

### Development Notes

**File Naming Convention:**
- Data files should include currency code in filename for auto-detection
- Unified parquet files contain both time_records and planned_records
- Dataset versioning: `*_regular.parquet` for regular values, `*_adjusted.parquet` for adjusted values
- App supports single or dual dataset operation with automatic detection

**Adding New Chart Modules:**
1. Create render function following established pattern
2. Add aggregation function to `processors.py` if needed
3. Import and wire into `dashboard.py` navigation
4. Use shared utilities from `chart_styles.py` and `chart_helpers.py`

**Data Requirements:**
- Schema defined in `utils/arkemy_schema.yaml` with field types and validation rules
- Unified files must contain `record_type` column to distinguish time_records vs planned_records
- Required fields vary by record type (see schema for details)
- Adjusted data columns: `fee_record_adjust`, `cost_hour_adjust`, `cost_record_adjust`, `profit_hour_adjust`, `profit_record_adjust`

**Schema Management:**
- Edit `utils/arkemy_schema.yaml` to modify field requirements, add new record types, or change validation rules
- No code changes needed for schema updates - system is fully schema-driven
- Schema supports both required and optional fields per record type

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

## 🏗️ Project Report Feature

### Overview
The Project Report feature provides period-based project analytics with actual vs planned comparisons. It transforms unified parquet data into project-focused visualizations and metrics.

### Key Features
- **Period Filtering**: Month, Quarter, Year, and Year-to-Date filtering options
- **Actual vs Planned Analysis**: Compare worked hours/fees against planned values
- **Multi-View Charts**: Hours, Fees, and Hourly Rate analysis tabs
- **Visualization Types**: Bar charts (monthly trends) and treemaps (project distribution)
- **Clean UI**: Minimal interface without redundant text or headers

### Technical Implementation

**Data Transformation**:
- Transforms unified parquet schema to Project Report CSV format
- Uses existing aggregation functions from `utils/processors.py`
- Maps `fee_record` → "Period Fees Adjusted" (fees already adjusted in ETL)
- Separates time_records (actual) and planned_records (forecasting) data

**Key Mapping**:
```
project_number → Project ID (client-facing identifier)
project_name → Project Name
record_date → Period
hours_used → Period Hours (actual hours worked)
planned_hours → Planned Hours (forecasted hours)
fee_record → Period Fees Adjusted (actual revenue)
planned_fee → Planned Income (forecasted revenue)
```

**Period Filtering Logic**:
- Quarter filter defaults to current year (2025) with fallback to most recent
- Shows helpful warnings when no data exists for selected period
- Validates data availability and guides users to periods with data

**Chart Features**:
- Hover templates with 0 decimal places and thousand separators
- Color scheme: "Used" data gets darker colors, "Planned" gets lighter colors
- Treemap with proper comma formatting for monetary values
- Monthly bar charts with chronological ordering

### File Structure
```
period_processors/
  └── project_report.py          # Main processor with transformation logic
period_charts/
  ├── project_hours.py           # Hours analysis charts
  ├── project_fees.py            # Fees analysis with treemap
  └── project_rate.py            # Hourly rate comparisons
period_utils/
  ├── project_utils.py           # Project utility functions
  └── chart_utils.py             # Chart creation and formatting
pages/
  └── 3_Project_Report.py        # Page entry point
```

### Data Requirements
- Unified parquet file with both time_record and planned_record types
- Required columns: record_type, project_number, project_name, record_date
- Actual data: hours_used, hours_billable, fee_record
- Planned data: planned_hours, planned_fee
- Currency detection from filename or manual selection

### Current Status: ✅ COMPLETE
- Fully functional with clean UI
- Integrated with existing data infrastructure
- Proper error handling and user feedback
- Production-ready with all requested features implemented
# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL - READ FIRST
- **Project Location**: `~/code/arkemy/` (standard professional location)
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
# Coworker Report Overview

The Coworker Report is a person-centric analytics dashboard that analyzes individual and team workload data. Here's how it works:

## Main Entry Point ([2_Coworker_Report.py](pages/2_Coworker_Report.py))
- Sets up page configuration and initializes translations
- Manages session state for coworker data (with bidirectional sync)
- Calls `handle_coworker_upload()` which does all the heavy lifting

---

## Core Data Flow ([period_processors/coworker_report.py](period_processors/coworker_report.py))

### 1. Data Loading (`try_autoload_coworker_data()`)
- Searches for CSV files in priority order:
  - `/data` (Railway production)
  - `./data` (project directory)
  - `~/temp_data` (fallback)
- Looks for files matching patterns: `*coworker_report*.csv`, `coworker*.csv`, `person*.csv`, etc.
- Falls back to file upload interface if no auto-loaded data found

### 2. Data Preparation (`handle_coworker_upload()`)
- Converts `Period` column to datetime format
- Fills missing `Capacity/Period` values with `Hours/Period` data
- **Creates "All coworkers" aggregate row** by summing all numeric columns grouped by period
- This allows viewing both individual and team-level metrics

### 3. Period Filtering (`render_sidebar_filters()`)
- Four filter options:
  - **Month**: Year + Month selection
  - **Quarters**: Year + Quarter selection
  - **Year**: Full year view
  - **Year-to-Date**: From/To month range within current year
- Intelligently defaults to current year/previous month
- Filters available periods based on actual data

### 4. Person Selection
- Dropdown in sidebar with unique person names
- "All coworkers" always appears first (if data exists)

---

## Visualization Tabs (3 tabs)

**Hours Flow Tab** - Sankey diagram showing hours distribution for selected person

**Comparison Tab** - Bar chart comparing metrics (likely hours worked vs planned vs capacity)

**Forecast Tab** - Person-level forecasting chart

Each tab includes:
- Details section (summary metrics)
- Data section (underlying table)

---

## Key Data Columns Expected
```
Period, Person, Hours/Period, Capacity/Period, Absence/Period,
Hours/Registered, Project hours, Planned hours, Unpaid work
```

---

## Data Structure Summary
- **Input**: CSV with individual person-period records
- **Processing**: Adds aggregated "All coworkers" row + applies filters
- **Output**: 3 interactive tabs analyzing individual vs team workload metrics

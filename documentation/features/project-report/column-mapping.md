# Project Report Column Mapping Analysis

## Overview
The Project Report feature expects CSV data with specific columns, but the actual data exists in a unified parquet schema. This analysis verifies that ALL required data is available and can be transformed.

## Column Mapping: Expected → Available

### ✅ **Project ID**
- **Expected**: `Project ID` (unique project identifier)
- **Available**:
  - `project_number` ✅ (correct value)

### ✅ **Project Name**
- **Expected**: `Project Name` (human-readable project name)
- **Available**:
  - `project_name` ✅ (exact match)

### ✅ **Period**
- **Expected**: `Period` (date/month for data point)
- **Available**:
  - `record_date` ✅ (exact datetime - primary choice)
  - `year` ✅ (numeric year)
  - `month` ✅ (period format)

### ✅ **Period Hours** (Actual Hours Worked)
- **Expected**: `Period Hours` (actual hours worked in period)
- **Available**:
  - `hours_used` from `time_record` rows ✅ (hours actually worked)
  - `hours_billable` from `time_record` rows ✅ (hours worked that are billable)

### ✅ **Planned Hours** (Planned Hours for Period)
- **Expected**: `Planned Hours` (planned/budgeted hours)
- **Available**:
  - `planned_hours` ✅ (static planned hours per project)
  - `planned_billable` ✅ (planned hours that are billabe, as some planned hours are NOT billable)

### ✅ **Period Fees** (Actual Revenue)
- **Expected**: `Period Fees` (revenue generated in period)
- **Available**:
  - `fee_record` ✅ (the monetary value of worked hours)

### ✅ **Planned Income** (Planned Revenue)
- **Expected**: `Planned Income` (planned/budgeted revenue)
- **Available**:
  - `planned_fee` ✅ (the monetary value of planned hours)

## Data Structure Verification

### Record Types in Parquet
- **time_record**: 99,360 entries (actual work performed)
- **planned_record**: 2,241 entries (planned/forecasted work)

### Sample Data Validation

**time_record example:**
```
project_name: RON3 Rondetunet Utomhus
record_date: 2014-02-28
hours_used: 6.0 (actual hours worked)
fee_record: 5520.0 (actual revenue)
```

**planned_record example:**
```
project_name: NUNO Internt
record_date: 2023-09-30
planned_hours: NaN (some planned records use planned_hours instead)
planned_fee: 0.0 (planned revenue)
```

## Revised Transformation Strategy (Using Existing Infrastructure)

### Key Insight: Reuse Existing Aggregation Functions
- `utils/processors.py` → `aggregate_by_project()` for time_record data
- `utils/planned_processors.py` → `aggregate_by_project_planned()` for planned_record data

### Column Mapping Corrections:
- **Project ID** → `project_number` ✅ (client-facing, not internal `project_id`)

### Step 1: Filter and Aggregate Actual Data (time_record)
```python
# Filter to time_record only
time_records_df = parquet_df[parquet_df['record_type'] == 'time_record']

# Use existing aggregation function
actual_agg = aggregate_by_project(time_records_df)
# Returns: project_number, project_name, hours_used, hours_billable, fee_record, etc.
```

### Step 2: Filter and Aggregate Planned Data (planned_record)
```python
# Filter to planned_record only
planned_records_df = parquet_df[parquet_df['record_type'] == 'planned_record']

# Use existing aggregation function
planned_agg = aggregate_by_project_planned(planned_records_df)
# Returns: project_number, project_name, planned_hours, planned_fee, etc.
```

### Step 3: Transform to Project Report Format
```python
# Add period grouping (missing from existing functions)
# Group by project + period (month/year from record_date)
# Rename columns to match Project Report expectations:
{
    'project_number': 'Project ID',
    'project_name': 'Project Name',
    'record_date': 'Period',
    'hours_used': 'Period Hours',
    'planned_hours': 'Planned Hours',
    'fee_record': 'Period Fees',
    'planned_fee': 'Planned Income'
}
```

### Step 4: Merge Actual + Planned by Project + Period
Use existing `merge_actual_planned_projects()` function as template, but adapt for period-level merging.

## Conclusion

✅ **COMPLETE MAPPING POSSIBLE**

All required Project Report columns can be successfully mapped from the existing parquet data:

1. **Direct mappings** available for Project ID, Project Name, Period
2. **Aggregation needed** for Period Hours and Period Fees from time_record rows
3. **Aggregation needed** for Planned Hours and Planned Income from planned_record rows
4. **Data volume sufficient** with 99K+ actual records and 2K+ planned records

The parquet file contains ALL necessary information to generate the expected CSV format for Project Report functionality.
# Project Report Feature

Period-based project analytics with actual vs planned comparisons.

## 📋 Documentation

- [column-mapping.md](column-mapping.md) - Data transformation from parquet schema to Project Report CSV format

## 🎯 Feature Overview

The Project Report feature provides:
- **Period Filtering** - Month, Quarter, Year, Year-to-Date analysis
- **Actual vs Planned** - Compare worked hours/fees against planned values
- **Multi-View Analysis** - Hours, Fees, and Hourly Rate tabs
- **Rich Visualizations** - Bar charts (monthly trends) and treemaps (project distribution)
- **Clean UI** - Minimal interface focused on analytics

## 📊 Key Metrics

| Metric | Source | Description |
|--------|--------|-------------|
| Period Hours | hours_used (time_record) | Actual hours worked in period |
| Billable Hours | hours_billable (time_record) | Hours worked that are billable |
| Period Fees Adjusted | fee_record (time_record) | Actual revenue (already adjusted in ETL) |
| Planned Hours | planned_hours (planned_record) | Forecasted hours for period |
| Planned Income | planned_fee (planned_record) | Forecasted revenue for period |

## 🔗 Related Documentation

- [@.claude/docs/features/project-report.md](../../../.claude/docs/features/project-report.md) - Feature status and overview
- [Lessons - Plotly](../../lessons/plotly/) - Treemap and chart implementations
- [Architecture - Schema System](../../architecture/schema-system.md) - Data validation and structure

## 🗂️ File Structure

```
pages/
├── 3_Project_Report.py          # Page entry point

period_processors/
├── project_report.py             # Main processor with transformation logic

period_charts/
├── project_hours.py              # Hours analysis charts
├── project_fees.py               # Fees analysis with treemap
└── project_rate.py               # Hourly rate comparisons

period_utils/
├── project_utils.py              # Project utility functions
└── chart_utils.py                # Chart creation and formatting utilities
```

## 💡 Key Implementation Details

### Data Transformation
The Project Report transforms unified parquet data into project-focused visualizations:
1. Filter by period (month, quarter, year, YTD)
2. Separate time_records (actual) and planned_records (forecasting)
3. Aggregate by project
4. Calculate metrics (hours, fees, rates, margins)
5. Display in visualizations

### Period Filtering Logic
- Quarter filter defaults to current year (2025) with fallback to most recent
- Shows helpful warnings when no data exists for selected period
- Validates data availability and guides users to periods with data

### Chart Features
- Hover templates with 0 decimal places and thousand separators
- Color scheme: "Used" data gets darker colors, "Planned" gets lighter
- Treemap with proper comma formatting for monetary values
- Monthly bar charts with chronological ordering

---

**Last Updated**: 2025-11-18
**Status**: Complete - Fully functional with clean UI

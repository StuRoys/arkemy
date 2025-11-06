# Branch: kpi-period-comparison

## Overview
Added comprehensive KPI Period Comparison feature to the Company tab, enabling users to compare company-wide metrics across two configurable time periods.

## Commit
- **3ab1cd9**: Add KPI Period Comparison feature to Company tab

## Changes Made

### New Files Created

#### 1. `utils/comparison_helpers.py` (277 lines)
Core business logic for period comparison calculations.

**Functions:**
- `calculate_period_dates(end_date, months, mode)`: Calculates Period A and Period B date ranges
  - Mode 'period': Consecutive/adjacent periods
  - Mode 'year': Same period across different years
  - Returns: (period_a_start, period_a_end, period_b_start, period_b_end)

- `aggregate_period_metrics(df, start_date, end_date)`: Aggregates company-wide metrics for a date range
  - Returns dict with: effective_rate, billability, fee, profit, profit_margin, hours_used, has_data
  - Safe division handling for all calculations

- `calculate_comparison(period_a_metrics, period_b_metrics)`: Calculates absolute and percentage differences
  - Returns structured dict with a, b, diff, pct_change, direction for each metric
  - Direction: 'up', 'down', or 'neutral'

- `validate_period_data(df, period_b_start, period_b_end)`: Validates Period B data availability
  - Returns: (is_valid, warning_message)
  - Checks if Period B extends before earliest data or has no records

- `format_period_label(start_date, end_date)`: Formats period labels for display
  - Format: "Apr 1, 2025 - Sep 30, 2025"

- `get_metric_config()`: Returns configuration dict for each metric
  - Includes: label, unit type, positive_is_good flag

#### 2. `charts/company_comparison.py` (400 lines)
UI components and visualization logic.

**Functions:**
- `render_summary_card(metric_name, comparison_data, metric_config)`: Renders individual KPI card
  - Shows: Period A value, Period B value, Absolute difference, Percentage change
  - Color-coded indicators (green ↑ for positive, red ↓ for negative)
  - Proper currency/percentage formatting with symbols

- `render_summary_cards(comparison)`: Renders all 5 summary cards in a row
  - Metrics: Effective Rate, Billability, Fee, Profit, Profit Margin

- `render_comparison_chart(selected_metric, comparison, period_a_label, period_b_label)`: Grouped bar chart
  - Side-by-side bars for Period A vs Period B
  - Proper axis labels with units (currency, percentage, etc.)
  - Hover tooltips with formatted values

- `render_comparison_tab(filtered_df)`: Main orchestration function
  - User controls for comparison mode, timeframe, end date
  - Auto-calculated period display
  - Data validation with warnings
  - Summary cards and comparison chart rendering

### Modified Files

#### 3. `ui/dashboard.py`
- Added import: `from charts.company_comparison import render_comparison_tab`
- Modified Company tab navigation from 3 tabs to 4:
  - Added "Comparison" as 4th tab (line 112)
  - Wired up comparison tab rendering (line 143-144)

## Feature Specifications

### User Controls
1. **Comparison Mode** (Radio buttons, horizontal)
   - "Period vs Period": Compare consecutive/adjacent periods
   - "Year vs Year": Compare same period across different years

2. **Time Frame** (Slider: 1-12 months)
   - Default: 6 months
   - Determines the length of each period

3. **Period A End Date** (Date picker)
   - Default: Latest date in dataset
   - Min/max constrained to available data

### Auto-Calculated Periods
- **Period A**: Calculated as [end_date - months + 1 day] to [end_date]
- **Period B**:
  - Period vs Period mode: [Period A start - months] to [Period A start - 1 day]
  - Year vs Year mode: Same dates as Period A, minus 1 year

### Example Scenarios
1. **Q2 2025 vs Q1 2025**
   - Mode: Period vs Period
   - Months: 3
   - End Date: 2025-06-30
   - Period A: Apr 1 - Jun 30, 2025
   - Period B: Jan 1 - Mar 31, 2025

2. **Q3 2025 vs Q3 2024**
   - Mode: Year vs Year
   - Months: 3
   - End Date: 2025-09-30
   - Period A: Jul 1 - Sep 30, 2025
   - Period B: Jul 1 - Sep 30, 2024

### KPIs Displayed

All metrics shown in both summary cards and chart selector:

1. **Effective Rate**: Total fee / total hours worked (kr/hr)
2. **Billability**: Billable hours percentage (%)
3. **Fee**: Total revenue (kr)
4. **Profit**: Total profit (kr)
5. **Profit Margin**: Profit as percentage of fee (%)

### Data Display

#### Summary Cards (5 cards)
Each card shows:
- Metric name (header)
- Period A value (large, bold)
- Period B value (medium)
- Absolute difference (Δ: ±X)
- Percentage change (±X.X% with ↑/↓ arrow)

Color coding:
- Green: Positive change (when increase is good)
- Red: Negative change (when decrease is bad)
- Gray: No change (neutral)

#### Comparison Chart
- Grouped bar chart (side-by-side)
- Metric selector dropdown above chart
- X-axis: Period A and Period B labels
- Y-axis: Metric value with appropriate units
- Hover: Shows period label, exact value, formatted

#### Detailed Numbers Table (Expandable)
- All 5 metrics in tabular format
- Columns: Metric, Period A, Period B, Difference, Change %
- Hidden by default in expander

### Error Handling

**Validation and Warnings:**
1. Period B extends before data start:
   - Shows warning with data start date and required date
   - Suggests selecting more recent end date or shorter timeframe

2. Period B has no records:
   - Shows warning with Period B date range
   - Prevents comparison calculations

3. Period A has no records:
   - Shows warning (rare edge case)
   - Prevents comparison calculations

## Technical Implementation

### Data Flow
1. User selects controls (mode, months, end date)
2. Calculate period dates using `calculate_period_dates()`
3. Validate Period B data with `validate_period_data()`
4. Aggregate metrics for both periods using `aggregate_period_metrics()`
5. Calculate comparison using `calculate_comparison()`
6. Render summary cards and chart

### Session State Keys
- `comparison_mode`: 'period' or 'year'
- `comparison_months`: 1-12
- `comparison_end_date`: date object
- `comparison_selected_metric`: metric name for chart

### Formatting
- Uses existing `format_currency_value()` from chart_styles
- Respects currency symbol positioning (before/after)
- Percentage points (pp) for billability differences
- Color-coded change indicators with arrows

### Integration Points
- Leverages existing `chart_styles.py` for currency formatting
- Follows pattern from other chart modules
- Uses filtered_df from sidebar filters
- Consistent with Arkemy visual design

## Testing Checklist
- [x] App starts without errors
- [x] Comparison tab appears in Company section
- [x] Controls update session state correctly
- [x] Period dates calculate correctly for both modes
- [x] Data validation shows appropriate warnings
- [x] Summary cards display with proper formatting
- [x] Chart renders with correct metric values
- [x] Currency symbols positioned correctly
- [x] Color coding works (green/red/gray)
- [x] Expandable table shows detailed numbers

## Dependencies
- pandas (date operations, filtering)
- dateutil.relativedelta (month/year calculations)
- streamlit (UI components)
- plotly.graph_objects (chart rendering)
- Existing utils: chart_styles, processors

## Future Enhancements (Not Implemented)
- Drill-down comparisons (by customer, project, person)
- Multi-period trend comparison (A vs B vs C)
- Export comparison data to CSV
- Custom period selection (non-rolling dates)
- Comparison of planned vs actual within periods

## Notes
- Feature is company-level only (aggregate metrics)
- Uses time_records data only (not planned_records)
- All calculations include safe division (handle zero denominators)
- Date ranges are inclusive on both ends
- Compatible with existing sidebar filters

# Project Snapshot Feature

Quick visual comparison of project performance over time with modern, Stockpeer-inspired UI.

## 🎯 Feature Overview

The Project Snapshot feature provides PMs with a crystal-clear, immediate impression of project performance:
- **Period Selection** - 3M, 6M, YTD, 1Y, All periods with pill-style selectors
- **Project Comparison** - Compare multiple projects or view aggregated data
- **Visual Analytics** - Altair line charts showing hours worked over time
- **Self-Contained UI** - No sidebar filters, all controls in the main view
- **Modern Design** - Stockpeer-inspired dark theme and asymmetric layout

## 🎨 Design Elements

### Stockpeer Inspiration
Borrowed modern design patterns from [Stockpeer demo](https://stockpeer.streamlit.app/):
- **Dark Theme** - Space Grotesk font, purple accent (#615fff), dark background (#1d293d)
- **Asymmetric Layout** - 1:3 column ratio (controls on left, chart on right)
- **Pills Widget** - Button-style period selectors instead of radio buttons
- **Bordered Containers** - Fixed height containers with border styling
- **Altair Charts** - Lightweight declarative charting instead of Plotly

### Theme Configuration
Applied globally via [.streamlit/config.toml](.streamlit/../../../../.streamlit/config.toml):
```toml
[theme]
base = "dark"
primaryColor = "#615fff"
backgroundColor = "#1d293d"
font = "Space Grotesk"
```

## 📊 Key Metrics

| Metric | Description |
|--------|-------------|
| Period Hours | Actual hours worked per project per period |

**Future metrics** (to be added):
- Fees
- Hourly rates
- Planned vs actual comparisons
- Project health indicators

## 🗂️ File Structure

```
pages/
└── 6_Project_Snapshot.py         # Page entry point with data autoload

period_charts/
└── project_snapshot.py            # Rendering logic with Stockpeer-style layout

.streamlit/
└── config.toml                    # Global dark theme configuration
```

## 💡 Key Implementation Details

### Layout Pattern
**Asymmetric 1:3 Column Layout** (Stockpeer-style):
```python
cols = st.columns([1, 3])

# Left: Controls (period + project selection)
left_cell = cols[0].container(border=True, height=500, vertical_alignment="top")

# Right: Chart visualization
right_cell = cols[1].container(border=True, height=500, vertical_alignment="center")
```

### Period Selection
**Pills Widget** for modern button-style selectors:
```python
period_options = {
    "3M": 3,
    "6M": 6,
    "YTD": "ytd",
    "1Y": 12,
    "All": "all"
}

selected_period_key = st.pills(
    "Period",
    options=list(period_options.keys()),
    default="1Y",
    label_visibility="collapsed"
)
```

### Period Filtering Logic
- **3M/6M/1Y**: Calculate start date using `pd.DateOffset(months=N)`
- **YTD**: Start from January 1st of max period year
- **All**: No filtering, show complete dataset

### Chart Implementation
**Altair Line Chart** with interactive tooltips:
```python
chart = (
    alt.Chart(plot_data)
    .mark_line(point=True)
    .encode(
        alt.X("Period:T", title="Period", axis=alt.Axis(format="%b %Y")),
        alt.Y("Period Hours:Q", title="Hours Worked", scale=alt.Scale(zero=False)),
        alt.Color("Project Name:N", title="Project"),
        tooltip=["Period:T", "Project Name:N", "Period Hours:Q"]
    )
    .properties(height=400, title="Period Hours by Project")
    .interactive()
)
```

### Data Loading
Uses autoload pattern from Project Report:
```python
# Try to autoload data first
autoloaded_data = try_autoload_project_data()

if autoloaded_data is not None:
    st.session_state.project_data = autoloaded_data
    st.session_state.period_report_project_data = autoloaded_data
```

### Project Selection
**Multiselect with "All projects" option**:
- Default: Top 5 projects by hours worked
- Option to aggregate all projects into single line
- Sort projects by total hours (descending)

## 🔄 Changelog

### v1.0.0 - Initial Implementation (2025-11-18)
**Branch**: `feat/project-report-project-snapshot` (8 commits)

#### Added
- Created dedicated Project Snapshot page ([pages/6_Project_Snapshot.py](../../../pages/6_Project_Snapshot.py))
- Implemented Stockpeer-style rendering ([period_charts/project_snapshot.py](../../../period_charts/project_snapshot.py))
- Applied global dark theme ([.streamlit/config.toml](../../../.streamlit/config.toml))
- Added period selection with pills widget (3M, 6M, YTD, 1Y, All)
- Added project comparison with multiselect
- Implemented Altair line chart for Period Hours visualization
- Added translation keys: `snapshot_project` (en/no)
- Registered page in main.py navigation

#### Design Decisions
- **Separate Page** (not nested tabs) - Better UX for PM workflow
- **No Sidebar Filters** - Self-contained UI reduces cognitive load
- **Pills over Radio** - Matches Stockpeer's modern aesthetic
- **Altair over Plotly** - Lighter weight, simpler syntax for basic charts
- **1:3 Column Ratio** - Maximizes chart visibility while keeping controls accessible

#### Technical Notes
- Tooltip syntax: Simple list of fields (Altair 5.x), not nested `alt.Tooltip()` objects
- Page registration: Must be added to `main.py` navigation array
- Data sharing: Uses `st.session_state.period_report_project_data` shared with Project Report
- Period filtering: Operates on copy of dataframe to avoid mutation

## 🔗 Related Documentation

- [Project Report Feature](../project-report/README.md) - Period-based analytics with tabs
- [Lessons - Streamlit](../../lessons/streamlit/) - Widget patterns and state management
- [Architecture - Schema System](../../architecture/schema-system.md) - Data validation

## 🚧 Future Enhancements

### Potential Additions
- [ ] Additional metrics (fees, rates, margins)
- [ ] Planned vs actual overlay
- [ ] Project health indicators (on track, at risk, over budget)
- [ ] Sparklines for quick trend visibility
- [ ] Export to PDF/CSV functionality
- [ ] Drill-down to Project Report detail view
- [ ] Comparison to historical averages
- [ ] Forecast projections

### Design Considerations
- Keep UI simple and focused
- Maintain Stockpeer aesthetic
- Prioritize PM workflow needs
- Avoid information overload

---

**Last Updated**: 2025-11-18
**Status**: v1.0.0 - Minimal viable feature (Period Hours only)
**Branch**: `feat/project-report-project-snapshot`
**Commits**: 8 total

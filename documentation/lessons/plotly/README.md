# Plotly - Visualization Patterns & Best Practices

Implementation lessons for building visualizations with Plotly in Arkemy.

## 📚 Lessons

### 1. Plotly Reference Guide
[plotly-reference.md](plotly-reference.md)

**Covers:**
- Treemap visualization basics
- Hierarchical treemap configuration
- The `branchvalues="total"` parameter (critical!)
- The `maxdepth` parameter for drill-down
- Pathbar navigation
- Customdata and hovertemplate alignment
- Debugging treemap rendering issues

**Read this when:**
- Building a treemap visualization
- Debugging why a treemap isn't rendering
- Implementing drill-down interactivity
- Understanding customdata array indexing

### 2. Treemap Percentage Implementation
[treemap-percentage-implementation.md](treemap-percentage-implementation.md)

**Covers:**
- Complete implementation of percentage display on treemaps
- Architecture (SUM_METRICS constant, helper functions)
- Implementation patterns for simple and hierarchical treemaps
- Customdata array structure
- Common pitfalls and solutions
- File reference map
- Testing checklist

**Read this when:**
- Implementing percentage display on treemaps
- Understanding Arkemy's percentage calculation system
- Debugging percentage display issues
- Building similar features with dynamic calculations

## 🎯 Quick Reference

### Common Treemap Issues & Solutions

| Problem | Solution | Reference |
|---------|----------|-----------|
| Treemap not visible | Ensure parent node values are numeric, not zero | plotly-reference.md - Debugging |
| Raw texttemplate shows on tiles | Customdata array size mismatch (needs 20 elements) | treemap-percentage-implementation.md |
| Percentages show 0.0% | Missing percentage population in customdata[19] | treemap-percentage-implementation.md - Pitfall 2 |
| Hover shows wrong values | Customdata order doesn't match IDs order | plotly-reference.md - Customdata Alignment |
| Can't drill down | maxdepth too low or hierarchy structure wrong | plotly-reference.md - maxdepth Parameter |

## 🔗 Related Documentation

- [Lessons - Main](../) - All implementation lessons
- [Features - Project Report](../../features/project-report/) - Uses treemap percentages
- [Architecture - System Design](../../architecture/) - Data structures used by visualizations

## 📖 Learning Path

### For New Plotly Users
1. Read **Plotly Reference Guide** - Understand treemap basics
2. Study **treemap-percentage-implementation** - Learn about customdata
3. Review Arkemy code examples - See patterns in action

### For Building Similar Features
1. Check **treemap-percentage-implementation** for the architecture approach
2. Understand the **SUM_METRICS constant** pattern
3. Review **common pitfalls** to avoid problems
4. Follow the **file reference map** to adapt to your context

### For Debugging Treemap Issues
1. Identify the symptom (rendering, drill-down, data, etc.)
2. Look it up in **plotly-reference.md - Debugging** section
3. Check **treemap-percentage-implementation.md - Common Pitfalls**
4. Review exact line numbers in file references

## 💡 Key Insights from Arkemy Plotly Usage

### Hierarchical Treemaps in Arkemy
- Used in: customer_group_charts, project_type_charts
- Structure: ROOT → Groups → Items
- Key setting: `branchvalues="total"` + manual parent value calculation

### Simple Treemaps in Arkemy
- Used in: customer, people, phase, activity, price_model, project charts
- Structure: ROOT → Items
- Centralized via: `create_single_metric_chart()` helper

### Percentage Display Pattern
- Calculation layer: `add_percentage_columns()` in processors.py
- Display layer: `build_treemap_texttemplate()` in chart_helpers.py
- Customdata index: [19] for percentage value

## 🛠️ Toolkit - Reusable Code Patterns

### Customdata Array Template
```python
# For any treemap with 20-element customdata
customdata = [
    metric_1,              # [0]
    metric_2,              # [1]
    # ... 18 more items ...
    percentage_value       # [19]
]
```

### Texttemplate for Percentages
```python
# Shows label + percentage (if available)
texttemplate = '%{label}<br>%{customdata[19]:.1f}%'
```

### Percentage Calculation Pattern
```python
# Calculate percentages for any metric
df['metric_pct'] = (df['metric'] / df['metric'].sum()) * 100
```

---

**Last Updated**: 2025-11-18
**Lessons**: 2 comprehensive guides covering treemaps and percentages

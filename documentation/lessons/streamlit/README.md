# Streamlit - Framework Patterns & Best Practices

Implementation lessons for building applications with Streamlit in Arkemy.

## 📚 Lessons

### 1. format_func Pattern
[format-func-pattern.md](format-func-pattern.md)

**Covers:**
- What is `format_func`?
- Problem it solves (display label translation)
- Implementation in Arkemy (project_type_charts)
- Complete data flow from parquet to UI
- Benefits (simplicity, performance, reliability)
- Pattern template for reuse
- Common pitfalls to avoid
- Testing the implementation

**Read this when:**
- You need to display user-friendly labels for technical values
- You're using st.selectbox and need label translation
- You want to avoid complex reverse lookups
- You're building similar "display one thing, use another" patterns

**Real-world example:**
- Technical values: `['project_tag_1', 'project_tag_2', 'project_tag_3']`
- User sees: `['Offentlig eller privat', 'Prosjektfase', 'TEAM']`
- Widget stores: Technical column name (no extra translation needed!)

### 2. Coworker Report Feature
[coworker-report-feature.md](coworker-report-feature.md)

**Covers:**
- Feature overview and purpose
- Person-centric analytics dashboard architecture
- Main entry point and data flow
- Core processors and aggregation
- Page sections and visualizations
- File structure and organization

**Read this when:**
- You need to understand the Coworker Report feature
- You're modifying person-based analytics
- You want to build a similar person-centric dashboard
- You're understanding how Arkemy aggregates by person

## 🎯 Quick Reference

### Common Streamlit Patterns in Arkemy

| Pattern | Use Case | Reference |
|---------|----------|-----------|
| `format_func` | Display label translation | format-func-pattern.md |
| Widget keys | State persistence across reruns | CLAUDE.md project notes |
| Session state | Storing data between interactions | architecture docs |
| Selectbox filters | Multi-level filtering | Various chart modules |

## 🔗 Related Documentation

- [Lessons - Main](../) - All implementation lessons
- [Architecture - System Design](../../architecture/) - Data and session state management
- [@.claude/docs/](../../.claude/docs/) - Additional Streamlit guidelines (in .claude)

## 📖 Learning Path

### For New Streamlit Users
1. Understand **format_func pattern** - Most common Streamlit pattern in Arkemy
2. Review **Coworker Report feature** - Complete feature implementation
3. Study the code in Arkemy - See patterns in action

### For Building UI Features
1. Check **format_func pattern** - How to handle label translation
2. Review **Coworker Report** - Example of a complete feature
3. Follow Arkemy conventions - Use established patterns
4. Reference the guidelines in .claude/docs - Framework-specific practices

### For Debugging Streamlit Issues
1. Check widget behavior in **format_func pattern** - Most common UI patterns
2. Review **Coworker Report** data flow - Understand how data moves
3. Consult [@.claude/streamlit-guidelines.md](../../../.claude/streamlit-guidelines.md) - Framework-specific guidance

## 💡 Key Insights from Arkemy Streamlit Usage

### Widget State Management
- Use `format_func` for display label translation
- Use meaningful `key` parameters for persistence
- Leverage session state for data caching

### Feature Organization
- Separate pages for major features (Analytics, Coworker Report, Project Report)
- Consistent chart patterns across features
- Centralized aggregation and helper functions

### Data Flow Pattern
1. Load data once in session state
2. Filter through sidebar
3. Aggregate using processors.py functions
4. Display in charts using consistent patterns

## 🛠️ Toolkit - Reusable Code Patterns

### format_func Template
```python
# Step 1: Get technical values
technical_values = get_values()  # ['value_1', 'value_2']

# Step 2: Get label mapping
label_mapping = get_mapping()    # {'value_1': 'Label 1', ...}

# Step 3: Use in selectbox
selected = st.selectbox(
    "Choose option",
    options=technical_values,
    format_func=lambda v: label_mapping.get(v, v),  # Fallback
    key="unique_key"
)

# selected is already the technical value!
```

### Feature File Structure
```
feature_name/
├── pages/
│   └── N_Feature_Name.py      # Page entry point
├── period_processors/         # Data processing
│   └── feature_name.py
├── period_charts/            # Visualizations
│   ├── feature_chart_1.py
│   └── feature_chart_2.py
└── period_utils/             # Utilities
    ├── feature_utils.py
    └── chart_utils.py
```

## 📚 Best Practices from Arkemy

### DO ✅
- Use `format_func` for label translation
- Store technical values in widget options
- Use meaningful widget keys
- Separate concerns (data vs UI logic)
- Reference existing patterns

### DON'T ❌
- Store display labels in widget options (complex reverse lookup)
- Use complex callbacks for simple state changes
- Mix display and data logic
- Create new patterns when existing ones exist

---

**Last Updated**: 2025-11-18
**Lessons**: 2 guides covering patterns and a complete feature

# Lessons - Implementation Patterns & Best Practices

This section contains implementation lessons learned from building Arkemy, organized by framework/technology.

## 📚 Available Lessons

### Plotly - Visualization Patterns
- [plotly-reference.md](plotly/plotly-reference.md) - Core Plotly patterns including treemaps, hierarchical structures, customdata alignment
- [treemap-percentage-implementation.md](plotly/treemap-percentage-implementation.md) - Complete guide to implementing percentage display on treemaps

**When to read:**
- You need to build or modify a treemap visualization
- You're debugging treemap rendering issues
- You want to understand customdata array indexing
- You're implementing hierarchical drill-down features

### Streamlit - Framework Patterns
- [format-func-pattern.md](streamlit/format-func-pattern.md) - Using Streamlit's format_func for display label translation
- [coworker-report-feature.md](streamlit/coworker-report-feature.md) - Feature architecture for person-centric analytics dashboard

**When to read:**
- You need to map technical values to user-friendly labels
- You're building a widget that shows different data than it stores
- You want to understand Arkemy's Coworker Report architecture
- You're implementing similar label translation patterns

## 🎓 How to Use These Lessons

### Learning a Pattern
1. **Identify what you're trying to do** - visualization, UI pattern, etc.
2. **Find the relevant lesson** - organized by framework
3. **Read the overview** - understand the problem and solution
4. **Study the implementation** - see code examples and patterns
5. **Learn the pitfalls** - understand what can go wrong

### Applying a Pattern
1. **Find the lesson** covering your use case
2. **Review code examples** from actual Arkemy code
3. **Follow the file references** to see exact line numbers
4. **Check the common pitfalls** section to avoid mistakes
5. **Adapt the pattern** to your specific context

### Contributing a Lesson

When you discover a useful pattern or solve a problem:

1. **Write the lesson** following the template:
   - Problem statement
   - Solution approach
   - Implementation patterns
   - Code examples from codebase
   - Common pitfalls
   - File references with line numbers

2. **Place it in the right directory**:
   - Plotly → `plotly/`
   - Streamlit → `streamlit/`
   - Python → `python/` (when created)

3. **Update this README** with a link and description

## 📋 Lesson Template

When creating a new lesson, use this structure:

```markdown
# Pattern/Lesson Name

## Overview
Brief description of what this lesson covers.

## Problem Statement
What problem does this solve? Why is this important?

## Solution Approach
High-level explanation of the approach.

## Architecture
Key components and how they fit together.

## Implementation Pattern
Step-by-step implementation guide with code examples.

## Common Pitfalls & Solutions
What can go wrong and how to fix it.

## File Reference Map
Exact locations in the codebase (with line numbers).

## Testing Checklist
How to verify the implementation works.

## Related Documentation
Links to related lessons, architecture docs, features.
```

## 🔗 Related Documentation

- [Architecture - System Design](../architecture/) - For understanding data models and overall system
- [Features - Feature Documentation](../features/) - For complete feature implementations
- [Main README](../) - Navigation hub for all documentation

---

**Last Updated**: 2025-11-18

# Arkemy Documentation

Comprehensive documentation for the Arkemy project, including architectural guides, implementation lessons, features, and best practices.

## Directory Structure

```
documentation/
├── README.md (this file)
├── lessons/                   - Implementation patterns & best practices
│   ├── plotly/               - Plotly visualization documentation
│   └── streamlit/            - Streamlit framework patterns
├── architecture/             - System design & data models
├── features/                 - Feature-specific documentation
└── (See Quick Links for .claude/docs/)
```

## 📚 Lessons - Implementation Patterns

### Plotly
- [Plotly Reference Guide](lessons/plotly/plotly-reference.md) - Treemap configurations, customdata structures, debugging
- [Treemap Percentage Implementation](lessons/plotly/treemap-percentage-implementation.md) - Complete guide to dynamic percentage display on treemaps

### Streamlit
- [format_func Pattern](lessons/streamlit/format-func-pattern.md) - Display label translation without reverse lookups
- [Coworker Report Feature](lessons/streamlit/coworker-report-feature.md) - Person-centric analytics dashboard architecture

## 🏗️ Architecture - System Design

- [Arkemy Schema System](architecture/schema-system.md) - YAML-driven data validation and record type separation
- [@.claude/docs/architecture.md](../.claude/docs/architecture.md) - Overall system architecture and data flow
- [@.claude/docs/data-model.md](../.claude/docs/data-model.md) - Data types and business concepts

## 🎯 Features - Feature Documentation

- [Project Report - Column Mapping](features/project-report/column-mapping.md) - Data mapping between parquet schema and Project Report CSV
- [Tag Parsing Configuration](features/tag-parsing-config.md) - Multiple project tag dimensions with user-friendly labels

## 🔗 Quick Reference Links

**Development & Deployment**:
- [@.claude/docs/railway.md](../.claude/docs/railway.md) - Railway deployment guide
- [CLAUDE.md](../CLAUDE.md) - Project-specific development instructions

**Feature Documentation** (in .claude/docs/):
- [@.claude/docs/features/project-report.md](../.claude/docs/features/project-report.md) - Project Report feature overview

## 📖 How to Use This Documentation

### Finding Information
- **Learning a visualization pattern?** → Check [Plotly Reference](lessons/plotly/)
- **Understanding a Streamlit feature?** → Check [Streamlit Lessons](lessons/streamlit/)
- **Need to modify data handling?** → Check [Architecture](architecture/) section
- **Working on a specific feature?** → Check [Features](features/) section

### Understanding a Feature
Each feature directory contains:
- **Overview** - What the feature does
- **Architecture** - How it's structured
- **Data Flow** - How data moves through the system
- **Implementation** - How it was built
- **File References** - Exact line numbers in source code

## ✨ Contributing

When adding new features or making significant architectural decisions:

1. **Create documentation** - Write a document explaining:
   - Problem statement
   - Solution approach
   - Implementation patterns
   - Common pitfalls & solutions
   - File references with exact line numbers
   - Data flow diagrams (when appropriate)

2. **Follow the structure**:
   ```
   If it's a pattern → lessons/{framework}/
   If it's architecture → architecture/
   If it's a feature → features/{feature-name}/
   ```

3. **Use consistent formatting** - Follow templates from existing documentation

4. **Update this README** - Add links and update directory structure

5. **Include code examples** - Real examples from the codebase help others learn

## 📋 Documentation Standards

### File Naming
- Use kebab-case: `treemap-percentage-implementation.md`
- Be descriptive: `format-func-pattern.md`, not `streamlit.md`

### Structure
- Start with overview/problem statement
- Include architecture diagrams or data flow
- Provide code examples from actual codebase
- List common pitfalls and solutions
- Reference exact files and line numbers
- End with related links and references

### Metadata
- Include "Last Updated" date
- Link to related files
- Reference line numbers in source code

---

**Last Updated**: 2025-11-18
**Organization**: Restructured to separate lessons, architecture, and features


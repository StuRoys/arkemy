# Features - Feature-Specific Documentation

This section contains comprehensive documentation for Arkemy features, including architecture, data flow, and implementation details.

## 📋 Available Features

### Project Report
**Directory**: [project-report/](project-report/)

- [column-mapping.md](project-report/column-mapping.md) - Data transformation from parquet schema to Project Report CSV format

**Overview**: The Project Report feature provides period-based project analytics with actual vs planned comparisons.

**When to read:**
- You need to understand how data maps from parquet to CSV
- You're modifying Project Report data transformation logic
- You need to add new columns or metrics to Project Report
- You want to understand the data schema compatibility

### Project Snapshot
**Directory**: [project-snapshot/](project-snapshot/)

**Overview**: Quick visual comparison of project performance over time with modern, Stockpeer-inspired UI. Provides PMs with immediate insights through period-based filtering and project comparison.

**When to read:**
- You're working on the Project Snapshot page
- You need to understand Stockpeer-inspired design patterns
- You want to add new metrics or visualizations to the snapshot view
- You're modifying period filtering or project comparison logic

### Tag Parsing Configuration
**File**: [tag-parsing-config.md](tag-parsing-config.md)

**Overview**: Support for multiple project tag dimensions with user-friendly label translation.

**When to read:**
- You need to understand how project tags work
- You're adding new tag dimensions
- You want to understand tag-to-label mapping
- You're working with the tag management system

## 🏗️ Feature Documentation Structure

Each feature directory contains:
- **Overview** - What the feature does and why
- **Architecture** - System design and components
- **Data Flow** - How data moves through the feature
- **Implementation** - How the feature was built
- **File References** - Exact line numbers in source code

## 📖 How to Use Feature Documentation

### Understanding a Feature
1. **Start with the overview** - Get the big picture
2. **Study the architecture** - See how components fit together
3. **Follow the data flow** - Understand how data moves
4. **Review the implementation** - Learn the exact code
5. **Check file references** - Find the code in the repository

### Modifying a Feature
1. **Read the overview** - Understand current behavior
2. **Review architecture** - Know what will be impacted
3. **Find file references** - Locate the code to modify
4. **Check related features** - Ensure no conflicts
5. **Test thoroughly** - Verify changes work end-to-end

### Adding a New Feature
1. **Create the feature documentation** first
2. **Document the architecture** before coding
3. **Define data flow** for clarity
4. **Implement following the documented approach**
5. **Update this README** with links

## 🔗 Related Documentation

### Design & Architecture
- [Architecture - System Design](../architecture/) - Overall Arkemy architecture
- [Lessons - Implementation Patterns](../lessons/) - Reusable patterns from existing features

### Development
- [@.claude/docs/features/project-report.md](../../.claude/docs/features/project-report.md) - Project Report overview and status
- [CLAUDE.md](../../CLAUDE.md) - Development instructions

## 📋 Feature Documentation Template

When creating a new feature document:

```markdown
# Feature Name

## Overview
What does this feature do? Why does it exist?

## Architecture
Key components and how they interact.

## Data Flow Diagram
Visual representation of data movement.

## Implementation Details
How was it built? Key code sections and algorithms.

## File Reference Map
Exact files and line numbers for the implementation.

## Configuration
Any configuration options or setup required.

## Testing
How to verify the feature works correctly.

## Related Features & Dependencies
What other features does this depend on?

## Future Enhancements
Planned improvements or known limitations.
```

---

**Last Updated**: 2025-11-18

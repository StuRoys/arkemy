# Architecture - System Design & Data Models

This section contains documentation about Arkemy's overall architecture, data models, and system design.

## 📐 Core Architecture Documentation

### Arkemy Schema System
**File**: [schema-system.md](schema-system.md)

**Overview**: YAML-driven data validation and loading system that automatically handles data validation, record type separation, and data type management.

**Key topics:**
- Two data types: `time_record` (actual) and `planned_record` (forecasting)
- Schema-driven validation without code changes
- Record type separation logic
- YAML schema configuration

**When to read:**
- You need to understand how data is validated
- You're adding new record types or fields
- You want to understand the unified parquet schema
- You're modifying data loading logic

### System Architecture & Data Flow
**Location**: [@.claude/docs/architecture.md](../../.claude/docs/architecture.md)

**Overview**: High-level architecture of Arkemy application including:
- Core data flow (unified schema-driven system)
- Key components (entry point, UI layer, data management, charts, utils)
- Session state management
- Currency system
- Development notes

**When to read:**
- You need the big picture of how Arkemy works
- You're adding a new page or major feature
- You want to understand the component relationships
- You're planning architectural changes

### Data Model & Business Concepts
**Location**: [@.claude/docs/data-model.md](../../.claude/docs/data-model.md)

**Overview**: Business concepts and data types including:
- `time_record` - Actual hours worked (historical)
- `planned_record` - Forecasted hours/fees (planning)
- Unified file benefits
- Session state data structures

**When to read:**
- You need to understand what data represents
- You're writing aggregation functions
- You're building reports or analytics
- You want to understand the time vs planned data distinction

## 🗂️ How Architecture Documentation Works

### For New Contributors
1. **Start here** - Read the core architecture overview
2. **Understand data** - Learn data types and models
3. **Study the schema** - Know how data is validated
4. **Explore features** - See how these concepts apply

### For Extending Arkemy
1. **Review architecture** - Understand current design
2. **Check data model** - Know what data is available
3. **Study schema system** - Learn how to add new fields
4. **Follow existing patterns** - Use established code structure
5. **Update documentation** - Document your additions

## 🔗 Related Documentation

### Implementation Patterns
- [Lessons - Implementation Patterns](../lessons/) - Reusable patterns for building features

### Specific Features
- [Features - Feature Documentation](../features/) - Individual feature implementations using this architecture

### Development
- [CLAUDE.md](../../CLAUDE.md) - Project-specific development instructions
- [@.claude/docs/railway.md](../../.claude/docs/railway.md) - Deployment architecture

## 📊 Architecture at a Glance

```
┌─────────────────────────────────────┐
│        Data Loading Layer            │
│  (unified_data_loader.py)            │
│  - Schema validation (YAML)          │
│  - Record type separation            │
│  - Currency detection                │
└──────────────┬──────────────────────┘
               │
      ┌────────▼────────┐
      │ Session State   │
      ├─────────────────┤
      │ transformed_df  │ (time_records)
      │ planned_df      │ (planned_records)
      │ currency, etc.  │
      └────────┬────────┘
               │
  ┌────────────┴──────────────┐
  │                           │
  ▼                           ▼
┌──────────────────┐   ┌──────────────────┐
│  Dashboard UI    │   │  Aggregation     │
│  (dashboard.py)  │   │  (processors.py) │
│  - Filters       │   │  - By customer   │
│  - Navigation    │   │  - By project    │
└──────────────────┘   │  - By person     │
                       └─────────┬────────┘
                                 │
                                 ▼
                        ┌──────────────────┐
                        │  Chart Rendering │
                        │  (chart_*.py)    │
                        │  - Treemaps      │
                        │  - Bar charts    │
                        │  - Comparisons   │
                        └──────────────────┘
```

## 🏗️ Key Architectural Decisions

### 1. Unified Parquet Files
Both `time_records` and `planned_records` in a single file, distinguished by `record_type` column.

**Benefits:**
- Single file to manage instead of multiple files
- Easier data synchronization
- Simpler data loading logic

### 2. Schema-Driven Validation
YAML schema defines all data requirements, not hardcoded in Python.

**Benefits:**
- Change requirements by editing YAML, not code
- Consistent validation across the app
- Easy to add new record types or fields
- No code changes needed for schema updates

### 3. Session-State Based Data
Data loaded once and stored in Streamlit session state.

**Benefits:**
- Fast interactions (data already in memory)
- Reduced API calls
- Consistent data across reruns

### 4. Centralized Aggregation Functions
All aggregation logic in `processors.py`, not scattered across chart modules.

**Benefits:**
- Easy to maintain consistent metrics
- Single place to add features (e.g., percentages)
- Prevents calculation errors
- Easier to test

## 📋 Documentation Standards

### When Adding Architecture Documentation
1. **Explain the why** - Not just the how
2. **Use diagrams** - Visual representations help understanding
3. **Provide examples** - Real Arkemy code examples
4. **Document trade-offs** - Why this approach over alternatives
5. **Reference related docs** - Link to related architecture decisions

### Structure Template
```markdown
# Architecture Component/Topic

## Overview
What is this component? What problem does it solve?

## Design Decisions
Why was it designed this way?

## Components
What are the key parts?

## Data Flow
How does data move through this?

## Diagram
Visual representation.

## Implementation
How is it implemented in Arkemy?

## File References
Exact locations with line numbers.

## Trade-offs
What compromises were made?

## Future Considerations
Planned improvements or limitations.
```

---

**Last Updated**: 2025-11-18
**Scope**: Core architecture, data models, and system design

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL - READ FIRST
- **Project Location**: `~/code/arkemy_app/arkemy`
- **Branch**: Work directly on `main` branch
- **Test command**: `streamlit run main.py`
- **Repository name**: `arkemy` (clean, professional)

## 🚀 GIT WORKFLOW - SIMPLIFIED
**User is vibe coding, not a Git person - I handle ALL git operations**

### Branch Strategy
- **main** = Production branch (work happens here, end users see this)
- **feature branches** = For experimental features (merge to main when ready)

### My Git Responsibilities
1. **Always check current branch** before any operations
2. **Work on main branch** for normal development
3. **Create feature branches** for larger experimental features
4. **Test locally first** before committing
5. **Handle all git commands** - user never needs to know Git
6. **NEVER deploy without explicit permission** - see Deployment Rules below

### 🚫 CRITICAL: GitHub Push Rules
**NEVER EVER push to GitHub without explicit user consent**

- User often merges to main locally for testing purposes
- Local main branch ≠ ready to push to GitHub
- Merging to main is for local testing workflow, NOT for publishing
- **ONLY push to GitHub when user explicitly says:**
  - "Push to GitHub"
  - "Push to GH"
  - "Sync to GitHub"
  - "Publish to GitHub"
  - OR explicitly approves a plan that includes pushing

**What "merge to main" means:**
- Commit changes to feature branch
- Merge to local main branch
- **STOP** - do NOT push
- Wait for explicit permission to push to GitHub

### Session Start Checklist
- [ ] Check current branch: `git rev-parse --abbrev-ref HEAD`
- [ ] Switch to develop if not already: `git checkout develop`
- [ ] Proceed with development work

## 🚨 DEPLOYMENT RULES - CRITICAL
**Railway deployments automatically commit and push to Git - NEVER deploy without permission**

### Testing Workflow (MANDATORY)
1. **ALWAYS test locally first**: `streamlit run main.py`
2. **Get explicit user permission** before ANY deployment
3. **Separate confirmations required**:
   - "Can I commit these changes to Git?"
   - "Can I deploy to Railway?"

### Railway Deployment Commands
⚠️ **WARNING**: `railway up` automatically commits and pushes to Git repository

**NEVER run these without explicit user permission:**
- `railway up` - Commits, pushes to Git, AND deploys
- `railway deploy` - May also trigger Git operations
- Any Railway deployment command

### Safe Testing Commands
**These are safe to run without permission:**
- `streamlit run main.py` - Local testing only
- `railway logs` - View deployment logs
- `railway status` - Check deployment status
- Git read operations (`git status`, `git log`, etc.)

### Deployment Approval Process
Before ANY Railway deployment:
1. Show user what changes will be committed
2. Ask: "Ready to commit and deploy these changes?"
3. Wait for explicit "yes" or similar confirmation
4. Only then run deployment commands

**REMEMBER**: User wants to test first, commit second, deploy third - all with explicit approval

## 🎯 STREAMLIT DEVELOPMENT GUIDELINES

**This is a Streamlit project. Framework-specific guidelines are loaded from:**
- `~/.claude/streamlit-guidelines.md` (via global CLAUDE.md framework detection)

**Key patterns used in this project:**
- Use `format_func` for display label mapping (see [charts/project_type_charts.py:51](charts/project_type_charts.py#L51))
- Static widget keys without counters (see [charts/project_type_charts.py:13](charts/project_type_charts.py#L13))
- Accept tab reset behavior as expected Streamlit behavior

## Communication Style
- **Chat summaries should be sober, concise and factual**
- **User does not need flair, emojis, or success messages**
- **Avoid phrases like "Perfect!", "Great!", "🚀" or similar excitement**
- **Focus on technical facts and what was accomplished**

## 📚 Documentation & Conditional Loading

**The project has comprehensive documentation - load conditionally based on task context.**

### When Working on Features
- **Project Report** → [@documentation/features/project-report/](documentation/features/project-report/)
- **Project Snapshot** → [@documentation/features/project-snapshot/](documentation/features/project-snapshot/)
- **Cashflow Analysis** → [@documentation/features/cashflow-analysis/README.md](documentation/features/cashflow-analysis/README.md)
- **Tag Parsing** → [@documentation/features/tag-parsing-config.md](documentation/features/tag-parsing-config.md)

### When Working on Architecture
- **Understanding data types and schema** → [@documentation/architecture/data-architecture.md](documentation/architecture/data-architecture.md)
- **Session state issues or adding features** → [@documentation/architecture/session-state-management.md](documentation/architecture/session-state-management.md)
- **Overall system design** → [@documentation/architecture/schema-system.md](documentation/architecture/schema-system.md)

### When Working on Deployment
- **Railway MCP commands** → [@documentation/deployment/railway-mcp-reference.md](documentation/deployment/railway-mcp-reference.md)
- **Production setup and configuration** → [@documentation/deployment/production-deployment.md](documentation/deployment/production-deployment.md)

### When Working on Implementation Patterns
- **Plotly treemaps or charts** → [@documentation/lessons/plotly/](documentation/lessons/plotly/)
  - Treemap percentages: [treemap-percentage-implementation.md](documentation/lessons/plotly/treemap-percentage-implementation.md)
  - Plotly reference: [plotly-reference.md](documentation/lessons/plotly/plotly-reference.md)
- **Streamlit widgets** → [@documentation/lessons/streamlit/](documentation/lessons/streamlit/)
  - Display labels: [format-func-pattern.md](documentation/lessons/streamlit/format-func-pattern.md)

### Navigation Hub
- **Documentation index** → [@documentation/README.md](documentation/README.md)

## Feature Development Protocol
**CRITICAL: DO NOT claim features are "solved" or "complete" without explicit user confirmation**

### Workflow for Feature Work
1. **Implement changes** - Write code, test locally, commit
2. **Report status** - Describe what was done, show the app is running
3. **WAIT for user feedback** - Do NOT assume it's working
4. **User tests and confirms** - They verify the feature works as intended
5. **ONLY THEN** - Mark as complete or move to next iteration

### What Counts as Confirmation
- User explicitly says "looks good", "works", "this is right", "ship it", etc.
- User asks for specific changes (implies they tested)
- Silence from user = **NOT confirmation** - ask what they think

### What Does NOT Count as Confirmation
- App starts without errors
- Code compiles/imports
- Local testing shows no crashes
- "I think it should work"

**Remember**: Just because the feature runs doesn't mean it solves the problem. Wait for the user to tell you.

## Common Development Commands

**Run the application:**
```bash
streamlit run main.py
```

**Install dependencies:**
```bash
pip install -r requirements.txt
```

## 🎯 BUSINESS PURPOSE

### What is Arkemy?
Arkemy is a **project profitability analytics dashboard** for architecture firms that need to:
- **Track actual time spent** on projects vs planned hours
- **Analyze project profitability** in real-time
- **Forecast resource allocation** and capacity planning
- **Compare planned vs actual performance** across projects, people, and time periods

### Core Concepts
- **time_records**: ACTUAL hours worked by people on projects (historical data)
- **planned_records**: FUTURE hours/fees planned for projects (forecasting data)
- **Unified Loading**: Both record types loaded from same file for simplified data management

## Quick Architecture Reference

**For detailed architecture, see**: [@documentation/architecture/](documentation/architecture/)

### Application Entry Points
- `main.py` - Conditional page navigation (localhost vs production)
- `pages/0_Dataset_Selection.py` - Pre-navigation dataset selection (localhost only)

### Global Dataset Selection (Localhost Mode)
1. Shows dataset selector ONLY when `is_localhost() and not csv_loaded`
2. User selects parquet file → loads into `transformed_df` + `transformed_planned_df`
3. Scans for optional CSV files (coworker, hrs/sqm/phase)
4. Sets availability flags → controls which pages appear
5. Dataset reset button in sidebar (localhost only)

**See**: [@documentation/architecture/session-state-management.md](documentation/architecture/session-state-management.md)

### Data Flow Patterns
- **Analytics Dashboard, Cashflow**: Use `transformed_df` directly
- **Project Report, Project Snapshot**: Transform via `transform_dataframes_to_project_report()`
- **Coworker/SQM Reports**: Load from CSV paths if available

**See**: [@documentation/architecture/data-architecture.md](documentation/architecture/data-architecture.md)

### Key Files
- `utils/unified_data_loader.py` - Schema-driven data loading
- `utils/arkemy_schema.yaml` - Central schema definition
- `utils/processors.py` - Core aggregation functions
- `utils/dataset_reset.py` - Dataset switching (localhost only)

## Development Workflow

**Adding new features:**
1. Check existing patterns in [@documentation/features/](documentation/features/)
2. Follow established aggregation patterns (see `utils/processors.py`)
3. Use conditional doc loading above for deep dives
4. Test locally → commit → get user confirmation

**Modifying data handling:**
1. Review [@documentation/architecture/data-architecture.md](documentation/architecture/data-architecture.md)
2. Check schema: `utils/arkemy_schema.yaml`
3. Understand session state: [@documentation/architecture/session-state-management.md](documentation/architecture/session-state-management.md)

**Deploying:**
1. Review [@documentation/deployment/production-deployment.md](documentation/deployment/production-deployment.md)
2. Follow deployment rules above (test → permission → deploy)
3. Check Railway MCP reference if needed: [@documentation/deployment/railway-mcp-reference.md](documentation/deployment/railway-mcp-reference.md)

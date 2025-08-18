# Claude Code Session Summary - Arkemy Production Setup

## Repository Information
- **GitHub Repo**: https://github.com/StuRoys/arkemy
- **Local Path**: `/Users/roark/code/arkemy/`
- **Current Branch**: develop (should always work here)
- **Production Branch**: main (only for deployment)

## User Profile & Workflow
- **User**: Vibe coder, not Git-savvy, wants to avoid deployment complexity
- **My Role**: Handle ALL git operations, Railway deployments, production safety
- **Communication**: User says exactly "Ship to production", "Deploy to prod", "Push to main", or "Ready for users" for production deployment
- **Everything else**: Stays on develop branch (including "this works", "looks good", etc.)

## Branch Strategy & Safety Rules
```
develop branch: All development work happens here
main branch: Production only - merge when user explicitly requests deployment
```

## Railway Deployment Setup
- **Staging**: arkemy-staging (project ID: 0771caf9-aec2-4991-a10f-2c8e4ac5bdef)
  - Deploys from: develop branch
  - Purpose: Test deployment vs local differences
  - Build logs: https://railway.com/project/0771caf9-aec2-4991-a10f-2c8e4ac5bdef/service/4f07a24a-5081-4bb8-85ea-574c38d88986

- **Production**: arkemy-production (project ID: 6cd5ff49-273e-4478-a39c-7faf004d0ccb)
  - Deploys from: main branch
  - Purpose: Live user-facing application
  - Build logs: https://railway.com/project/6cd5ff49-273e-4478-a39c-7faf004d0ccb/service/1a2594c3-1bf8-4dfc-995d-106b1f97610f

## MCP Configuration
- **Railway MCP Server**: Configured in `.claude/mcp.json`
- **Authentication**: Railway CLI authenticated as Sturla Roysland (sturla@roark.no)
- **Status**: Should be active in new sessions for enhanced Railway management

## Session Start Checklist
1. Check current branch: `git rev-parse --abbrev-ref HEAD`
2. Switch to develop if not already: `git checkout develop`
3. Verify Railway MCP tools are available
4. Ready for development work

## Production Audit Results
- **Security**: ✅ Excellent (no vulnerabilities, proper HTML sanitization)
- **Error Handling**: ✅ Robust (comprehensive exception handling)
- **Data Validation**: ✅ Strong (schema validation with type checking)
- **Performance**: ✅ Optimized (extensive caching, memory management)
- **Dependencies**: ✅ Clean (no conflicts, minimal requirements)
- **Environment Config**: ✅ Ready (ARKEMY_DEBUG controls, proper logging)

## Key Commands & Operations
- **Local testing**: `streamlit run main.py`
- **Deploy to staging**: Push develop branch changes
- **Deploy to production**: Only when user explicitly requests with magic words
- **Railway logs**: Use Railway MCP tools (available in new session)
- **Link staging**: `railway link --project arkemy-staging`
- **Link production**: `railway link --project arkemy-production`

## Critical Reminders
- NEVER work directly on main branch
- ALWAYS test on develop first
- User doesn't know Git - I handle everything
- Only explicit production keywords trigger main branch deployment
- Test locally AND on staging before production
- Railway MCP server provides enhanced deployment management capabilities

## File Structure
```
/Users/roark/code/arkemy/
├── .claude/
│   ├── mcp.json (Railway MCP configuration)
│   └── session-summary.md (this file)
├── CLAUDE.md (updated with Git workflow rules)
├── main.py (Streamlit app entry point)
├── requirements.txt (production-ready dependencies)
└── [full codebase] (production-audited and ready)
```

## Current Issue - Deployment Failure
- **Problem**: Deployment failed, need to fetch logs to diagnose
- **Build URL**: https://railway.com/project/0771caf9-aec2-4991-a10f-2c8e4ac5bdef/service/4f07a24a-5081-4bb8-85ea-574c38d88986?id=f8efe130-35f2-430a-bf90-e8bbf02b80af&
- **Status**: Railway MCP tools not available in current session (need restart)
- **Next Steps**: Use `mcp__railway__get-logs` to fetch deployment logs after restart

## Railway MCP Tools Setup
- **Configuration**: Updated in CLAUDE.md with all available commands
- **Status**: MCP server configured but tools not loaded (restart required)
- **Commands Added**: All Railway MCP functions documented for future use
- **Always Latest**: Use `npx -y @railway/mcp-server@latest` for updates

**Last Updated**: 2025-08-17
**Status**: Deployment issue pending - need Railway MCP tools to fetch logs
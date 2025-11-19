# Railway MCP Server - Command Reference

**When to use this guide**: Working with Railway deployment, MCP server setup, or managing Railway infrastructure.

**Reference this file with**: `@documentation/deployment/railway-mcp-reference.md`

---

## Railway MCP Server Overview

The Railway MCP (Model Context Protocol) server provides tools for managing Railway projects, services, environments, and deployments directly through Claude Code.

## Available Commands

### Project Management

**`mcp__railway__list-projects`**
- List all Railway projects in your account
- No arguments required
- Returns project names and IDs

**`mcp__railway__create-project-and-link`**
- Create a new Railway project and link it to current directory
- Automatically sets up project context
- Links local directory to Railway project

### Service Management

**`mcp__railway__list-services`**
- List all services in a Railway project
- Requires project context (linked directory)
- Returns service names, IDs, and deployment status

**`mcp__railway__link-service`**
- Link a Railway service to current directory
- Establishes service context for deployments
- Required before deploying

**`mcp__railway__deploy`**
- Deploy current service to Railway
- **WARNING**: Automatically commits and pushes to Git repository
- **NEVER run without explicit user permission** (see CLAUDE.md Deployment Rules)
- Requires linked service

**`mcp__railway__deploy-template`**
- Deploy a template from Railway's template library
- Useful for quick starts with popular frameworks
- Browse templates at https://railway.app/templates

### Environment Management

**`mcp__railway__create-environment`**
- Create a new environment (staging, production, etc.)
- Environments isolate deployments and variables
- Can have separate configurations per environment

**`mcp__railway__link-environment`**
- Link an environment to current directory
- Required for environment-specific operations
- Affects which environment receives deployments

### Configuration & Variables

**`mcp__railway__list-variables`**
- List all environment variables for current service/environment
- Shows variable names and values
- Sensitive values may be masked

**`mcp__railway__set-variables`**
- Set or update environment variables
- Format: key-value pairs
- Changes apply immediately to linked environment

**`mcp__railway__generate-domain`**
- Generate a railway.app subdomain for your service
- Provides public URL: `https://yourservice.railway.app`
- Free tier includes one domain per service

### Monitoring

**`mcp__railway__get-logs`**
- Retrieve build or deployment logs
- Useful for debugging failed deployments
- Can filter by build ID or deployment ID

## MCP Server Setup

Add to Claude Code MCP configuration (`~/.config/claude_code/mcp.json` or project `.claude/mcp.json`):

```json
{
  "mcpServers": {
    "railway-mcp-server": {
      "command": "npx",
      "args": ["-y", "@railway/mcp-server"]
    }
  }
}
```

## Troubleshooting

**MCP tools not available?**
- Restart Claude Code to reload MCP servers
- Verify Railway CLI is installed: `railway --version`
- Check MCP server is configured correctly

**Authentication issues?**
- Login to Railway CLI: `railway login`
- Verify authentication: `railway whoami`

**Deployment fails?**
- Check logs: `mcp__railway__get-logs`
- Verify service is linked: `mcp__railway__list-services`
- Ensure git repo is up to date (Railway requires committed changes)

## Related Documentation

- Production deployment workflow: [production-deployment.md](production-deployment.md)
- Railway deployment rules: See CLAUDE.md "Deployment Rules" section
- Railway official docs: https://docs.railway.com

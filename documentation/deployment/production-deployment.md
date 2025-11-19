# Production Deployment Guide

**When to use this guide**: Setting up production environment, deploying to Railway, or configuring production data volumes.

**Reference this file with**: `@documentation/deployment/production-deployment.md`

---

## Production Environment Configuration

### Environment Variables

Set the following environment variable to disable debug mode in production:

```bash
export ARKEMY_DEBUG=false
```

**What this does:**
- Disables debug information display in UI
- Hides verbose logging and error traces
- Optimizes performance for production use

**Where to set:**
- Railway: Project Settings → Variables
- Local production testing: `.env` file (not committed)
- Docker: Environment variables in container config

### Data Volume Setup

**Critical**: Production requires persistent data storage.

**Data Location:**
- Mount data files to `/data` directory in production
- Application checks `/data` first (Railway volume)
- Falls back to `./data` (local development)
- Final fallback: `~/temp_data`

**File Format:**
- Parquet files with currency code in filename (e.g., `data_NOK.parquet`)
- Unified schema with both `time_record` and `planned_record` data
- Use `*_regular.parquet` and `*_adjusted.parquet` for dual dataset support

**Railway Volume Configuration:**
```bash
# Create a volume in Railway dashboard
# Mount point: /data
# Size: Based on data needs (typically 1-5 GB)
```

**Dataset Versioning:**
- `data_NOK_regular.parquet` - Standard financial metrics
- `data_NOK_adjusted.parquet` - Modified rates, costs, and profits
- Application auto-detects and prefers adjusted values when available

### Upload Functionality

**Production vs Development:**
- **Production**: Auto-loads from `/data` volume (no upload UI needed)
- **Development**: Shows dataset selection page for local file selection
- **Localhost detection**: Based on hostname (see `utils/localhost_selector.py`)

**Disabling Upload in Production:**
- Upload feature automatically hidden in production mode
- No code changes needed - environment-based detection
- Dataset Selection page only shows in localhost mode

## Security Considerations

### Data Safety
- **No user input in HTML**: All unsafe HTML usage is for internal styling only
- **No hardcoded credentials**: All secrets in environment variables
- **No sensitive data exposure**: Debug mode disabled in production

### Authentication
- Currently: No authentication (internal tool)
- Future: Can add Streamlit authentication if needed
- Consider: Railway basic auth for additional layer

### Logging
- Print statements replaced with proper logging
- Debug mode controlled via `ARKEMY_DEBUG` environment variable
- Error logging to stderr for Railway log capture

## Performance Optimization

### Caching Strategy
- Application uses Streamlit `@st.cache_data` for data operations
- Cache signatures include `data_version` to prevent stale data
- Memory management with garbage collection for large datasets

### Data Loading
- Automatic Parquet file detection and loading
- Lazy loading: Only load data when needed
- Shared session state across pages reduces redundant loads

### Railway Resource Recommendations
- **Memory**: 512 MB minimum, 1 GB recommended
- **CPU**: Shared vCPU sufficient for most workloads
- **Region**: Choose closest to primary users for lower latency

## Deployment Workflow

**CRITICAL**: See CLAUDE.md "Deployment Rules" section for workflow.

### Pre-Deployment Checklist
- [ ] Test locally: `streamlit run main.py`
- [ ] Verify all features work with production-like data
- [ ] Check debug mode is disabled
- [ ] Confirm data volume is mounted and accessible
- [ ] Review environment variables are set correctly

### Deployment Steps
1. **Commit changes** to feature branch
2. **Merge to main** branch (local testing)
3. **Test merged code** locally on main branch
4. **Get user permission** to deploy
5. **Push to GitHub** (if approved)
6. **Deploy via Railway** MCP or CLI

**Never skip user permission** - See CLAUDE.md for full deployment protocol.

### Post-Deployment Verification
- [ ] Check Railway logs for errors: `mcp__railway__get-logs`
- [ ] Verify application starts successfully
- [ ] Test data loading from `/data` volume
- [ ] Confirm all pages render correctly
- [ ] Validate currency detection and formatting

## Monitoring & Troubleshooting

### Railway Logs
```bash
# View recent logs
railway logs

# Or via MCP
mcp__railway__get-logs
```

### Common Issues

**Application won't start:**
- Check Railway logs for import errors
- Verify all dependencies in `requirements.txt`
- Confirm Python version compatibility

**Data not loading:**
- Verify `/data` volume is mounted correctly
- Check file permissions on volume
- Confirm parquet files exist and are readable

**Performance issues:**
- Check Railway resource usage
- Review memory limits
- Consider upgrading Railway plan

**Currency not detected:**
- Verify filename includes currency code (e.g., `data_NOK.parquet`)
- Check supported currencies in `utils/currency_formatter.py`
- Manual selection available in Admin page

## Rollback Procedure

**If deployment fails:**

1. Check Railway logs for errors
2. If critical: Revert to previous deployment via Railway dashboard
3. Fix issues locally and test
4. Redeploy when ready

**Railway Rollback:**
- Railway Dashboard → Deployments → Select previous deployment → Redeploy

## Related Documentation

- Railway MCP commands: [railway-mcp-reference.md](railway-mcp-reference.md)
- Deployment rules and workflow: See CLAUDE.md "Deployment Rules" section
- Data architecture: [../architecture/data-architecture.md](../architecture/data-architecture.md)
- Session state management: [../architecture/session-state-management.md](../architecture/session-state-management.md)

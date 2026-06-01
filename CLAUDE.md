# CLAUDE.md — netbox-pdm

## Workspace Context

This file lives at `/root/personal-context/nmulticloud-context/netbox-pdm/CLAUDE.md` inside the `personal-context` workspace.
Workspace guidance: `/root/personal-context/CLAUDE.md`.
Per-repo deep-dive: `/root/personal-context/claude-reference/nmulticloud-context.md`.
Submodule layout and cross-repo links: `/root/personal-context/claude-reference/dependency-map.md`.

---

NetBox plugin for netbox-pdm integration with netbox.nmulti.cloud.

## Installation

```bash
pip install -e .
python manage.py migrate
python manage.py collectstatic
```

## Development

- Pre-commit: `python -m compileall . && ruff check . && pytest tests/`
- Type checking: `pyright .`
- Full test suite: `pytest tests/ -v`

## Architecture

See the plugin's code structure:
- `netbox-pdm_plugin/` — main plugin package
- `netbox-pdm_plugin/models/` — Django ORM models
- `netbox-pdm_plugin/views/` — Django views and viewsets
- `netbox-pdm_plugin/api/` — DRF serializers and API endpoints
- `netbox-pdm_plugin/templates/` — Django HTML templates
- `tests/` — unit and integration tests

## Automatic Production Deployment

**Starting with the deploy-production workflow**, new commits to `main` automatically deploy to `netbox.nmulti.cloud`.

**Deploy job in `.gitea/workflows/deploy-production.yml`:**
- Triggers on `push: [main]` branch updates
- Also supports manual dispatch via `workflow_dispatch` with optional `ref` input
- Runs on `prod-deploy` runner with SSH access to production host
- Executes: `ssh nmc-prod-207 -- deploy-plugin pdm "$REF"`

**Deploy parameters:**
- REF: can be a version tag (v0.1.0), branch name (main/develop), or 7+ character commit SHA
- Default: uses current commit SHA if not specified in manual dispatch

**Security hardening:**
- REF is passed via environment variable, not direct GitHub Actions context interpolation
- Bash case statement validates ref format before SSH (whitelist: version tags, branch names, commit SHAs)
- StrictHostKeyChecking=accept-new prevents MITM attacks
- Quoted variable interpolation prevents shell injection

**Deployment on production server (`nmc-prod-207`):**
1. Git fetch/checkout of the specified ref in the plugin submodule
2. pip install -e to refresh editable install and pick up new dependencies
3. manage.py migrate to apply any pending migrations
4. manage.py collectstatic to collect new/updated static files
5. systemctl reload netbox-production (graceful gunicorn reload)
6. systemctl restart netbox-rq (RQ worker restart for code changes)
7. Health check: curl -sf http://127.0.0.1:18001/api/ to verify service is responding

**Monitoring and verification:**
- Watch the `deploy-production.yml` workflow run in Gitea Actions
- Check the `deploy` job logs for SSH output and health check results
- Verify production is healthy: `ssh nmc-prod-207 -- health netbox`
- Check service logs: `ssh nmc-prod-207 -- logs netbox`

**Manual deployment trigger:**
```bash
# Deploy a specific tag or branch via workflow dispatch
nms git actions run netbox-pdm .gitea/workflows/deploy-production.yml \
  -r main -f ref=v0.1.0

# Or SSH directly to production
ssh nmc-prod-207 -- deploy-plugin pdm v0.1.0
```

For comprehensive deploy infrastructure documentation, see `/root/personal-context/nmulticloud-context/CLAUDE.md` section "Automatic Plugin Deployment to Production".

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

## Security and Sync Invariants

- `PDMEndpointSyncView` is a mutating queue action. It must resolve endpoints
  through NetBox object visibility and require `core.add_job`; never authorize
  sync enqueue with `netbox_proxbox.view_pdmendpoint` alone.
- `PDMEndpointForm` must use `PasswordInput(render_value=False)` for
  `token_secret`. Blank token-secret submissions on edit preserve the stored
  value; stored secrets must not be rendered into HTML or logs.
- `PDMSyncJob` reconciles PDM remotes by creating, updating, and pruning stale
  `PDMRemote` rows scoped to the endpoint. Job results should include created,
  updated, deleted, and total counts.

## Architecture

See the plugin's code structure:
- `netbox-pdm_plugin/` — main plugin package
- `netbox-pdm_plugin/models/` — Django ORM models
- `netbox-pdm_plugin/views/` — Django views and viewsets
- `netbox-pdm_plugin/api/` — DRF serializers and API endpoints
- `netbox-pdm_plugin/templates/` — Django HTML templates
- `tests/` — unit and integration tests

## Automatic Staging/Production Deployment

The deploy workflow treats `develop` as staging and `main` as production.
Pushes to `develop` deploy `netbox-pdm` to
`https://staging.netbox.nmulti.cloud`; pushes to `main` deploy to
`https://netbox.nmulti.cloud`.

**Deploy job in `.gitea/workflows/deploy-production.yml`:**
- Triggers on `push: [develop, main]` branch updates
- Also supports manual dispatch via `workflow_dispatch` with optional `ref` and optional `environment` choice
- Runs on `prod-deploy` runner with access to the NetBox deploy host
- For staging, executes `/opt/nmulticloud/deploy/bin/deploy-netbox-plugin-staging netbox-pdm "$REF"`
- For production, executes `/opt/nmulticloud/deploy/bin/deploy-netbox-plugin pdm "$REF"` when local, or falls back to `ssh nmc-prod-207 -- deploy-plugin pdm "$REF"`

**Deploy parameters:**
- REF: can be a version tag (v0.1.0), branch name (main/develop), or 7+ character commit SHA
- Default: uses current commit SHA if not specified in manual dispatch

**Security hardening:**
- REF is passed via environment variable, not direct GitHub Actions context interpolation
- Bash case statement validates ref format before SSH (whitelist: version tags, branch names, commit SHAs)
- StrictHostKeyChecking=accept-new prevents MITM attacks
- Quoted variable interpolation prevents shell injection

**Deployment on target server (`nmc-prod-207`):**
1. Git fetch/checkout of the specified ref in the plugin submodule
2. pip install -e to refresh editable install and pick up new dependencies
3. manage.py migrate to apply any pending migrations
4. manage.py collectstatic to collect new/updated static files
5. Reload/restart the target NetBox web and worker services
6. Health check the selected endpoint to verify the service is responding

**Monitoring and verification:**
- Watch the `deploy-production.yml` workflow run in Gitea Actions
- Check the `deploy` job logs for SSH output and health check results
- Verify staging: `curl -fsS https://staging.netbox.nmulti.cloud/api/`
- Verify production: `curl -fsS https://netbox.nmulti.cloud/api/`
- Check service logs: `ssh nmc-prod-207 -- logs netbox`

**Manual deployment trigger:**
```bash
# Deploy a specific tag or branch via workflow dispatch
nms git actions run netbox-pdm .gitea/workflows/deploy-production.yml \
  -r main -f environment=production -f ref=v0.1.0

# Or SSH directly to production
ssh nmc-prod-207 -- deploy-plugin pdm v0.1.0
```

For comprehensive deploy infrastructure documentation, see `/root/personal-context/nmulticloud-context/CLAUDE.md` section "Automatic Plugin Deployment to Production".

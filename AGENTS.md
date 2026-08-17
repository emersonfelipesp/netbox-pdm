# CLAUDE.md — netbox-pdm — AGENTS.md Mirror

This file mirrors the sibling `CLAUDE.md` guidance for agents that read `AGENTS.md`. Treat `CLAUDE.md` as the source material; the content below preserves the current guide.

## Source

@CLAUDE.md

---

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

See the plugin's code structure (full deep dive in `docs/architecture.md`):
- `netbox_pdm/` — main plugin package (flat modules, no `views/`/`api/` subpackages)
- `netbox_pdm/models/` — only `PdmPluginSettings` (singleton settings row); the
  `PDMEndpoint`/`PDMRemote` ORM models live in the sibling `netbox-proxbox`
  repo, not here
- `netbox_pdm/views.py`, `forms.py`, `tables.py`, `filtersets.py` — views,
  forms, tables, and filtersets over netbox-proxbox's `PDMEndpoint`/`PDMRemote`
  models
- `netbox_pdm/jobs.py` — `PDMSyncJob` (RQ background sync job)
- `netbox_pdm/services/` — `branch_lifecycle.py` (netbox-branching integration)
- `netbox_pdm/navigation.py`, `sitemap.py`, `urls.py` — NetBox plugin
  registration glue
- No `api/` subpackage — `netbox-pdm` registers no DRF viewsets of its own; the
  REST API is served by `netbox-proxbox`
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

## NetBox compatibility: two tiers, one shared module

`netbox_pdm/compat.py` is the single declaration of which NetBox releases this plugin
supports, and `PluginConfig.min_version`/`max_version` are sourced from it rather
than re-typed as literals:

- **stable** `4.5.8` – `4.6.99` — certified, CI-gated, silent;
- **experimental** `4.7.0` – `4.7.99` — loads and runs with no configuration
  change, and emits system check `netbox_pdm.W001` (a **Warning**, never an Error)
  plus one `ready()` log line. A version that cannot be classified reports
  `netbox_pdm.W002` rather than passing silently. Operators silence the notice with
  Django's stock `SILENCED_SYSTEM_CHECKS`; the plugin adds no setting of its own.

**`compat.py` is vendored byte-identically across `netbox-proxbox`,
`netbox-ceph`, `netbox-packer`, `netbox-pbs`, and `netbox-pdm`.** Change it in
one repo and you must change it in all five, bumping `CONTRACT_VERSION` when the
contract itself moves. Verify with
`sha256sum */compat.py` across the five checkouts — the
`proxbox-stack-code-review` skill runs that drift check.

Two hard rules:

1. **No Django import at module scope in `compat.py`.** NetBox imports it while
   `netbox/settings.py` is still executing, so every Django touch lives inside a
   function.
2. **Upgrading to NetBox 4.7 means upgrading the whole plugin family.**
   `settings.py` *catches* `IncompatiblePluginError`, warns, and **skips** the
   offending plugin — NetBox still starts. The failure is therefore silent: the
   plugin's views, API routes and jobs are simply absent, and a health probe
   against NetBox still passes. Verify registration with `apps.is_installed()`
   after any upgrade rather than trusting that NetBox came up.

Beta release strings are why the ceiling is `4.7.99` and not something
pre-release-shaped: `release.yaml` at tag `v4.7.0-beta1` reads `version: "4.7.0"`
with `designation: "beta1"`, and the plugin gate compares against
`RELEASE.version` — the bare `"4.7.0"`. `RELEASE.full_version`
(`"4.7.0-beta1"`) is display only.

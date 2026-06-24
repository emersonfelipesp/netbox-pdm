# Version 0.0.2

## What's new

This release delivers the full PDM inventory and sync feature set:

### Models and views

- **PDMEndpoint** and **PDMRemote** list, detail, edit, delete, and changelog
  pages provided by `netbox-pdm` over the models defined in `netbox-proxbox`.
- Filterable, searchable tables for both object types.
- Endpoint detail page embeds a related-remotes table.

### Sync job

- **PDMSyncJob** (RQ, `default` queue, 10-minute timeout) dispatches per-endpoint
  via `PDMSyncJob.enqueue(endpoint_pk=<pk>)`.
- Sync calls the PDM API **directly via `proxmox-sdk`** `SyncPDMClient` —
  no `proxbox-api` process is required.
- Token parsing uses `proxmox_sdk.sdk.auth.token.parse_token_id()` to split
  `user@realm!tokenname` from the `token_id` field.
- `verify_ssl=False` emits a CRITICAL log entry per sync; always use a
  trusted certificate or pin the fingerprint in production.

### Branching support

- Optional integration with `netbox-branching`: set `branching_enabled=True`
  in `PdmPluginSettings` to run syncs inside an isolated branch.
- `branch_name_prefix` (default `pdm-sync`) and `branch_on_conflict`
  (`fail` or `acknowledge`) are configurable from the plugin settings page.

### Plugin settings

- `PdmPluginSettings` singleton (via `get_solo()`) stores branching
  configuration and reserved `proxbox_api_url` / `proxbox_api_key` fields
  (unused in v0.0.2; present for future proxbox-api integration).

### CI and packaging

- Gitea CI workflow: ruff lint, `compileall`, pytest, deploy-on-push.
- GitHub mirror via `mirror-github.yml`.

## Compatibility

| NetBox | netbox-pdm | netbox-proxbox | Python |
| --- | --- | --- | --- |
| v4.5.8 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.5.9 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.0 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.1 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.2 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.3 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |

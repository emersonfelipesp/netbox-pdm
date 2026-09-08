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
- Sync reconciles remote inventory by creating/updating rows reported by PDM
  and deleting stale rows that are no longer present in the PDM response.
- The UI sync action requires endpoint visibility plus `core.add_job`, matching
  NetBox job-queue authorization expectations.
- Token parsing uses `proxmox_sdk.sdk.auth.token.parse_token_id()` to split
  `user@realm!tokenname` from the `token_id` field.
- Endpoint edit forms never render the stored token secret into HTML; leaving
  the token-secret field blank preserves the stored value.
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

### Post-release fix: NetBox 4.5.x migration graph

- `netbox_pdm/migrations/0002_pdmpluginsettings_tags_and_more.py` depended on
  `extras.0138_customfieldchoiceset_choice_colors`, a NetBox-4.6-only
  migration node. This raised `NodeNotFoundError` on a real NetBox 4.5.x
  install despite v0.0.2 already certifying NetBox v4.5.8 support. The
  dependency was retargeted to `extras.0134_owner` (present in both 4.5.x and
  4.6.x), and `tests/test_migration_dependencies.py` was added as a regression
  guard against future migration nodes that only exist on one side of the
  supported NetBox range.

## Compatibility

| NetBox | netbox-pdm | netbox-proxbox | Python |
| --- | --- | --- | --- |
| v4.5.8–v4.6.6 | v0.0.2 | >=0.0.25.post2,<0.1.0 | 3.12+ |
| v4.7.0 GA | v0.0.2 | >=0.0.25.post2,<0.1.0 | 3.12+ |

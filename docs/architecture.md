# Architecture

## Overview

`netbox-pdm` is a **thin view/job layer** over models that live in
`netbox-proxbox`.  The two primary data models —`PDMEndpoint` and `PDMRemote`
— are defined and migrated by `netbox-proxbox`; `netbox-pdm` contributes the
UI views, forms, tables, filtersets, sync job, and navigation menu over them.

```
netbox-proxbox  ←─── model ownership (PDMEndpoint, PDMRemote)
     │
netbox-pdm  ─── views / forms / tables / filtersets / jobs / navigation
     │
     └── PDMSyncJob  ──→ proxmox-sdk SyncPDMClient  ──→ PDM API
```

## Models

### PDMEndpoint *(defined in netbox-proxbox)*

Represents one Proxmox Datacenter Manager instance.  Key fields:

| Field | Description |
| --- | --- |
| `name` | Unique display name |
| `ip_address` | FK → `ipam.IPAddress` (used as PDM host when `domain` is blank) |
| `domain` | Hostname override |
| `port` | Default `8443` |
| `token_id` | PDM API token ID in `user@realm!tokenname` format |
| `token_secret` | Secret part of the API token |
| `fingerprint` | Optional TLS fingerprint for certificate pinning |
| `verify_ssl` | Whether to verify the TLS certificate (default `True`) |
| `enabled` | Gates sync — disabled endpoints are skipped |
| `allow_writes` | Reserved for future write-back support |

`PDMEndpoint` also has optional FKs to `dcim.Site` and `tenancy.Tenant`, and
an M2M to `ProxmoxEndpoint` and `PBSEndpoint` for federation context.

### PDMRemote *(defined in netbox-proxbox)*

Represents one remote registered in PDM (a PVE cluster or PBS instance).

| Field | Description |
| --- | --- |
| `pdm_endpoint` | FK → `PDMEndpoint` (CASCADE) |
| `name` | Remote name as reported by PDM |
| `type` | `pve` (Proxmox VE) or `pbs` (Proxmox Backup Server) |
| `hostname` | Hostname of the remote |
| `fingerprint` | TLS fingerprint of the remote |
| `version` | Last-reported version string |
| `last_seen_at` | Timestamp of most recent successful sync |
| `linked_proxmox_endpoint` | Optional FK → `ProxmoxEndpoint` (PVE only) |
| `linked_pbs_endpoint` | Optional FK → `PBSEndpoint` (PBS only) |

Unique constraint: `(pdm_endpoint, name)`.  The `clean()` method enforces
that only `pve`-type remotes may link a Proxmox endpoint.

### PdmPluginSettings *(defined here, in netbox-pdm)*

Singleton settings row controlling sync behaviour.  Access via
`PdmPluginSettings.get_solo()`.

| Field | Default | Description |
| --- | --- | --- |
| `proxbox_api_url` | `""` | Fallback proxbox-api URL (future use) |
| `proxbox_api_key` | `""` | Fallback proxbox-api key (future use) |
| `branching_enabled` | `False` | Run syncs inside a netbox-branching branch |
| `branch_name_prefix` | `"pdm-sync"` | Prefix for auto-created branch names |
| `branch_on_conflict` | `"fail"` | Conflict policy: `fail` or `acknowledge` |

## REST API

`netbox-pdm` registers **no** DRF viewsets of its own.  The
`PDMEndpoint` and `PDMRemote` REST API is served by **`netbox-proxbox`**:

| Resource | URL |
| --- | --- |
| PDM endpoints | `/api/plugins/proxbox/endpoints/pdm/` |
| PDM remotes | `/api/plugins/proxbox/pdm-remotes/` |

The `netbox-pdm` plugin UI mounts at `/plugins/pdm/` and provides:

| Page | URL |
| --- | --- |
| Endpoint list | `/plugins/pdm/endpoints/` |
| Endpoint detail | `/plugins/pdm/endpoints/<pk>/` |
| Trigger sync | `/plugins/pdm/endpoints/<pk>/sync/` (POST) |
| Remote list | `/plugins/pdm/remotes/` |
| Remote detail | `/plugins/pdm/remotes/<pk>/` |

## Sync flow

```
PDMSyncJob.enqueue(endpoint_pk=<pk>)
    ↓
1. Load PDMEndpoint from netbox-proxbox (checks .enabled)
2. Build SyncPDMClient (proxmox-sdk)
   - host  = endpoint.domain  OR  endpoint.ip_address.address.ip
   - token = "user@realm!tokenname" parsed via parse_token_id()
   - token_secret = endpoint.token_secret
   - port  = endpoint.port  (default 8443)
   - verify_ssl = endpoint.verify_ssl
3. client.remotes.list()  →  PDM /remotes API
4. For each remote:
   PDMRemote.objects.update_or_create(
       pdm_endpoint=endpoint,
       name=remote_name,
       defaults={type, hostname, fingerprint, version, last_seen_at, ...}
   )
5. Delete stale PDMRemote rows for the endpoint when their names are absent
   from the current PDM response
6. Persist `job.data["result"]` and log created / updated / deleted counts
```

If `branching_enabled` is `True` in `PdmPluginSettings`, the sync runs
inside a `netbox-branching` branch (prefix from `branch_name_prefix`) and
merges on success according to `branch_on_conflict`.  The job fetches data
from PDM before branch creation, then activates the branch context only while
reconciling `PDMRemote` rows so the direct ORM writes are isolated correctly.
If reconciliation fails, the branch is left open for operator inspection.

## Dispatch invariant

Always dispatch the job with `endpoint_pk` in `kwargs`, **never** with
`instance=`:

```python
# Correct
PDMSyncJob.enqueue(endpoint_pk=endpoint.pk)

# Wrong — PDMEndpoint is not a jobs-assignable object type
PDMSyncJob.enqueue(instance=endpoint)  # raises TypeError
```

The UI sync action is mutating even though PDM itself remains read-only. The
POST endpoint first resolves the endpoint through NetBox's `restrict(user,
"view")` object-visibility queryset and then requires `core.add_job` before it
queues `PDMSyncJob`.

## Token format

PDM API tokens use the format `user@realm!tokenname:secret`.  In the
`PDMEndpoint` model this is split across two fields:

| Model field | Contains |
| --- | --- |
| `token_id` | `user@realm!tokenname`  (e.g. `root@pam!my-token`) |
| `token_secret` | The secret value after the colon |

`proxmox-sdk`'s `parse_token_id()` helper handles the `!` split.

## Security notes

- When `verify_ssl=False` on a `PDMEndpoint`, the sync job emits a
  **CRITICAL** log entry.  This setting should only be used in air-gapped
  or internal deployments where a proper CA certificate cannot be added.
- Log messages use a safe endpoint label and do not stringify the full endpoint
  object, so token fields are not emitted through object representations.
- API token secrets remain stored by the owning `netbox-proxbox` model and are
  protected by NetBox's own access controls.
- Endpoint edit forms use `PasswordInput(render_value=False)` so the stored
  token secret is never rendered into HTML. On edits, submitting the token
  secret field blank preserves the stored value.
- Triggering sync requires `core.add_job` in addition to endpoint visibility;
  `view_pdmendpoint` alone can inspect visible inventory but cannot enqueue RQ
  sync work.

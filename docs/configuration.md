# Configuration

## Plugin settings

After installation, open **Plugins → PDM → Plugin Settings** in the NetBox
UI to configure sync behaviour.  Settings are stored in the
`PdmPluginSettings` singleton (accessed via `PdmPluginSettings.get_solo()`).

### proxbox-api URL / key

These fields are reserved for a future integration that will allow
`netbox-pdm` to delegate certain operations through a running `proxbox-api`
instance.  Leave them blank in v0.0.2 — sync uses `proxmox-sdk` directly.

### Branching (optional)

`netbox-pdm` integrates with the
[`netbox-branching`](https://github.com/netboxlabs/netbox-branching) plugin to
isolate sync changes in a branch before committing them to the main NetBox
database.

| Setting | Default | Effect |
| --- | --- | --- |
| **Branching enabled** | `False` | Run syncs inside a branch |
| **Branch name prefix** | `pdm-sync` | Prefix for auto-created branch names |
| **Branch merge conflict policy** | `fail` | What to do when merge conflicts occur |

**Conflict policies:**

- `fail` — leave the branch open for manual review if there are conflicts.
- `acknowledge` — merge despite conflicts (last-write-wins).

!!! note
    `netbox-branching` must be installed and enabled in your NetBox instance
    to use branch-isolated sync.  If it is not installed, `branching_enabled`
    has no effect.

## PDMEndpoint configuration

Each Proxmox Datacenter Manager instance is modelled as a `PDMEndpoint`.
Navigate to **Plugins → PDM → Endpoints → Add** to create one.

| Field | Required | Notes |
| --- | --- | --- |
| Name | Yes | Unique display label |
| IP Address | Cond. | Used as the PDM host when Domain is blank |
| Domain | Cond. | Hostname override; takes precedence over IP |
| Port | No | Default `8443` |
| Token ID | Yes | `user@realm!tokenname`  (e.g. `root@pam!my-token`) |
| Token Secret | Yes | Secret value from the PDM API token |
| Fingerprint | No | TLS fingerprint for certificate pinning |
| Verify SSL | No | Default `True`; set `False` only for internal CAs |
| Enabled | No | Default `True`; disabled endpoints are skipped |

!!! warning "TLS verification"
    Setting **Verify SSL** to `False` disables TLS certificate verification
    and emits a CRITICAL log entry on every sync.  Always use a trusted
    certificate or pin the fingerprint instead.

## Running a sync

Sync is triggered per-endpoint.  From the endpoint detail page, click
**Sync** to enqueue a `PDMSyncJob`.  The job runs in the NetBox RQ worker
queue (`default`) with a 10-minute timeout.

To trigger a sync programmatically:

```python
from netbox_pdm.jobs import PDMSyncJob

PDMSyncJob.enqueue(endpoint_pk=<endpoint_pk>)
```

## Permissions

`netbox-pdm` uses the permissions defined on the `netbox-proxbox` models.
Assign these via **Admin → Permissions**:

| Action | Permission |
| --- | --- |
| View endpoint list / detail | `netbox_proxbox.view_pdmendpoint` |
| Add / edit endpoints | `netbox_proxbox.add_pdmendpoint` / `change_pdmendpoint` |
| View remote list / detail | `netbox_proxbox.view_pdmremote` |
| Edit remotes | `netbox_proxbox.change_pdmremote` |
| Delete | `netbox_proxbox.delete_pdmendpoint` / `delete_pdmremote` |

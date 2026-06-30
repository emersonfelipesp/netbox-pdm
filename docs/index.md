# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** remotes
(PVE clusters and PBS instances federated by PDM) into NetBox.

`netbox-pdm` is a companion plugin to
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox).
It provides views, sync jobs, forms, tables, and filtersets over the
`PDMEndpoint` and `PDMRemote` models that are **defined in `netbox-proxbox`**.
It does **not** require a running `proxbox-api` instance — sync connects
directly to the PDM API using
[`proxmox-sdk`](https://github.com/emersonfelipesp/proxmox-sdk).

## How it works

```
NetBox  (PDMSyncJob — background RQ job)
    │  SyncPDMClient (proxmox-sdk)
    ▼
Proxmox Datacenter Manager API  →  /remotes endpoint
    │
    ▼
PDMRemote rows created/updated in NetBox
```

The `PDMSyncJob` builds a `SyncPDMClient` from the `PDMEndpoint` credentials
(token format `user@realm!tokenname:secret`), calls the PDM remotes list,
and `update_or_create`s `PDMRemote` rows in NetBox.  No `proxbox-api`
process is required for sync.

## Scope

v0.0.2 delivers:

- Read-only **PDMEndpoint** and **PDMRemote** inventory views: list, detail,
  edit, delete, and changelog.
- **PDMSyncJob** background RQ job with per-endpoint dispatch.
- Optional [**netbox-branching**](https://github.com/netboxlabs/netbox-branching)
  integration: sync runs inside a branch and merges on success.
- Packaging, docs, CI pipelines, and certification evidence.

## Compatibility

| NetBox | netbox-pdm | netbox-proxbox | Python |
| --- | --- | --- | --- |
| v4.5.8 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.5.9 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.0 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.1 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.2 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.3 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.4 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |

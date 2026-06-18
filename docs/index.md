# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** inventory
into NetBox through the
[`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api) backend.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) and
reuses its backend context, branch lifecycle, endpoint relationships, and
job conventions.
Install `netbox-proxbox` alongside `netbox-pdm` as a NetBox peer plugin; PDM
keeps only `proxmox-sdk` in its Python dependency set so stack installs can
resolve one shared Pydantic minor line.

## Scope

v0.0.2 provides read-only PDM endpoint and remote inventory views, sync job
wiring, packaging, docs, tests, and CI pipelines.

## Compatibility

| NetBox | netbox-pdm | netbox-proxbox | Python |
| --- | --- | --- | --- |
| v4.5.8 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.5.9 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.0 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.1 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.2 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.3 | v0.0.2 | >=0.0.18,<0.1.0 | 3.12+ |

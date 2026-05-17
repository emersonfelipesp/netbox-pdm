# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** inventory
into NetBox through the
[`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api) backend.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) and
reuses its backend context, branch lifecycle, endpoint relationships, and
job conventions.

## Scope

v0.0.1 is a **scaffold** release: NetBox plugin registration, navigation,
overview page, packaging, docs, tests, and CI pipelines. Models and sync
views land in subsequent releases.

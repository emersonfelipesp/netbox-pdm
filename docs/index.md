# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** inventory
into NetBox through the
[`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api) backend.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) and
reuses its backend context, branch lifecycle, endpoint relationships, and
job conventions.

## Scope

v0.0.1.post1 is a **scaffold** release: NetBox plugin registration,
navigation, overview page, packaging, docs, tests, and CI pipelines. Models and
sync views land in subsequent releases.

## Compatibility

| NetBox | netbox-pdm | netbox-proxbox | Python |
| --- | --- | --- | --- |
| v4.5.8 | v0.0.1.post1 | >=0.0.18,<0.1.0 | 3.12+ |
| v4.6.1 | v0.0.1.post1 | >=0.0.18,<0.1.0 | 3.12+ |

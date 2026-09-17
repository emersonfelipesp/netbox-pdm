# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** remote
inventory into NetBox. The current sync path connects directly to PDM through
`proxmox-sdk`'s `SyncPDMClient`; it does not use `proxbox-api`.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox); it
reuses the `PDMEndpoint` and `PDMRemote` models owned by `netbox-proxbox`.
The local `proxbox_api_url` and `proxbox_api_key` settings are reserved for a
future integration and are unused by the current sync job.
`netbox-proxbox` remains a required NetBox peer plugin in `PLUGINS` and a
Python package dependency. Fail-closed branch isolation is guaranteed across
the supported `netbox-proxbox` range. Version 0.0.27 and later supply the typed
branching decision consumed by this plugin; older supported versions use the
fail-closed runtime-probe fallback.

## Status

`netbox-pdm` v0.0.2 ships PDM endpoint and remote inventory views, sync job
wiring, and the proxmox-sdk-backed PDM client path. PDM-managed SDN zones and
VNets are not implemented. The plugin never writes
configuration back to PDM; sync reconciles NetBox inventory rows only.

Security and reconciliation behavior:

- Triggering endpoint sync requires both endpoint visibility and `core.add_job`.
- PDM token secrets are never rendered back into endpoint edit forms; leaving
  the field blank preserves the stored secret.
- Sync creates, updates, and prunes `PDMRemote` rows so remotes removed from
  PDM do not remain as stale NetBox inventory.

## Branch isolation

Branch isolation is disabled by default. When `PdmPluginSettings.branching_enabled`
is `False`, sync writes directly to the main schema. When it is `True`, sync
requires a loaded, working `netbox-branching` runtime and performs reconciliation
inside a provisioned branch.

The job fails closed if it cannot read the settings row, import the Proxbox
branching helpers, or confirm that the branching runtime is available. It raises
`BranchingUnavailableError` before fetching PDM data or writing `PDMRemote` rows;
the refusal is recorded as the job error instead of silently writing to main.
This guarantee applies to every supported `netbox-proxbox` version.

## Compatibility

See [COMPATIBILITY.md](COMPATIBILITY.md) for the full version compatibility table.

## Installation

```bash
pip install netbox-proxbox netbox-pdm
```

In `configuration.py`:

```python
PLUGINS = [
    "netbox_proxbox",
    "netbox_pdm",
]
```

```bash
python manage.py migrate
```

## Documentation

Full documentation is published at
<https://emersonfelipesp.github.io/netbox-pdm/>.

## Support

Use GitHub Issues for bugs and feature requests:
<https://github.com/emersonfelipesp/netbox-pdm/issues>.

## Certification Status

Certification evidence is tracked in [CERTIFICATION.md](./CERTIFICATION.md).
The repository includes Apache-2.0 licensing, PyPI metadata, compatibility
metadata, GitHub Actions CI, release validation, docs publishing, screenshot
capture, and page-coverage workflows for NetBox v4.6.4. Digest-pinned Docker
install smoke covers official NetBox v4.7.0 GA; exact-source integration tests
cover the backward-compatible v4.5.8 through v4.6.6 range.

Canonical NetBox `v4.7.0 GA` metadata is admitted on a **GA**
basis and runs without a compatibility warning; 4.7.1 and later fail
closed. CI pins exact source revision
`5f06007e4c9bacc93ce17c1e645fc1143d60df3d`; the shared numeric compatibility
bounds preserve the historical upgrade path. See [COMPATIBILITY.md](COMPATIBILITY.md)
for the tier table and the Proxbox-family upgrade procedure.

## License

Apache-2.0

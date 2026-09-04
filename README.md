# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** inventory —
remotes, views, and SDN-adjacent state — into NetBox through the
[`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api) backend.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox); it
reuses `netbox-proxbox` FastAPI endpoint resolution and job conventions when
that plugin is installed, and falls back to its own `proxbox_api_url` /
`proxbox_api_key` plugin settings otherwise.
`netbox-proxbox` remains a required NetBox peer plugin in `PLUGINS`, but is not
installed as a Python wheel dependency so the Proxbox stack can resolve one
shared Pydantic line with `proxmox-sdk`.

## Status

`netbox-pdm` v0.0.2 ships PDM endpoint and remote inventory views, sync job
wiring, and the proxmox-sdk-backed PDM client path. The plugin never writes
configuration back to PDM; sync reconciles NetBox inventory rows only.

Security and reconciliation behavior:

- Triggering endpoint sync requires both endpoint visibility and `core.add_job`.
- PDM token secrets are never rendered back into endpoint edit forms; leaving
  the field blank preserves the stored secret.
- Sync creates, updates, and prunes `PDMRemote` rows so remotes removed from
  PDM do not remain as stale NetBox inventory.

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
capture, and page-coverage workflows for NetBox v4.6.4. Docker install smoke
coverage spans NetBox v4.5.8 through v4.6.6.

Official NetBox `v4.7.0` GA is admitted in the stable backward-compatible
`4.5.8`–`4.7.0` range. Pre-release identities warn once at startup and are not
production support. CI pins the exact GA source revision
`5f06007e4c9bacc93ce17c1e645fc1143d60df3d`; runtime enforces the numeric
compatibility band while CI provides canonical source provenance. See [COMPATIBILITY.md](COMPATIBILITY.md) for the tier
table, how to silence the notice, and why every Proxbox-family plugin must be
upgraded together before moving an instance to NetBox 4.7 GA.

## License

Apache-2.0

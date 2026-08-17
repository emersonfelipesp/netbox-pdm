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
coverage spans NetBox v4.5.8, v4.5.9, and v4.6.0 through v4.6.4.

NetBox `4.7.x` is additionally supported on an **experimental** basis: the plugin
loads and runs with no configuration change and warns once at startup that the
line is not yet certified. See [COMPATIBILITY.md](COMPATIBILITY.md) for the tier
table, how to silence the notice, and why every Proxbox-family plugin must be
upgraded together before moving an instance to 4.7.

## License

Apache-2.0

# netbox-pdm

NetBox plugin that reflects **Proxmox Datacenter Manager (PDM)** inventory —
remotes, views, and SDN-adjacent state — into NetBox through the
[`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api) backend.

`netbox-pdm` is a sibling plugin of
[`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox); it
reuses `netbox-proxbox` FastAPI endpoint resolution and job conventions when
that plugin is installed, and falls back to its own `proxbox_api_url` /
`proxbox_api_key` plugin settings otherwise.

## Status

`netbox-pdm` v0.0.1.post1 ships the plugin scaffold and NetBox installation
glue. Model and sync views land in upcoming releases. The plugin is
**read-only**: all mutations remain in PDM. This post release normalizes
certification evidence, packaging metadata, and compatibility documentation
without changing runtime behavior.

## Requirements

- NetBox 4.5.8 through 4.6.x, verified against NetBox v4.5.8 and v4.6.1
- Python 3.12+
- [`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) `>= 0.0.18,<0.1.0`
- A reachable [`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api)
  instance with PDM-aware endpoints enabled

## Installation

```bash
pip install netbox-pdm
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
capture, and page-coverage workflows for NetBox v4.6.1.

## License

Apache-2.0

# Installation

## Requirements

- NetBox 4.5.8, 4.5.9, and 4.6.0 through 4.6.4
- Python 3.12+
- [`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) `>=0.0.18,<0.1.0`
  installed as a NetBox peer plugin
- [`proxmox-sdk`](https://github.com/emersonfelipesp/proxmox-sdk) `>=0.0.12`
  (installed automatically as a dependency of `netbox-pdm`)
- Network access from the NetBox host to the Proxmox Datacenter Manager API
  (typically HTTPS on port 8443)

!!! note "No proxbox-api required"
    `netbox-pdm` sync jobs call the PDM API **directly** via `proxmox-sdk`.
    A running `proxbox-api` instance is **not** required for PDM sync.

## Install

```bash
pip install netbox-proxbox netbox-pdm
```

In `configuration.py`, list both plugins — `netbox_proxbox` must come first:

```python
PLUGINS = [
    "netbox_proxbox",
    "netbox_pdm",
]
```

Run migrations (both plugins add tables):

```bash
python manage.py migrate
```

Restart the NetBox WSGI process and the RQ worker:

```bash
systemctl restart netbox netbox-rq
```

## Upgrade

```bash
pip install --upgrade netbox-proxbox netbox-pdm
python manage.py migrate
systemctl restart netbox netbox-rq
```

## Uninstall

Remove `"netbox_proxbox"` and `"netbox_pdm"` from `PLUGINS`, then:

```bash
python manage.py migrate netbox_pdm zero
python manage.py migrate netbox_proxbox zero   # only if removing proxbox too
pip uninstall netbox-pdm
```

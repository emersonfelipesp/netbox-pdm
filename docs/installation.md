# Installation

## Requirements

- NetBox 4.5.8, 4.5.9, and 4.6.0 through 4.6.3
- Python 3.12+
- [`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) `>=0.0.18,<0.1.0`
  installed as a NetBox peer plugin
- A reachable [`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api)
  instance with PDM-aware endpoints

## Install

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

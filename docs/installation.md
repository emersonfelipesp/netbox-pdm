# Installation

## Requirements

- NetBox 4.5.8 through 4.6.x
- Python 3.12+
- [`netbox-proxbox`](https://github.com/emersonfelipesp/netbox-proxbox) `>=0.0.18,<0.1.0`
- A reachable [`proxbox-api`](https://github.com/emersonfelipesp/proxbox-api)
  instance with PDM-aware endpoints

## Install

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

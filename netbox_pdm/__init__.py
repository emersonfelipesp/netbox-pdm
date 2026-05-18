"""netbox-pdm — NetBox plugin for Proxmox Datacenter Manager (PDM).

Sibling plugin of `netbox-proxbox`. Reuses the same `proxbox-api` backend to
reflect PDM remotes, views, and SDN-adjacent state into NetBox.
"""

from __future__ import annotations

from netbox.plugins import PluginConfig

__version__ = "0.0.1rc2"


class NetBoxPDMConfig(PluginConfig):
    name = "netbox_pdm"
    verbose_name = "NetBox PDM"
    description = (
        "Read-only NetBox inventory of Proxmox Datacenter Manager remotes, "
        "views, and SDN-adjacent state, reflected through proxbox-api."
    )
    version = __version__
    author = "Emerson Felipe"
    author_email = "emersonfelipe.2003@gmail.com"
    base_url = "pdm"
    min_version = "4.5.8"
    max_version = "4.6.99"
    required_plugins = ["netbox_proxbox"]
    required_settings: list[str] = []
    default_settings = {
        # Fallback only — when netbox-proxbox is installed, its singleton
        # FastAPIEndpoint row is reused instead.
        "proxbox_api_url": "",
        "proxbox_api_key": "",
    }


config = NetBoxPDMConfig

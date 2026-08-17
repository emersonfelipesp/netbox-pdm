"""netbox-pdm — NetBox plugin for Proxmox Datacenter Manager (PDM).

Sibling plugin of `netbox-proxbox`. Reuses the same `proxbox-api` backend to
reflect PDM remotes, views, and SDN-adjacent state into NetBox.
"""

from __future__ import annotations

from netbox.plugins import PluginConfig

from .compat import (
    PLUGIN_MAX_VERSION,
    PLUGIN_MIN_VERSION,
    register_netbox_compatibility_check,
)

__version__ = "0.0.2"


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
    # Sourced from .compat so the stable/experimental bands are declared in
    # one place across the Proxbox plugin stack. max_version is the
    # *experimental* ceiling: NetBox 4.7 loads without an opt-in, and
    # .compat's system check warns that the line is not yet certified.
    min_version = PLUGIN_MIN_VERSION
    max_version = PLUGIN_MAX_VERSION
    required_plugins = ["netbox_proxbox"]
    required_settings: list[str] = []
    default_settings = {
        # Fallback only — when netbox-proxbox is installed, its singleton
        # FastAPIEndpoint row is reused instead.
        "proxbox_api_url": "",
        "proxbox_api_key": "",
    }

    def ready(self) -> None:
        super().ready()
        register_netbox_compatibility_check(self)


config = NetBoxPDMConfig

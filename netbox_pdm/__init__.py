"""netbox-pdm — NetBox plugin for Proxmox Datacenter Manager (PDM).

Sibling plugin of `netbox-proxbox`. Reuses the same `proxbox-api` backend to
reflect PDM remotes, views, and SDN-adjacent state into NetBox.
"""

from __future__ import annotations

from netbox.plugins import PluginConfig

from .compat import (
    APPROVED_EXPERIMENTAL_NETBOX_DESIGNATION,
    APPROVED_EXPERIMENTAL_NETBOX_VERSION,
    PLUGIN_MAX_VERSION,
    PLUGIN_MIN_VERSION,
    register_netbox_compatibility_check,
    validate_held_netbox_release_identity,
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
    # Sourced from .compat so the stable and held-beta contracts are declared
    # in one place across the Proxbox plugin stack.
    min_version = PLUGIN_MIN_VERSION
    max_version = PLUGIN_MAX_VERSION
    approved_netbox_version = APPROVED_EXPERIMENTAL_NETBOX_VERSION
    approved_netbox_designation = APPROVED_EXPERIMENTAL_NETBOX_DESIGNATION
    required_plugins = ["netbox_proxbox"]
    required_settings: list[str] = []
    default_settings = {
        # Fallback only — when netbox-proxbox is installed, its singleton
        # FastAPIEndpoint row is reused instead.
        "proxbox_api_url": "",
        "proxbox_api_key": "",
    }

    @classmethod
    def validate(cls, user_config: dict[str, object], netbox_version: str) -> None:
        """Apply stock bounds, then attest the held 4.7 release identity."""
        super().validate(user_config, netbox_version)
        validate_held_netbox_release_identity(cls, netbox_version)

    def ready(self) -> None:
        super().ready()
        register_netbox_compatibility_check(self)


config = NetBoxPDMConfig

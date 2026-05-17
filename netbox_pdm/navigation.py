"""NetBox navigation entries for netbox-pdm."""

from __future__ import annotations

from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label="PDM",
    icon_class="mdi mdi-server-network",
    groups=(
        (
            "Proxmox Datacenter Manager",
            (
                PluginMenuItem(
                    link="plugins:netbox_pdm:home",
                    link_text="Overview",
                ),
            ),
        ),
    ),
)

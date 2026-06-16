"""NetBox navigation entries for netbox-pdm."""

from __future__ import annotations

from netbox.plugins import PluginMenu, PluginMenuButton, PluginMenuItem

menu = PluginMenu(
    label="PDM",
    icon_class="mdi mdi-server-network",
    groups=(
        (
            "Proxmox Datacenter Manager",
            (
                PluginMenuItem(
                    link="plugins:netbox_pdm:pdmendpoint_list",
                    link_text="Endpoints",
                    permissions=["netbox_proxbox.view_pdmendpoint"],
                    buttons=[
                        PluginMenuButton(
                            link="plugins:netbox_pdm:pdmendpoint_add",
                            title="Add",
                            icon_class="mdi mdi-plus-thick",
                            permissions=["netbox_proxbox.add_pdmendpoint"],
                        ),
                    ],
                ),
                PluginMenuItem(
                    link="plugins:netbox_pdm:pdmremote_list",
                    link_text="Remotes",
                    permissions=["netbox_proxbox.view_pdmremote"],
                ),
            ),
        ),
    ),
)

"""Tables for netbox-pdm views."""

from __future__ import annotations

import django_tables2 as tables
from netbox.tables import ChoiceFieldColumn, NetBoxTable
from netbox_proxbox.models import PDMEndpoint, PDMRemote


class PDMEndpointTable(NetBoxTable):
    name = tables.Column(linkify=True)
    domain = tables.Column(verbose_name="Domain")
    ip_address = tables.Column(verbose_name="IP")
    port = tables.Column()
    enabled = tables.BooleanColumn()
    allow_writes = tables.BooleanColumn(verbose_name="Writes")
    verify_ssl = tables.BooleanColumn(verbose_name="SSL")
    remote_count = tables.Column(verbose_name="Remotes", orderable=False)

    class Meta(NetBoxTable.Meta):
        model = PDMEndpoint
        fields = (
            "pk",
            "id",
            "name",
            "ip_address",
            "domain",
            "port",
            "enabled",
            "allow_writes",
            "verify_ssl",
            "remote_count",
            "actions",
        )
        default_columns = (
            "name",
            "ip_address",
            "domain",
            "port",
            "enabled",
            "remote_count",
            "actions",
        )

    def render_remote_count(self, record: PDMEndpoint) -> int:
        return record.remotes.count()


class PDMRemoteTable(NetBoxTable):
    name = tables.Column(linkify=True)
    pdm_endpoint = tables.Column(linkify=True, verbose_name="PDM endpoint")
    type = ChoiceFieldColumn(verbose_name="Type")
    hostname = tables.Column()
    version = tables.Column()
    linked_proxmox_endpoint = tables.Column(linkify=True, verbose_name="PVE endpoint")
    linked_pbs_endpoint = tables.Column(linkify=True, verbose_name="PBS endpoint")

    class Meta(NetBoxTable.Meta):
        model = PDMRemote
        fields = (
            "pk",
            "id",
            "name",
            "pdm_endpoint",
            "type",
            "hostname",
            "fingerprint",
            "version",
            "linked_proxmox_endpoint",
            "linked_pbs_endpoint",
            "last_seen_at",
            "actions",
        )
        default_columns = (
            "name",
            "pdm_endpoint",
            "type",
            "hostname",
            "version",
            "linked_proxmox_endpoint",
            "actions",
        )

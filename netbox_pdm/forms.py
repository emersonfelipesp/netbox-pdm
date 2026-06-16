"""Forms for netbox-pdm views."""

from __future__ import annotations

from django import forms
from netbox.forms import NetBoxModelFilterSetForm, NetBoxModelForm
from utilities.forms.fields import (
    CommentField,
    DynamicModelChoiceField,
    TagFilterField,
)
from utilities.forms.rendering import FieldSet

from netbox_proxbox.models import PDMEndpoint, PDMRemote
from netbox_proxbox.models.pdm_remote import PDMRemoteTypeChoices


class PDMEndpointForm(NetBoxModelForm):
    comments = CommentField()

    class Meta:
        model = PDMEndpoint
        fields = (
            "name",
            "ip_address",
            "domain",
            "port",
            "token_id",
            "token_secret",
            "fingerprint",
            "verify_ssl",
            "allow_writes",
            "enabled",
            "timeout",
            "site",
            "tenant",
            "proxmox_endpoints",
            "pbs_endpoints",
            "comments",
            "tags",
        )
        fieldsets = (
            FieldSet("name", "ip_address", "domain", "port", name="Connection"),
            FieldSet(
                "token_id",
                "token_secret",
                "fingerprint",
                "verify_ssl",
                name="Authentication",
            ),
            FieldSet("enabled", "allow_writes", "timeout", name="Settings"),
            FieldSet("site", "tenant", name="Tenancy"),
            FieldSet("proxmox_endpoints", "pbs_endpoints", name="Federation"),
        )
        widgets = {
            "token_secret": forms.PasswordInput(render_value=True),
        }


class PDMEndpointFilterForm(NetBoxModelFilterSetForm):
    model = PDMEndpoint

    enabled = forms.NullBooleanSelect()
    verify_ssl = forms.NullBooleanSelect()
    tag = TagFilterField(model)

    class Meta:
        fields = ("q", "enabled", "verify_ssl", "port", "tag")


class PDMRemoteFilterForm(NetBoxModelFilterSetForm):
    model = PDMRemote

    type = forms.MultipleChoiceField(
        choices=PDMRemoteTypeChoices.choices,
        required=False,
        label="Type",
    )
    pdm_endpoint_id = DynamicModelChoiceField(
        queryset=PDMEndpoint.objects.all(),
        required=False,
        label="PDM endpoint",
    )
    tag = TagFilterField(model)

    class Meta:
        fields = ("q", "type", "pdm_endpoint_id", "tag")

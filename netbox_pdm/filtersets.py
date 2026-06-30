"""FilterSets for netbox-pdm views."""

from __future__ import annotations

import django_filters
from django.db.models import QuerySet
from netbox.filtersets import NetBoxModelFilterSet
from netbox_proxbox.models import PDMEndpoint, PDMRemote
from netbox_proxbox.models.pdm_remote import PDMRemoteTypeChoices


class PDMEndpointFilterSet(NetBoxModelFilterSet):
    enabled = django_filters.BooleanFilter()

    class Meta:
        model = PDMEndpoint
        fields = ("id", "name", "domain", "port", "enabled", "verify_ssl")

    def search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.filter(name__icontains=value) | queryset.filter(
            domain__icontains=value
        )


class PDMRemoteFilterSet(NetBoxModelFilterSet):
    type = django_filters.MultipleChoiceFilter(choices=PDMRemoteTypeChoices.choices)
    pdm_endpoint_id = django_filters.ModelMultipleChoiceFilter(
        queryset=PDMEndpoint.objects.all(),
        field_name="pdm_endpoint",
        label="PDM endpoint",
    )

    class Meta:
        model = PDMRemote
        fields = ("id", "name", "type", "hostname", "pdm_endpoint_id")

    def search(self, queryset: QuerySet, name: str, value: str) -> QuerySet:
        return queryset.filter(name__icontains=value) | queryset.filter(
            hostname__icontains=value
        )

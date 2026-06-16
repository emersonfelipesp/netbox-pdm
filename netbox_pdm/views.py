"""Views for netbox-pdm — PDMEndpoint and PDMRemote CRUD + sync action."""

from __future__ import annotations

from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.views import View
from netbox.views import generic
from utilities.views import ConditionalLoginRequiredMixin, register_model_view

from netbox_proxbox.models import PDMEndpoint, PDMRemote

from netbox_pdm.filtersets import PDMEndpointFilterSet, PDMRemoteFilterSet
from netbox_pdm.forms import (
    PDMEndpointFilterForm,
    PDMEndpointForm,
    PDMRemoteFilterForm,
)
from netbox_pdm.jobs import PDMSyncJob
from netbox_pdm.tables import PDMEndpointTable, PDMRemoteTable


# ---------------------------------------------------------------------------
# Home view — redirects to the endpoint list
# ---------------------------------------------------------------------------

class PDMHomeView(ConditionalLoginRequiredMixin, View):
    """Plugin home page — redirects to the PDMEndpoint list."""

    def get(self, request, *args, **kwargs):
        return redirect("plugins:netbox_pdm:pdmendpoint_list")


# ---------------------------------------------------------------------------
# PDMEndpoint views
# ---------------------------------------------------------------------------

@register_model_view(PDMEndpoint, "list", path="", detail=False)
class PDMEndpointListView(generic.ObjectListView):
    queryset = PDMEndpoint.objects.all()
    table = PDMEndpointTable
    filterset = PDMEndpointFilterSet
    filterset_form = PDMEndpointFilterForm


@register_model_view(PDMEndpoint)
class PDMEndpointView(generic.ObjectView):
    queryset = PDMEndpoint.objects.prefetch_related("remotes")

    def get_extra_context(self, request, instance):
        remotes_table = PDMRemoteTable(instance.remotes.all())
        remotes_table.configure(request)
        return {"remotes_table": remotes_table}


@register_model_view(PDMEndpoint, "add", path="add", detail=False)
class PDMEndpointAddView(generic.ObjectEditView):
    queryset = PDMEndpoint.objects.all()
    form = PDMEndpointForm
    default_return_url = "plugins:netbox_pdm:pdmendpoint_list"


@register_model_view(PDMEndpoint, "edit")
class PDMEndpointEditView(generic.ObjectEditView):
    queryset = PDMEndpoint.objects.all()
    form = PDMEndpointForm
    default_return_url = "plugins:netbox_pdm:pdmendpoint_list"


@register_model_view(PDMEndpoint, "delete")
class PDMEndpointDeleteView(generic.ObjectDeleteView):
    queryset = PDMEndpoint.objects.all()
    default_return_url = "plugins:netbox_pdm:pdmendpoint_list"


# ---------------------------------------------------------------------------
# PDMEndpoint sync action (POST only, not a registered model view)
# ---------------------------------------------------------------------------

class PDMEndpointSyncView(ConditionalLoginRequiredMixin, View):
    """Trigger a PDMSyncJob for a single PDMEndpoint."""

    def post(self, request, pk):
        endpoint = get_object_or_404(PDMEndpoint, pk=pk)
        if not request.user.has_perm("netbox_proxbox.view_pdmendpoint"):
            return HttpResponseForbidden()
        PDMSyncJob.enqueue(endpoint_pk=endpoint.pk)
        messages.success(
            request,
            f"Sync job queued for PDM endpoint '{endpoint}'.",
        )
        return redirect("plugins:netbox_pdm:pdmendpoint_list")


# ---------------------------------------------------------------------------
# PDMRemote views
# ---------------------------------------------------------------------------

@register_model_view(PDMRemote, "list", path="", detail=False)
class PDMRemoteListView(generic.ObjectListView):
    queryset = PDMRemote.objects.select_related("pdm_endpoint")
    table = PDMRemoteTable
    filterset = PDMRemoteFilterSet
    filterset_form = PDMRemoteFilterForm


@register_model_view(PDMRemote)
class PDMRemoteView(generic.ObjectView):
    queryset = PDMRemote.objects.select_related(
        "pdm_endpoint",
        "linked_proxmox_endpoint",
        "linked_pbs_endpoint",
    )

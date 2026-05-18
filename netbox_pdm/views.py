from __future__ import annotations

from django.shortcuts import render
from django.views.generic import View
from utilities.views import ConditionalLoginRequiredMixin


class PDMHomeView(ConditionalLoginRequiredMixin, View):
    """Placeholder home page for the PDM plugin."""

    def get(self, request, *args, **kwargs):
        return render(request, "netbox_pdm/home.html", {})

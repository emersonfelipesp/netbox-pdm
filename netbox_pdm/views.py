from __future__ import annotations

from django.shortcuts import render
from utilities.views import ConditionalLoginRequiredMixin
from django.views.generic import View


class PDMHomeView(ConditionalLoginRequiredMixin, View):
    """Placeholder home page for the PDM plugin."""

    def get(self, request, *args, **kwargs):
        return render(request, "netbox_pdm/home.html", {})

from __future__ import annotations

from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_pdm import views  # noqa: F401 — registers views via @register_model_view
from netbox_pdm.sitemap import SitemapView

app_name = "netbox_pdm"

urlpatterns = [
    # Plugin home (redirects to endpoint list)
    path("", views.PDMHomeView.as_view(), name="home"),
    path("sitemap.txt", SitemapView.as_view(), name="sitemap"),

    # PDMEndpoint — list/add (detail=False) and detail/edit/delete/changelog (detail=True)
    path(
        "endpoints/",
        include(get_model_urls("netbox_proxbox", "pdmendpoint", detail=False)),
    ),
    path(
        "endpoints/<int:pk>/",
        include(get_model_urls("netbox_proxbox", "pdmendpoint")),
    ),
    path(
        "endpoints/<int:pk>/sync/",
        views.PDMEndpointSyncView.as_view(),
        name="pdmendpoint_sync",
    ),

    # PDMRemote — list (detail=False) and detail (detail=True)
    path(
        "remotes/",
        include(get_model_urls("netbox_proxbox", "pdmremote", detail=False)),
    ),
    path(
        "remotes/<int:pk>/",
        include(get_model_urls("netbox_proxbox", "pdmremote")),
    ),
]

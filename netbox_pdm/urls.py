from __future__ import annotations

from django.urls import path

from netbox_pdm import views
from netbox_pdm.sitemap import SitemapView

app_name = "netbox_pdm"

urlpatterns = [
    path("", views.PDMHomeView.as_view(), name="home"),
    path("sitemap.txt", SitemapView.as_view(), name="sitemap"),
]

from __future__ import annotations

from django.urls import path

from netbox_pdm import views

app_name = "netbox_pdm"

urlpatterns = [
    path("", views.PDMHomeView.as_view(), name="home"),
]

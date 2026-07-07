"""Behavioral tests for sync, client construction, views, and secret forms."""

from __future__ import annotations

import importlib
import logging
import sys
import types
from contextlib import contextmanager
from types import SimpleNamespace

import pytest


def _install_netbox_package_stubs(monkeypatch: pytest.MonkeyPatch) -> None:
    netbox = types.ModuleType("netbox")
    netbox.__path__ = []

    plugins = types.ModuleType("netbox.plugins")

    class PluginConfig:
        def ready(self) -> None:
            return None

    plugins.PluginConfig = PluginConfig
    netbox.plugins = plugins

    monkeypatch.setitem(sys.modules, "netbox", netbox)
    monkeypatch.setitem(sys.modules, "netbox.plugins", plugins)


def _import_jobs_module(monkeypatch: pytest.MonkeyPatch):
    _install_netbox_package_stubs(monkeypatch)

    constants = types.ModuleType("netbox.constants")
    constants.RQ_QUEUE_DEFAULT = "default"

    netbox_jobs = types.ModuleType("netbox.jobs")

    class JobRunner:
        @classmethod
        def enqueue(cls, *args, instance=None, **kwargs):
            return SimpleNamespace(data={}, save=lambda **_kwargs: None)

    netbox_jobs.JobRunner = JobRunner

    branch_lifecycle = types.ModuleType("netbox_pdm.services.branch_lifecycle")

    @contextmanager
    def activate_branch_context(branch):
        yield branch

    branch_lifecycle.activate_branch_context = activate_branch_context
    branch_lifecycle.branching_enabled_settings = lambda: None
    branch_lifecycle.create_and_provision_branch = lambda **_kwargs: None
    branch_lifecycle.merge_branch = lambda **_kwargs: (True, "merged")

    monkeypatch.setitem(sys.modules, "netbox.constants", constants)
    monkeypatch.setitem(sys.modules, "netbox.jobs", netbox_jobs)
    monkeypatch.setitem(
        sys.modules,
        "netbox_pdm.services.branch_lifecycle",
        branch_lifecycle,
    )
    sys.modules.pop("netbox_pdm.jobs", None)
    return importlib.import_module("netbox_pdm.jobs")


class _FakePDMRemoteQuerySet:
    def __init__(self, manager: "_FakePDMRemoteManager", rows: list[object]) -> None:
        self.manager = manager
        self.rows = rows

    def exclude(self, **kwargs):
        names = set(kwargs["name__in"])
        return _FakePDMRemoteQuerySet(
            self.manager,
            [row for row in self.rows if row.name not in names],
        )

    def count(self) -> int:
        return len(self.rows)

    def delete(self):
        for row in list(self.rows):
            self.manager.rows.pop((row.pdm_endpoint, row.name), None)
        return len(self.rows), {"netbox_proxbox.PDMRemote": len(self.rows)}


class _FakePDMRemoteManager:
    def __init__(self) -> None:
        self.rows: dict[tuple[object, str], object] = {}

    def update_or_create(self, *, pdm_endpoint: object, name: str, defaults: dict):
        key = (pdm_endpoint, name)
        created = key not in self.rows
        row = self.rows.get(key) or SimpleNamespace(
            pdm_endpoint=pdm_endpoint,
            name=name,
        )
        for field, value in defaults.items():
            setattr(row, field, value)
        self.rows[key] = row
        return row, created

    def filter(self, *, pdm_endpoint: object):
        return _FakePDMRemoteQuerySet(
            self,
            [
                row
                for (row_endpoint, _name), row in self.rows.items()
                if row_endpoint is pdm_endpoint
            ],
        )


def _install_sync_runtime_stubs(
    monkeypatch: pytest.MonkeyPatch,
    manager: _FakePDMRemoteManager,
) -> None:
    django = types.ModuleType("django")
    django.__path__ = []
    django_utils = types.ModuleType("django.utils")
    timezone = types.ModuleType("django.utils.timezone")
    timezone.now = lambda: "now-marker"

    netbox_proxbox = types.ModuleType("netbox_proxbox")
    netbox_proxbox.__path__ = []
    proxbox_models = types.ModuleType("netbox_proxbox.models")

    class PDMRemote:
        objects = manager

    proxbox_models.PDMRemote = PDMRemote
    netbox_proxbox.models = proxbox_models

    monkeypatch.setitem(sys.modules, "django", django)
    monkeypatch.setitem(sys.modules, "django.utils", django_utils)
    monkeypatch.setitem(sys.modules, "django.utils.timezone", timezone)
    monkeypatch.setitem(sys.modules, "netbox_proxbox", netbox_proxbox)
    monkeypatch.setitem(sys.modules, "netbox_proxbox.models", proxbox_models)


def test_sync_remotes_creates_updates_and_prunes_stale_rows(monkeypatch):
    jobs = _import_jobs_module(monkeypatch)
    manager = _FakePDMRemoteManager()
    _install_sync_runtime_stubs(monkeypatch, manager)

    class Endpoint:
        pk = 1
        name = "pdm-a"

    endpoint = Endpoint()
    manager.update_or_create(
        pdm_endpoint=endpoint,
        name="alpha",
        defaults={
            "type": "pve",
            "hostname": "old-host",
            "fingerprint": "old-fp",
            "version": "",
            "last_seen_at": "before",
        },
    )
    manager.update_or_create(
        pdm_endpoint=endpoint,
        name="stale",
        defaults={
            "type": "pbs",
            "hostname": "gone",
            "fingerprint": "gone-fp",
            "version": "",
            "last_seen_at": "before",
        },
    )

    remotes = [
        SimpleNamespace(
            id="alpha",
            type="pve",
            nodes=[SimpleNamespace(hostname="new-host", fingerprint="new-fp")],
            fingerprint=None,
        ),
        SimpleNamespace(
            id="beta",
            type=None,
            nodes=[],
            fingerprint="remote-fp",
        ),
    ]

    result = jobs._sync_remotes(endpoint, remotes, logging.getLogger(__name__))

    assert result == {"created": 1, "updated": 1, "deleted": 1, "total": 2}
    assert (endpoint, "stale") not in manager.rows
    assert manager.rows[(endpoint, "alpha")].hostname == "new-host"
    assert manager.rows[(endpoint, "alpha")].fingerprint == "new-fp"
    assert manager.rows[(endpoint, "beta")].type == "pve"
    assert manager.rows[(endpoint, "beta")].fingerprint == "remote-fp"
    assert manager.rows[(endpoint, "beta")].last_seen_at == "now-marker"


def test_make_pdm_client_resolves_host_token_and_logs_disabled_tls(
    monkeypatch,
    caplog,
):
    jobs = _import_jobs_module(monkeypatch)

    pdm_client = types.ModuleType("proxmox_sdk.pdm.client")
    auth_token = types.ModuleType("proxmox_sdk.sdk.auth.token")

    class FakeSyncPDMClient:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    pdm_client.SyncPDMClient = FakeSyncPDMClient
    auth_token.parse_token_id = lambda token_id: ("root@pam", "sync-token")

    monkeypatch.setitem(sys.modules, "proxmox_sdk", types.ModuleType("proxmox_sdk"))
    monkeypatch.setitem(sys.modules, "proxmox_sdk.pdm", types.ModuleType("proxmox_sdk.pdm"))
    monkeypatch.setitem(sys.modules, "proxmox_sdk.pdm.client", pdm_client)
    monkeypatch.setitem(sys.modules, "proxmox_sdk.sdk", types.ModuleType("proxmox_sdk.sdk"))
    monkeypatch.setitem(
        sys.modules,
        "proxmox_sdk.sdk.auth",
        types.ModuleType("proxmox_sdk.sdk.auth"),
    )
    monkeypatch.setitem(sys.modules, "proxmox_sdk.sdk.auth.token", auth_token)

    endpoint = SimpleNamespace(
        pk=10,
        domain="pdm.example.net",
        ip_address=None,
        token_id="root@pam!sync-token",
        token_secret="super-secret",
        port=8443,
        verify_ssl=False,
        timeout=None,
    )

    with caplog.at_level(logging.CRITICAL, logger="netbox_pdm.jobs"):
        client = jobs._make_pdm_client(endpoint)

    assert client.kwargs == {
        "host": "pdm.example.net",
        "user": "root@pam",
        "token_name": "sync-token",
        "token_value": "super-secret",
        "port": 8443,
        "verify_ssl": False,
        "timeout": 30,
    }
    assert "super-secret" not in caplog.text
    assert "TLS verification DISABLED" in caplog.text


def test_make_pdm_client_uses_ip_address_and_rejects_missing_host(monkeypatch):
    jobs = _import_jobs_module(monkeypatch)

    pdm_client = types.ModuleType("proxmox_sdk.pdm.client")
    auth_token = types.ModuleType("proxmox_sdk.sdk.auth.token")

    class FakeSyncPDMClient:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

    pdm_client.SyncPDMClient = FakeSyncPDMClient
    auth_token.parse_token_id = lambda token_id: ("api@pdm", "name")

    monkeypatch.setitem(sys.modules, "proxmox_sdk", types.ModuleType("proxmox_sdk"))
    monkeypatch.setitem(sys.modules, "proxmox_sdk.pdm", types.ModuleType("proxmox_sdk.pdm"))
    monkeypatch.setitem(sys.modules, "proxmox_sdk.pdm.client", pdm_client)
    monkeypatch.setitem(sys.modules, "proxmox_sdk.sdk", types.ModuleType("proxmox_sdk.sdk"))
    monkeypatch.setitem(
        sys.modules,
        "proxmox_sdk.sdk.auth",
        types.ModuleType("proxmox_sdk.sdk.auth"),
    )
    monkeypatch.setitem(sys.modules, "proxmox_sdk.sdk.auth.token", auth_token)

    endpoint = SimpleNamespace(
        pk=11,
        domain="",
        ip_address=SimpleNamespace(address=SimpleNamespace(ip="10.0.30.10")),
        token_id="api@pdm!name",
        token_secret="secret",
        port=8443,
        verify_ssl=True,
        timeout=12,
    )
    client = jobs._make_pdm_client(endpoint)

    assert client.kwargs["host"] == "10.0.30.10"
    assert client.kwargs["timeout"] == 12

    missing_host = SimpleNamespace(
        pk=12,
        domain="",
        ip_address=None,
        token_id="api@pdm!name",
        token_secret="secret",
        port=8443,
        verify_ssl=True,
        timeout=12,
    )
    with pytest.raises(ValueError, match="has no host or IP address"):
        jobs._make_pdm_client(missing_host)


def _import_forms_module(monkeypatch: pytest.MonkeyPatch):
    _install_netbox_package_stubs(monkeypatch)

    django = types.ModuleType("django")
    django.__path__ = []
    django_forms = types.ModuleType("django.forms")

    class PasswordInput:
        def __init__(self, *, render_value=False, **kwargs) -> None:
            self.render_value = render_value
            self.kwargs = kwargs

    class CharField:
        def __init__(
            self,
            *,
            label=None,
            required=True,
            widget=None,
            help_text="",
            **kwargs,
        ) -> None:
            self.label = label
            self.required = required
            self.widget = widget
            self.help_text = help_text
            self.kwargs = kwargs

    class NullBooleanSelect:
        pass

    class MultipleChoiceField:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    django_forms.CharField = CharField
    django_forms.PasswordInput = PasswordInput
    django_forms.NullBooleanSelect = NullBooleanSelect
    django_forms.MultipleChoiceField = MultipleChoiceField
    django.forms = django_forms

    netbox_forms = types.ModuleType("netbox.forms")

    class NetBoxModelForm:
        def __init__(self, *args, **kwargs) -> None:
            self.instance = kwargs.get("instance") or SimpleNamespace(pk=None)
            self.cleaned_data = {}
            token_secret = getattr(type(self), "token_secret", None)
            self.fields = {
                "token_secret": SimpleNamespace(
                    required=getattr(token_secret, "required", True),
                    help_text=getattr(token_secret, "help_text", ""),
                    widget=getattr(token_secret, "widget", None),
                ),
            }

        def save(self, *, commit=True):
            if commit:
                self.instance.save()
            return self.instance

        def save_m2m(self):
            self.saved_m2m = True

    class NetBoxModelFilterSetForm:
        pass

    netbox_forms.NetBoxModelForm = NetBoxModelForm
    netbox_forms.NetBoxModelFilterSetForm = NetBoxModelFilterSetForm

    utilities = types.ModuleType("utilities")
    utilities.__path__ = []
    utilities_forms = types.ModuleType("utilities.forms")
    utilities_forms.__path__ = []
    utilities_fields = types.ModuleType("utilities.forms.fields")
    utilities_rendering = types.ModuleType("utilities.forms.rendering")

    class DummyField:
        def __init__(self, *args, **kwargs) -> None:
            self.args = args
            self.kwargs = kwargs

    utilities_fields.CommentField = DummyField
    utilities_fields.DynamicModelChoiceField = DummyField
    utilities_fields.TagFilterField = DummyField
    utilities_rendering.FieldSet = lambda *args, **kwargs: (args, kwargs)

    class DummyManager:
        def all(self):
            return []

    class DummyModel:
        objects = DummyManager()

    netbox_proxbox = types.ModuleType("netbox_proxbox")
    netbox_proxbox.__path__ = []
    proxbox_models = types.ModuleType("netbox_proxbox.models")
    proxbox_models.PBSEndpoint = DummyModel
    proxbox_models.PDMEndpoint = DummyModel
    proxbox_models.PDMRemote = DummyModel
    proxbox_models.ProxmoxEndpoint = DummyModel

    pdm_remote = types.ModuleType("netbox_proxbox.models.pdm_remote")

    class PDMRemoteTypeChoices:
        choices = (("pve", "PVE"), ("pbs", "PBS"))

    pdm_remote.PDMRemoteTypeChoices = PDMRemoteTypeChoices

    monkeypatch.setitem(sys.modules, "django", django)
    monkeypatch.setitem(sys.modules, "django.forms", django_forms)
    monkeypatch.setitem(sys.modules, "netbox.forms", netbox_forms)
    monkeypatch.setitem(sys.modules, "utilities", utilities)
    monkeypatch.setitem(sys.modules, "utilities.forms", utilities_forms)
    monkeypatch.setitem(sys.modules, "utilities.forms.fields", utilities_fields)
    monkeypatch.setitem(sys.modules, "utilities.forms.rendering", utilities_rendering)
    monkeypatch.setitem(sys.modules, "netbox_proxbox", netbox_proxbox)
    monkeypatch.setitem(sys.modules, "netbox_proxbox.models", proxbox_models)
    monkeypatch.setitem(sys.modules, "netbox_proxbox.models.pdm_remote", pdm_remote)

    sys.modules.pop("netbox_pdm.forms", None)
    return importlib.import_module("netbox_pdm.forms")


def test_pdm_endpoint_form_never_renders_existing_token_and_preserves_blank(
    monkeypatch,
):
    forms = _import_forms_module(monkeypatch)

    widget = forms.PDMEndpointForm.Meta.widgets["token_secret"]
    assert widget.render_value is False
    assert forms.PDMEndpointForm.token_secret.required is True
    assert forms.PDMEndpointForm.token_secret.widget.render_value is False

    instance = SimpleNamespace(pk=123, token_secret="stored-fernet-value")
    form = forms.PDMEndpointForm(instance=instance)
    assert form.fields["token_secret"].required is False

    form.cleaned_data = {"token_secret": ""}
    assert form.clean_token_secret() == "stored-fernet-value"

    form.cleaned_data = {"token_secret": "new-secret"}
    assert form.clean_token_secret() == "new-secret"

    add_form = forms.PDMEndpointForm(instance=SimpleNamespace(pk=None))
    assert add_form.fields["token_secret"].required is True


def test_pdm_endpoint_form_saves_token_secret_through_model_property(monkeypatch):
    forms = _import_forms_module(monkeypatch)

    class EndpointInstance:
        pk = 123
        token_secret = "stored-secret"
        saved = False

        def save(self):
            self.saved = True

    instance = EndpointInstance()
    form = forms.PDMEndpointForm(instance=instance)
    form.cleaned_data = {"token_secret": "replacement-secret"}

    saved = form.save()

    assert saved is instance
    assert instance.token_secret == "replacement-secret"
    assert instance.saved is True
    assert form.saved_m2m is True


class _FakeUser:
    def __init__(self, permissions: set[str]) -> None:
        self.permissions = permissions

    def has_perm(self, permission: str) -> bool:
        return permission in self.permissions


class _FakeRestrictedEndpointQuerySet:
    def __init__(self, endpoint: object | None) -> None:
        self.endpoint = endpoint

    def get(self, *, pk: int):
        if self.endpoint is None or self.endpoint.pk != pk:
            raise LookupError(pk)
        return self.endpoint


class _FakeEndpointManager:
    def __init__(self, endpoint: object) -> None:
        self.endpoint = endpoint
        self.restrict_calls: list[tuple[object, str]] = []

    def all(self):
        return self

    def prefetch_related(self, *args):
        return self

    def restrict(self, user: _FakeUser, action: str):
        self.restrict_calls.append((user, action))
        if user.has_perm("netbox_proxbox.view_pdmendpoint"):
            return _FakeRestrictedEndpointQuerySet(self.endpoint)
        return _FakeRestrictedEndpointQuerySet(None)


class _FakeRemoteManager:
    def all(self):
        return self

    def select_related(self, *args):
        return self


def _import_views_module(monkeypatch: pytest.MonkeyPatch, endpoint: object):
    _install_netbox_package_stubs(monkeypatch)

    django = types.ModuleType("django")
    django.__path__ = []
    django_contrib = types.ModuleType("django.contrib")
    messages = types.ModuleType("django.contrib.messages")
    messages.sent = []
    messages.success = lambda request, message: messages.sent.append((request, message))

    django_http = types.ModuleType("django.http")

    class HttpResponseForbidden:
        status_code = 403

    django_http.HttpResponseForbidden = HttpResponseForbidden

    django_shortcuts = types.ModuleType("django.shortcuts")

    def get_object_or_404(queryset, *, pk):
        try:
            return queryset.get(pk=pk)
        except LookupError as exc:
            raise RuntimeError("not found") from exc

    django_shortcuts.get_object_or_404 = get_object_or_404
    django_shortcuts.redirect = lambda name: SimpleNamespace(status_code=302, url=name)

    django_views = types.ModuleType("django.views")

    class View:
        pass

    django_views.View = View
    django.contrib = django_contrib
    django_contrib.messages = messages

    netbox_views = types.ModuleType("netbox.views")
    generic = types.ModuleType("netbox.views.generic")
    for class_name in (
        "ObjectListView",
        "ObjectView",
        "ObjectEditView",
        "ObjectDeleteView",
    ):
        setattr(generic, class_name, type(class_name, (), {}))
    netbox_views.generic = generic

    utilities = types.ModuleType("utilities")
    utilities.__path__ = []
    utilities_views = types.ModuleType("utilities.views")

    class ConditionalLoginRequiredMixin:
        pass

    utilities_views.ConditionalLoginRequiredMixin = ConditionalLoginRequiredMixin
    utilities_views.register_model_view = lambda *args, **kwargs: lambda cls: cls

    endpoint_manager = _FakeEndpointManager(endpoint)

    class PDMEndpoint:
        objects = endpoint_manager

    class PDMRemote:
        objects = _FakeRemoteManager()

    netbox_proxbox = types.ModuleType("netbox_proxbox")
    netbox_proxbox.__path__ = []
    proxbox_models = types.ModuleType("netbox_proxbox.models")
    proxbox_models.PDMEndpoint = PDMEndpoint
    proxbox_models.PDMRemote = PDMRemote

    filtersets = types.ModuleType("netbox_pdm.filtersets")
    filtersets.PDMEndpointFilterSet = object
    filtersets.PDMRemoteFilterSet = object

    forms = types.ModuleType("netbox_pdm.forms")
    forms.PDMEndpointFilterForm = object
    forms.PDMEndpointForm = object
    forms.PDMRemoteFilterForm = object
    forms.PDMRemoteForm = object

    tables = types.ModuleType("netbox_pdm.tables")
    tables.PDMEndpointTable = object
    tables.PDMRemoteTable = object

    pdm_jobs = types.ModuleType("netbox_pdm.jobs")

    class PDMSyncJob:
        enqueued: list[dict] = []

        @classmethod
        def enqueue(cls, **kwargs) -> None:
            cls.enqueued.append(kwargs)

    pdm_jobs.PDMSyncJob = PDMSyncJob

    monkeypatch.setitem(sys.modules, "django", django)
    monkeypatch.setitem(sys.modules, "django.contrib", django_contrib)
    monkeypatch.setitem(sys.modules, "django.contrib.messages", messages)
    monkeypatch.setitem(sys.modules, "django.http", django_http)
    monkeypatch.setitem(sys.modules, "django.shortcuts", django_shortcuts)
    monkeypatch.setitem(sys.modules, "django.views", django_views)
    monkeypatch.setitem(sys.modules, "netbox.views", netbox_views)
    monkeypatch.setitem(sys.modules, "netbox.views.generic", generic)
    monkeypatch.setitem(sys.modules, "utilities", utilities)
    monkeypatch.setitem(sys.modules, "utilities.views", utilities_views)
    monkeypatch.setitem(sys.modules, "netbox_proxbox", netbox_proxbox)
    monkeypatch.setitem(sys.modules, "netbox_proxbox.models", proxbox_models)
    monkeypatch.setitem(sys.modules, "netbox_pdm.filtersets", filtersets)
    monkeypatch.setitem(sys.modules, "netbox_pdm.forms", forms)
    monkeypatch.setitem(sys.modules, "netbox_pdm.tables", tables)
    monkeypatch.setitem(sys.modules, "netbox_pdm.jobs", pdm_jobs)

    sys.modules.pop("netbox_pdm.views", None)
    return importlib.import_module("netbox_pdm.views")


def test_sync_view_requires_add_job_permission_after_view_restriction(monkeypatch):
    endpoint = SimpleNamespace(pk=77)
    views = _import_views_module(monkeypatch, endpoint)

    request = SimpleNamespace(
        user=_FakeUser({"netbox_proxbox.view_pdmendpoint"}),
    )
    response = views.PDMEndpointSyncView().post(request, pk=endpoint.pk)

    assert response.status_code == 403
    assert views.PDMSyncJob.enqueued == []
    assert views.PDMEndpoint.objects.restrict_calls == [(request.user, "view")]

    allowed_request = SimpleNamespace(
        user=_FakeUser({"netbox_proxbox.view_pdmendpoint", "core.add_job"}),
    )
    allowed_response = views.PDMEndpointSyncView().post(allowed_request, pk=endpoint.pk)

    assert allowed_response.status_code == 302
    assert allowed_response.url == "plugins:netbox_pdm:pdmendpoint_list"
    assert views.PDMSyncJob.enqueued == [{"endpoint_pk": endpoint.pk}]

"""Real-NetBox guard for PDM's declared compatibility contract."""

from __future__ import annotations

import os

os.environ.setdefault("NETBOX_CONFIGURATION", "tests.netbox_test_configuration")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "netbox.settings")

import django  # noqa: E402

django.setup()


def test_plugin_is_installed_and_current_release_is_admitted() -> None:
    from django.apps import apps
    from django.conf import settings
    from packaging.version import parse

    from netbox_pdm import config

    assert apps.is_installed("netbox_pdm")
    current = parse(settings.RELEASE.version)
    assert parse(config.min_version) <= current <= parse(config.max_version)


def test_stable_release_emits_no_compatibility_notice() -> None:
    from django.core.checks import run_checks

    messages = [message for message in run_checks() if message.id.startswith("netbox_pdm.W")]
    assert messages == []

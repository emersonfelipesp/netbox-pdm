"""Smoke tests that do not require a NetBox environment."""

from __future__ import annotations

import importlib

import pytest


def test_package_importable() -> None:
    pytest.importorskip("netbox")
    module = importlib.import_module("netbox_pdm")
    assert module is not None
    assert module.__version__


def test_plugin_config_exposes_required_attrs() -> None:
    pytest.importorskip("netbox")
    from netbox_pdm import config

    cfg = config
    for attr in ("name", "version", "min_version", "max_version", "base_url"):
        assert hasattr(cfg, attr), attr

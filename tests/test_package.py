"""Smoke tests that do not require a NetBox environment."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_package_importable() -> None:
    pytest.importorskip("netbox")
    module = importlib.import_module("netbox_pdm")
    assert module is not None
    assert module.__version__ == "0.0.1.post1"


def test_plugin_config_exposes_required_attrs() -> None:
    pytest.importorskip("netbox")
    from netbox_pdm import config

    cfg = config
    for attr in ("name", "version", "min_version", "max_version", "base_url"):
        assert hasattr(cfg, attr), attr
    assert cfg.version == "0.0.1.post1"
    assert cfg.min_version == "4.5.8"
    assert cfg.max_version == "4.6.99"
    assert cfg.required_plugins == ["netbox_proxbox"]
    assert cfg.author_email == "emersonfelipe.2003@gmail.com"


def test_pyproject_certification_metadata() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["version"] == "0.0.1.post1"
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: Apache Software License" not in project["classifiers"]
    assert "netbox-proxbox>=0.0.18,<0.1.0" in project["dependencies"]
    assert project["urls"]["Documentation"] == "https://emersonfelipesp.github.io/netbox-pdm/"
    assert (ROOT / "LICENSE").is_file()

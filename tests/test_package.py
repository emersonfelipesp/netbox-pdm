"""Smoke tests that do not require a NetBox environment."""

from __future__ import annotations

import importlib
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SUPPORTED_NETBOX_IMAGES = (
    "netboxcommunity/netbox:v4.5.8",
    "netboxcommunity/netbox:v4.5.9",
    "netboxcommunity/netbox:v4.6.0",
    "netboxcommunity/netbox:v4.6.1",
    "netboxcommunity/netbox:v4.6.2",
    "netboxcommunity/netbox:v4.6.3",
    "netboxcommunity/netbox:v4.6.4",
)


def test_package_importable() -> None:
    pytest.importorskip("netbox")
    module = importlib.import_module("netbox_pdm")
    assert module is not None
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert module.__version__ == data["project"]["version"]


def test_plugin_config_exposes_required_attrs() -> None:
    pytest.importorskip("netbox")
    from netbox_pdm import config

    cfg = config
    for attr in ("name", "version", "min_version", "max_version", "base_url"):
        assert hasattr(cfg, attr), attr
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert cfg.version == data["project"]["version"]
    assert cfg.min_version == "4.5.8"
    assert cfg.max_version == "4.7.99"
    assert cfg.required_plugins == ["netbox_proxbox"]
    assert cfg.author_email == "emersonfelipe.2003@gmail.com"


def test_pyproject_certification_metadata() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    project = data["project"]

    assert project["version"] == "0.0.2"
    assert project["license"] == "Apache-2.0"
    assert project["license-files"] == ["LICENSE"]
    assert "License :: OSI Approved :: Apache Software License" not in project["classifiers"]
    assert "proxmox-sdk>=0.0.12" in project["dependencies"]
    assert not any(
        dependency.startswith("netbox-proxbox")
        for dependency in project["dependencies"]
    )
    assert project["urls"]["Documentation"] == "https://emersonfelipesp.github.io/netbox-pdm/"
    assert (ROOT / "LICENSE").is_file()


def test_e2e_workflow_covers_supported_netbox_versions() -> None:
    workflow = (ROOT / ".github" / "workflows" / "e2e.yml").read_text(encoding="utf-8")

    for image in SUPPORTED_NETBOX_IMAGES:
        assert image in workflow


def test_docs_name_supported_netbox_versions() -> None:
    docs = "\n".join(
        [
            (ROOT / "CERTIFICATION.md").read_text(encoding="utf-8"),
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "certification.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "index.md").read_text(encoding="utf-8"),
            (ROOT / "docs" / "release-notes" / "version-0.0.1.post1.md").read_text(
                encoding="utf-8"
            ),
        ]
    )

    for image in SUPPORTED_NETBOX_IMAGES:
        assert image.rsplit(":", 1)[1] in docs


def test_pdm_sync_job_persists_result_data() -> None:
    jobs = (ROOT / "netbox_pdm" / "jobs.py").read_text(encoding="utf-8")

    result_assignment = jobs.index('data["result"] = result')
    result_save = jobs.index('self.job.save(update_fields=["data"])', result_assignment)

    assert result_save > result_assignment


def test_pdm_sync_job_uses_branch_lifecycle_for_orm_reconciliation() -> None:
    jobs = (ROOT / "netbox_pdm" / "jobs.py").read_text(encoding="utf-8")
    lifecycle = (
        ROOT / "netbox_pdm" / "services" / "branch_lifecycle.py"
    ).read_text(encoding="utf-8")

    for snippet in (
        "branching_enabled_settings()",
        "create_and_provision_branch(",
        "with activate_branch_context(branch):",
        "merge_branch(",
        "Leaving branch %s open because PDM sync failed.",
    ):
        assert snippet in jobs

    assert '"activate_branch_context"' in lifecycle
    assert "from netbox_branching.utilities import activate_branch" in lifecycle


def test_plugin_config_bounds_come_from_the_shared_compat_module() -> None:
    """The declared bounds must be sourced from compat.py, not re-typed literals.

    Two copies of the supported range would drift silently. The stable ceiling
    (4.6.99) and the declared ceiling (4.7.99) are deliberately different: 4.7 is
    admitted on an experimental basis, so ``max_version`` is the experimental one.
    """
    pytest.importorskip("netbox")
    from netbox_pdm import config
    from netbox_pdm.compat import (
        EXPERIMENTAL_MAX_NETBOX_VERSION,
        PLUGIN_MAX_VERSION,
        PLUGIN_MIN_VERSION,
        STABLE_MAX_NETBOX_VERSION,
        STABLE_MIN_NETBOX_VERSION,
    )

    assert config.min_version == PLUGIN_MIN_VERSION == STABLE_MIN_NETBOX_VERSION
    assert config.max_version == PLUGIN_MAX_VERSION == EXPERIMENTAL_MAX_NETBOX_VERSION
    assert STABLE_MAX_NETBOX_VERSION == "4.6.99"
    assert EXPERIMENTAL_MAX_NETBOX_VERSION == "4.7.99"

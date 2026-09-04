"""Branch-isolation safety checks for the PDM compatibility path."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest


def _load_branch_lifecycle(monkeypatch: pytest.MonkeyPatch) -> Any:
    models = types.ModuleType("netbox_pdm.models")

    class PdmPluginSettings:
        @classmethod
        def get_solo(cls) -> object:
            return SimpleNamespace(branching_enabled=True)

    models.PdmPluginSettings = PdmPluginSettings
    monkeypatch.setitem(sys.modules, "netbox_pdm.models", models)
    path = Path(__file__).parents[1] / "netbox_pdm" / "services" / "branch_lifecycle.py"
    spec = importlib.util.spec_from_file_location("pdm_branch_lifecycle_under_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_enabled_isolation_fails_closed_when_branching_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module = _load_branch_lifecycle(monkeypatch)
    monkeypatch.setattr(module, "is_branching_available", lambda: False)

    with pytest.raises(RuntimeError, match="refusing to sync against the main schema"):
        module.branching_enabled_settings()

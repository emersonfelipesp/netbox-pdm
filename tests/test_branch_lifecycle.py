"""Behavioral tests for the fail-closed PDM branching decision wrapper."""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
LIFECYCLE_PATH = ROOT / "netbox_pdm" / "services" / "branch_lifecycle.py"


def _typed_lifecycle(
    *,
    state: str,
    available: bool,
    reason: str | None = None,
) -> types.ModuleType:
    lifecycle = types.ModuleType("netbox_proxbox.services.branch_lifecycle")

    class SharedBranchingUnavailableError(RuntimeError):
        pass

    setattr(lifecycle, "BranchingUnavailableError", SharedBranchingUnavailableError)
    setattr(lifecycle, "is_branching_available", lambda: available)
    setattr(
        lifecycle,
        "resolve_branching_decision",
        lambda: SimpleNamespace(
            state=SimpleNamespace(value=state),
            reason=reason,
        ),
    )
    return lifecycle


def _load_lifecycle(
    monkeypatch: pytest.MonkeyPatch,
    *,
    settings: object,
    proxbox_lifecycle: types.ModuleType | None,
):
    pdm_package = types.ModuleType("netbox_pdm")
    pdm_package.__path__ = [str(ROOT / "netbox_pdm")]
    pdm_services = types.ModuleType("netbox_pdm.services")
    pdm_services.__path__ = [str(ROOT / "netbox_pdm" / "services")]
    pdm_models = types.ModuleType("netbox_pdm.models")

    class PdmPluginSettings:
        @classmethod
        def get_solo(cls):
            if isinstance(settings, Exception):
                raise settings
            return settings

    setattr(pdm_models, "PdmPluginSettings", PdmPluginSettings)

    proxbox_package = types.ModuleType("netbox_proxbox")
    proxbox_package.__path__ = []
    proxbox_services = types.ModuleType("netbox_proxbox.services")
    proxbox_services.__path__ = []
    if proxbox_lifecycle is not None:
        setattr(proxbox_services, "branch_lifecycle", proxbox_lifecycle)

    monkeypatch.setitem(sys.modules, "netbox_pdm", pdm_package)
    monkeypatch.setitem(sys.modules, "netbox_pdm.services", pdm_services)
    monkeypatch.setitem(sys.modules, "netbox_pdm.models", pdm_models)
    monkeypatch.setitem(sys.modules, "netbox_proxbox", proxbox_package)
    monkeypatch.setitem(sys.modules, "netbox_proxbox.services", proxbox_services)
    if proxbox_lifecycle is not None:
        monkeypatch.setitem(
            sys.modules,
            "netbox_proxbox.services.branch_lifecycle",
            proxbox_lifecycle,
        )

    spec = importlib.util.spec_from_file_location(
        "netbox_pdm.services.branch_lifecycle",
        LIFECYCLE_PATH,
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_branching_disabled_returns_none_without_consulting_runtime(monkeypatch):
    lifecycle = _typed_lifecycle(
        state="configured_but_unavailable",
        available=False,
        reason="runtime absent",
    )
    setattr(
        lifecycle,
        "resolve_branching_decision",
        lambda: pytest.fail("disabled PDM branching consulted the runtime"),
    )
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(branching_enabled=False),
        proxbox_lifecycle=lifecycle,
    )

    assert module.branching_enabled_settings() is None


def test_branching_enabled_and_available_returns_pdm_settings(monkeypatch):
    lifecycle = _typed_lifecycle(state="enabled", available=True)
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(
            branching_enabled=True,
            branch_name_prefix="pdm-custom",
            branch_on_conflict="acknowledge",
        ),
        proxbox_lifecycle=lifecycle,
    )

    assert module.BranchingUnavailableError is lifecycle.BranchingUnavailableError
    assert module.branching_enabled_settings() == {
        "prefix": "pdm-custom",
        "on_conflict": "acknowledge",
    }


def test_branching_enabled_but_typed_runtime_unavailable_fails_closed(monkeypatch):
    lifecycle = _typed_lifecycle(
        state="configured_but_unavailable",
        available=False,
        reason="the Django app is not loaded",
    )
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(branching_enabled=True),
        proxbox_lifecycle=lifecycle,
    )

    with pytest.raises(
        module.BranchingUnavailableError,
        match="PDM sync refused.*Django app is not loaded",
    ):
        module.branching_enabled_settings()


def test_unreadable_settings_row_fails_closed(monkeypatch):
    lifecycle = _typed_lifecycle(state="enabled", available=True)
    module = _load_lifecycle(
        monkeypatch,
        settings=RuntimeError("database unavailable"),
        proxbox_lifecycle=lifecycle,
    )

    with pytest.raises(
        module.BranchingUnavailableError,
        match="branching_enabled could not be read.*database unavailable",
    ):
        module.branching_enabled_settings()


@pytest.mark.parametrize("available", [True, False])
def test_old_proxbox_falls_back_to_runtime_probe(monkeypatch, available):
    lifecycle = types.ModuleType("netbox_proxbox.services.branch_lifecycle")
    setattr(lifecycle, "is_branching_available", lambda: available)
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(
            branching_enabled=True,
            branch_name_prefix="",
            branch_on_conflict="",
        ),
        proxbox_lifecycle=lifecycle,
    )

    if not available:
        with pytest.raises(
            module.BranchingUnavailableError,
            match="no usable netbox-branching runtime",
        ):
            module.branching_enabled_settings()
        return
    assert module.branching_enabled_settings() == {
        "prefix": "pdm-sync",
        "on_conflict": "fail",
    }


def test_missing_proxbox_helpers_fail_closed_when_enabled(monkeypatch):
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(branching_enabled=True),
        proxbox_lifecycle=None,
    )

    with pytest.raises(
        module.BranchingUnavailableError,
        match="Branch lifecycle support requires netbox-proxbox",
    ):
        module.branching_enabled_settings()


@pytest.mark.parametrize(
    ("upstream_result", "expected"),
    [
        pytest.param(
            (True, "Branch pdm-1 merged.", None),
            (True, "Branch pdm-1 merged.", None),
            id="0.0.27-merged",
        ),
        pytest.param(
            (False, "Branch pdm-1 has unresolved conflicts.", None),
            (False, "Branch pdm-1 has unresolved conflicts.", None),
            id="0.0.27-conflict",
        ),
        pytest.param(
            (True, "Branch pdm-1 had no changes; branch left open.", "no_changes_left_open"),
            (True, "Branch pdm-1 had no changes; branch left open.", "no_changes_left_open"),
            id="0.0.27-no-change",
        ),
        pytest.param(
            (True, "Branch pdm-1 merged."),
            (True, "Branch pdm-1 merged.", None),
            id="legacy-two-item",
        ),
    ],
)
def test_merge_branch_normalizes_supported_proxbox_return_shapes(
    monkeypatch,
    upstream_result,
    expected,
):
    lifecycle = _typed_lifecycle(state="enabled", available=True)
    setattr(lifecycle, "merge_branch", lambda **_kwargs: upstream_result)
    module = _load_lifecycle(
        monkeypatch,
        settings=SimpleNamespace(branching_enabled=True),
        proxbox_lifecycle=lifecycle,
    )

    result = module.merge_branch(
        branch=SimpleNamespace(name="pdm-1"),
        user=None,
        on_conflict="fail",
    )

    assert isinstance(result, module.BranchMergeResult)
    assert (result.merged, result.message, result.disposition) == expected

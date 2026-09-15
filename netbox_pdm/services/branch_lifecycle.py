"""Optional netbox-branching lifecycle wrappers for PDM sync jobs."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any

from netbox_pdm.models import PdmPluginSettings

logger = logging.getLogger("netbox_pdm.branch_lifecycle")

_BRANCHING_UNAVAILABLE = (
    "Branch lifecycle support requires netbox-proxbox with its "
    "netbox_proxbox.services.branch_lifecycle helpers installed."
)


class _FallbackBranchingUnavailableError(RuntimeError):
    """Fallback used with netbox-proxbox releases before the typed contract."""


@dataclass(frozen=True)
class BranchMergeResult:
    """Version-neutral result returned by the PDM branch merge wrapper."""

    merged: bool
    message: str
    disposition: str | None


__all__ = (
    "BranchMergeResult",
    "BranchingUnavailableError",
    "activate_branch_context",
    "branch_has_conflicts",
    "branching_enabled_settings",
    "create_and_provision_branch",
    "get_active_branch_schema_id",
    "is_branching_available",
    "merge_branch",
)


def _proxbox_branch_lifecycle() -> Any | None:
    try:
        from netbox_proxbox.services import branch_lifecycle  # noqa: PLC0415
    except Exception:
        logger.exception("Could not import netbox-proxbox branch lifecycle helpers")
        return None
    return branch_lifecycle


def _branching_error_type() -> type[RuntimeError]:
    """Use the shared typed error when present and a local legacy fallback."""
    lifecycle = _proxbox_branch_lifecycle()
    candidate = getattr(lifecycle, "BranchingUnavailableError", None)
    if isinstance(candidate, type) and issubclass(candidate, RuntimeError):
        return candidate
    return _FallbackBranchingUnavailableError


BranchingUnavailableError = _branching_error_type()


def _exception_detail(prefix: str, exc: Exception) -> str:
    detail = str(exc).strip()
    suffix = f": {detail}" if detail else ""
    return f"{prefix} ({type(exc).__name__}{suffix})"


def _availability_failure(lifecycle: Any) -> str | None:
    try:
        available = bool(lifecycle.is_branching_available())
    except Exception as exc:
        return _exception_detail("the branching runtime probe failed", exc)
    if available:
        return None
    return "no usable netbox-branching runtime was detected"


def _decision_state_value(decision: Any) -> object:
    state = getattr(decision, "state", None)
    return getattr(state, "value", state)


def _runtime_failure(lifecycle: Any) -> str | None:
    resolver = getattr(lifecycle, "resolve_branching_decision", None)
    if not callable(resolver):
        return _availability_failure(lifecycle)
    try:
        decision = resolver()
    except Exception as exc:
        return _exception_detail("the branching decision could not be resolved", exc)
    state = _decision_state_value(decision)
    if state == "configured_but_unavailable":
        return getattr(decision, "reason", None) or "the branching runtime is unavailable"
    if state == "enabled":
        return None
    if state == "disabled":
        return _availability_failure(lifecycle)
    return f"the branching decision returned an unknown state ({state!r})"


def _runtime_failure_message(detail: str) -> str:
    return (
        "PDM sync refused: branch isolation is configured with "
        "branching_enabled=True, but netbox-branching is unavailable "
        f"({detail}). Install and enable a netbox-branching release compatible "
        "with this NetBox version, or set branching_enabled=False to explicitly "
        "allow sync on main."
    )


def is_branching_available() -> bool:
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        return False
    try:
        return bool(lifecycle.is_branching_available())
    except Exception:
        logger.exception("Could not determine netbox-branching availability")
        return False


def get_active_branch_schema_id() -> str | None:
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        return None
    return lifecycle.get_active_branch_schema_id()


def create_and_provision_branch(
    *,
    name: str,
    user: Any | None,
    ready_timeout_seconds: int = 60,
) -> Any:
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        raise NotImplementedError(_BRANCHING_UNAVAILABLE)
    return lifecycle.create_and_provision_branch(
        name=name,
        user=user,
        ready_timeout_seconds=ready_timeout_seconds,
    )


def branch_has_conflicts(branch: Any) -> bool:
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        raise NotImplementedError(_BRANCHING_UNAVAILABLE)
    return bool(lifecycle.branch_has_conflicts(branch))


@contextmanager
def activate_branch_context(branch: Any):
    """Activate a netbox-branching Branch for ORM writes inside the block."""
    if not is_branching_available():
        raise NotImplementedError(_BRANCHING_UNAVAILABLE)
    from netbox_branching.utilities import activate_branch  # noqa: PLC0415

    with activate_branch(branch):
        yield


def merge_branch(
    *,
    branch: Any,
    user: Any | None,
    on_conflict: str,
) -> BranchMergeResult:
    """Normalize legacy two-item and current three-item Proxbox results."""
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        raise NotImplementedError(_BRANCHING_UNAVAILABLE)
    raw_result = lifecycle.merge_branch(
        branch=branch,
        user=user,
        on_conflict=on_conflict,
    )
    if not isinstance(raw_result, tuple) or len(raw_result) not in (2, 3):
        raise TypeError("netbox-proxbox merge_branch() must return a two-item or three-item tuple")
    merged, message = raw_result[:2]
    disposition = raw_result[2] if len(raw_result) == 3 else None
    if (
        not isinstance(merged, bool)
        or not isinstance(message, str)
        or (disposition is not None and not isinstance(disposition, str))
    ):
        raise TypeError("netbox-proxbox merge_branch() returned invalid field types")
    return BranchMergeResult(
        merged=merged,
        message=message,
        disposition=disposition,
    )


def branching_enabled_settings() -> dict[str, str] | None:
    """Return enabled config, ``None`` when disabled, or refuse unsafe sync."""
    try:
        settings_obj = PdmPluginSettings.get_solo()
    except Exception as exc:
        logger.exception("Could not load PdmPluginSettings")
        detail = _exception_detail("PdmPluginSettings could not be loaded", exc)
        raise BranchingUnavailableError(
            "PDM sync refused: branching_enabled could not be read, so branch "
            f"isolation cannot be safely ruled out ({detail}). Restore access to "
            "PdmPluginSettings, then set branching_enabled=False to explicitly "
            "allow sync on main or restore a working branch runtime."
        ) from exc
    if not getattr(settings_obj, "branching_enabled", False):
        return None
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        raise BranchingUnavailableError(_runtime_failure_message(_BRANCHING_UNAVAILABLE))
    failure = _runtime_failure(lifecycle)
    if failure is not None:
        raise BranchingUnavailableError(_runtime_failure_message(failure))
    return {
        "prefix": getattr(settings_obj, "branch_name_prefix", "") or "pdm-sync",
        "on_conflict": getattr(settings_obj, "branch_on_conflict", "") or "fail",
    }

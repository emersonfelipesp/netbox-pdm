"""Optional netbox-branching lifecycle wrappers for PDM sync jobs."""

from __future__ import annotations

import logging
from typing import Any

from netbox_pdm.models import PdmPluginSettings

logger = logging.getLogger("netbox_pdm.branch_lifecycle")

_BRANCHING_UNAVAILABLE = (
    "Branch lifecycle support requires netbox-proxbox with its "
    "netbox_proxbox.services.branch_lifecycle helpers installed."
)

__all__ = (
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
    except ImportError:
        return None
    return branch_lifecycle


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


def merge_branch(
    *,
    branch: Any,
    user: Any | None,
    on_conflict: str,
) -> tuple[bool, str]:
    lifecycle = _proxbox_branch_lifecycle()
    if lifecycle is None:
        raise NotImplementedError(_BRANCHING_UNAVAILABLE)
    return lifecycle.merge_branch(
        branch=branch,
        user=user,
        on_conflict=on_conflict,
    )


def branching_enabled_settings() -> dict[str, str] | None:
    """Return PDM branching config, or ``None`` when disabled/unavailable."""
    if not is_branching_available():
        return None
    try:
        settings_obj = PdmPluginSettings.get_solo()
    except Exception:
        logger.exception("Could not load PdmPluginSettings")
        return None
    if not getattr(settings_obj, "branching_enabled", False):
        return None
    return {
        "prefix": getattr(settings_obj, "branch_name_prefix", "") or "pdm-sync",
        "on_conflict": getattr(settings_obj, "branch_on_conflict", "") or "fail",
    }

"""Guard against migration graph edges on NetBox core nodes absent from 4.5.8.

The plugin declares support for NetBox >= 4.5.8. Django refuses to build the
migration graph (NodeNotFoundError) when a plugin migration references a core
migration that does not exist in the running NetBox release, so every core-app
graph edge — ``dependencies`` and ``run_before`` alike — must reference a node
that exists, by exact name, in NetBox v4.5.8 (squashed ``replaces`` aliases
resolve to older nodes and stay valid).

The guard fails closed: any edge entry it cannot statically resolve to a
literal ``(app, name)`` pair is reported as an offender rather than skipped.
To add a new core dependency, verify the exact migration name exists in the
oldest supported NetBox release (``git show v4.5.8:netbox/<app>/migrations/``
in the NetBox source tree) and add it to ``ALLOWED_CORE_DEPENDENCIES``.
"""

import ast
import pathlib

PLUGIN_DIR = pathlib.Path(__file__).resolve().parent.parent / "netbox_pdm"

# Every migration-bearing NetBox core app in v4.5.8.
CORE_APPS = {
    "account",
    "circuits",
    "core",
    "dcim",
    "extras",
    "ipam",
    "tenancy",
    "users",
    "virtualization",
    "vpn",
    "wireless",
}

# Exact core migration nodes this plugin is allowed to reference. Every entry
# has been verified to exist in NetBox v4.5.8 (directly or via a squashed
# migration's ``replaces`` list).
ALLOWED_CORE_DEPENDENCIES = frozenset(
    {
        "extras.0002_squashed_0059",
        "extras.0134_owner",
    }
)

_EDGE_ATTRIBUTES = ("dependencies", "run_before")


def _iter_edge_entries(tree):
    """Yield (edge_kind, resolved_pair_or_None, source_text) for graph edges."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        targets = {getattr(target, "id", "") for target in node.targets}
        kinds = targets.intersection(_EDGE_ATTRIBUTES)
        if not kinds:
            continue
        kind = kinds.pop()
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            yield kind, None, ast.dump(node.value)[:80]
            continue
        for element in node.value.elts:
            resolved = None
            if isinstance(element, (ast.Tuple, ast.List)) and len(element.elts) == 2:
                try:
                    resolved = (
                        ast.literal_eval(element.elts[0]),
                        ast.literal_eval(element.elts[1]),
                    )
                except ValueError:
                    resolved = None
            if resolved is not None and not (
                isinstance(resolved[0], str) and isinstance(resolved[1], str)
            ):
                resolved = None
            if resolved is None and _is_swappable_dependency(element):
                continue
            yield kind, resolved, ast.dump(element)[:80]


def _is_swappable_dependency(element):
    return (
        isinstance(element, ast.Call)
        and isinstance(element.func, ast.Attribute)
        and element.func.attr == "swappable_dependency"
    )


def test_core_migration_graph_edges_exist_in_netbox_458():
    offenders = []
    for path in sorted((PLUGIN_DIR / "migrations").glob("[0-9]*.py")):
        tree = ast.parse(path.read_text())
        for kind, resolved, source in _iter_edge_entries(tree):
            if resolved is None:
                offenders.append(f"{path.name} ({kind}): unresolvable edge {source}")
                continue
            app, name = resolved
            if app not in CORE_APPS:
                continue
            if f"{app}.{name}" not in ALLOWED_CORE_DEPENDENCIES:
                offenders.append(f"{path.name} ({kind}): {app}.{name}")
    assert not offenders, (
        "Migration graph edges reference NetBox core nodes not verified to "
        "exist in v4.5.8 (or could not be statically resolved); verify against "
        "the oldest supported NetBox release and extend "
        "ALLOWED_CORE_DEPENDENCIES deliberately: " + ", ".join(offenders)
    )

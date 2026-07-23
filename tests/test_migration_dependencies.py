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
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        else:
            continue
        target_names = {getattr(target, "id", "") for target in targets}
        kinds = target_names.intersection(_EDGE_ATTRIBUTES)
        if not kinds:
            continue
        kind = kinds.pop()
        if node.value is None:
            yield kind, None, "<missing>"
            continue
        if not isinstance(node.value, (ast.List, ast.Tuple)):
            yield kind, None, ast.dump(node.value)[:80]
            continue
        for element in node.value.elts:
            resolved = _resolve_edge_element(element)
            if resolved is None and _is_swappable_dependency(element):
                continue
            yield kind, resolved, ast.dump(element)[:80]


def _resolve_edge_element(element):
    """Return a literal (app, name) string pair, or None if unresolvable."""
    if not (isinstance(element, (ast.Tuple, ast.List)) and len(element.elts) == 2):
        return None
    try:
        resolved = (
            ast.literal_eval(element.elts[0]),
            ast.literal_eval(element.elts[1]),
        )
    except ValueError:
        return None
    if not (isinstance(resolved[0], str) and isinstance(resolved[1], str)):
        return None
    return resolved


def _is_swappable_dependency(element):
    return (
        isinstance(element, ast.Call)
        and isinstance(element.func, ast.Attribute)
        and element.func.attr == "swappable_dependency"
        and isinstance(element.func.value, ast.Name)
        and element.func.value.id == "migrations"
    )


def test_iter_edge_entries_handles_annotated_assignments():
    tree = ast.parse(
        'dependencies: list[tuple[str, str]] = [("dcim", "0227_alter_interface_speed_bigint")]'
    )

    entries = list(_iter_edge_entries(tree))

    assert len(entries) == 1
    assert entries[0][:2] == (
        "dependencies",
        ("dcim", "0227_alter_interface_speed_bigint"),
    )


def test_swappable_dependency_exemption_requires_migrations_receiver():
    valid = ast.parse("migrations.swappable_dependency(settings.AUTH_USER_MODEL)").body[0].value
    impostor = ast.parse("helpers.swappable_dependency(settings.AUTH_USER_MODEL)").body[0].value

    assert _is_swappable_dependency(valid)
    assert not _is_swappable_dependency(impostor)


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

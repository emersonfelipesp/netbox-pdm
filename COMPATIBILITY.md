# Compatibility Matrix

> `proxbox-api` is a separately deployed backend service with PDM-aware endpoints.

## NetBox support tiers

`netbox-pdm` declares two NetBox support tiers, defined once in
[`netbox_pdm/compat.py`](netbox_pdm/compat.py) and vendored byte-identically across the
whole Proxbox plugin stack (`netbox-proxbox`, `netbox-ceph`, `netbox-packer`,
`netbox-pbs`, `netbox-pdm`):

| Tier | NetBox range | Constant | Behaviour |
|---|---|---|---|
| **Stable** | `4.5.8` – `4.7.0` | `STABLE_MIN_NETBOX_VERSION` / `STABLE_MAX_NETBOX_VERSION` | Admitted silently. CI exercises the established 4.5/4.6 cells and official v4.7.0 GA. |
| **Experimental** | Pre-release builds within the declared `4.5.8`–`4.7.0` loader range | Derived by `compat.py` | Loads for evaluation and warns once via system check `netbox_pdm.W001`; it is not production support. |

`PluginConfig.min_version` and `PluginConfig.max_version` are sourced from the
shared v5 compatibility contract, which admits the stable `4.5.8`–`4.7.0`
range and classifies pre-release designations as experimental. Local release
metadata is advisory only and cannot widen the loader range.

Official NetBox 4.7.0 GA emits no compatibility warning. A pre-release identity
within the loader range emits one evaluation warning from `manage.py check` and
the startup log:

```
WARNINGS:
?: (netbox_pdm.W001) NetBox PDM is running on a pre-release identity within
   the supported loader range.
```

It is a warning, never an error — it cannot block NetBox from starting.

**To silence it**, set the key in this plugin's `PLUGINS_CONFIG` entry:

```python
PLUGINS_CONFIG = {
    "netbox_pdm": {"silence_netbox_compatibility_warning": True},
}
```

That silences both the system check and the startup log line.

> Django's own `SILENCED_SYSTEM_CHECKS` is honoured too, but **not from
> `configuration.py`** — NetBox's `settings.py` imports an explicit list of
> named settings and that one is not on it, so setting it there has no effect.
> It only applies through NetBox's `local_settings.py` hatch, which upstream
> labels unsupported. Use the `PLUGINS_CONFIG` key above.

NetBox below `4.5.8` and 4.8+ are refused by the stock numeric gate.

> **These tiers describe the *next* release, not the currently published
> package.** Every artifact published before this change declares
> `max_version = "4.6.99"` and will refuse NetBox 4.7 regardless of what this
> table says. `pip install` of an older version therefore still caps at 4.6.99.

### Upgrading to NetBox 4.7 means upgrading the whole plugin stack

A Proxbox-family plugin left at the old `4.6.99` ceiling does **not** stop
NetBox from starting. `netbox/settings.py` catches `IncompatiblePluginError`,
emits a Python `warnings.warn`, and **skips that plugin** — NetBox comes up
without it.

That is easy to miss and worth stating plainly, because the quiet failure is
the dangerous one. `warnings.warn` does not reach the application log in a
normal production deployment, so the visible symptom is not an error but an
*absence*: the plugin's navigation entries, views, REST API routes, and
background jobs are simply gone, and anything that depended on them fails later
and further away. A health probe against NetBox itself still returns 200.

So before moving an instance to NetBox 4.7 GA, upgrade **every** installed
Proxbox-family plugin to a release carrying compatibility contract v5, and
afterwards verify each one is actually registered rather than trusting that
NetBox started:

```bash
python manage.py shell -c "from django.apps import apps; print([p for p in ('netbox_proxbox','netbox_pbs','netbox_pdm','netbox_ceph','netbox_packer') if apps.is_installed(p)])"
```

On 4.5.8–4.6.x, mixed versions remain fine as before.

### netbox-branching does not support NetBox 4.7 yet

`netboxlabs-netbox-branching` declares `max_version = "4.6.99"` (checked
through 1.0.3), so on NetBox 4.7 **NetBox skips it** — the package stays
importable, but its Django app is absent from `INSTALLED_APPS` and its models
and schemas do not exist.

If you use branch-isolated sync (`branching_enabled = True`), **do not move to
NetBox 4.7 until a 4.7-capable netbox-branching release exists.** The
availability detector here now requires the loaded app rather than an
importable package, so a skipped branching app is correctly reported as
unavailable. A sync configured for branch isolation that finds branching
unavailable refuses to continue rather than silently dropping the isolation
boundary; the sync job also fails closed when the settings or helper is
unavailable.

Installations that do not use branching are unaffected.

**Pre-release version strings.** NetBox's stock loader passes the numeric
`RELEASE.version` to `PluginConfig.validate()`. The shared compatibility module
keeps the stable GA range in one place and emits an advisory for pre-release
designations without making them production support.

**Current GA evidence.** A required source-checkout job runs PDM and
its required Proxbox dependency on exact NetBox `v4.7.0` commit
`5f06007e4c9bacc93ce17c1e645fc1143d60df3d`. The stable Docker matrix now
extends through v4.6.6 and remains the backward-compatibility evidence.

| netbox-pdm | NetBox | Python | netbox-proxbox peer plugin | proxbox-api | PDM client |
|---|---|---|---|---|---|
| v0.0.2 branch | v4.5.8-v4.6.6 plus held v4.7.0 | ≥3.12 | >=0.0.18,<0.1.0 | Required | proxmox-sdk>=0.0.12 |
| v0.0.1.post1 | 4.5.8 – 4.6.x | ≥3.12 | >=0.0.18,<0.1.0 | Required | ≥2.33.0 |
| v0.0.1 | 4.5.x – 4.6.x | ≥3.12 | ≥0.0.16.post5 | Required | ≥2.33.0 |

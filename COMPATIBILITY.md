# Compatibility Matrix

> `proxbox-api` is a separately deployed backend service with PDM-aware endpoints.

## NetBox support tiers

`netbox-pdm` declares two NetBox support tiers, defined once in
[`netbox_pdm/compat.py`](netbox_pdm/compat.py) and vendored byte-identically across the
whole Proxbox plugin stack (`netbox-proxbox`, `netbox-ceph`, `netbox-packer`,
`netbox-pbs`, `netbox-pdm`):

| Tier | NetBox range | Constant | Behaviour |
|---|---|---|---|
| **Stable** | `4.5.8` – `4.6.99` | `STABLE_MIN_NETBOX_VERSION` / `STABLE_MAX_NETBOX_VERSION` | Admitted silently. Directly exercised in CI at v4.5.8 through v4.6.4 (Docker image matrix); the rest of the band is admitted on the strength of those. |
| **Experimental** | `4.7.0` – `4.7.99` | `EXPERIMENTAL_MIN_NETBOX_VERSION` / `EXPERIMENTAL_MAX_NETBOX_VERSION` | Loads and runs normally; warns once via system check `netbox_pdm.W001`. |

`PluginConfig.min_version` is the stable floor; `PluginConfig.max_version` is the
**experimental** ceiling (`4.7.99`). Admitting 4.7 without an opt-in is
deliberate — an operator upgrading NetBox never has to touch plugin
configuration. Experimental support needs no setting, no flag, and no extra
install step.

On a 4.7 install you will see one warning per plugin, from `manage.py check` and
in the startup log:

```
WARNINGS:
?: (netbox_pdm.W001) NetBox PDM is running on NetBox 4.7.0-beta1, which is
   supported on an experimental basis only. Certified support covers NetBox
   4.5.8 through 4.6.99.
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

NetBox below `4.5.8` and from `4.8` onward is still refused outright by NetBox's
own plugin version gate.

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

So before moving an instance to 4.7, upgrade **every** installed Proxbox-family
plugin to a release carrying the `4.7.99` ceiling, and afterwards verify each
one is actually registered rather than trusting that NetBox started:

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
unavailable; but a sync configured for branch isolation that finds branching
unavailable currently proceeds against `main` rather than refusing, which
silently drops the isolation boundary you configured. Tightening that to
fail closed is tracked separately.

Installations that do not use branching are unaffected.

**Beta version strings.** NetBox's `release.yaml` at tag `v4.7.0-beta1` reads
`version: "4.7.0"` with `designation: "beta1"`, and `netbox/settings.py` passes
`RELEASE.version` — the bare `"4.7.0"` — to `PluginConfig.validate()`. The
`4.7.99` ceiling is sized for that comparison string; `RELEASE.full_version`
(`"4.7.0-beta1"`) is used only for display.

| netbox-pdm | NetBox | Python | netbox-proxbox peer plugin | proxbox-api | PDM client |
|---|---|---|---|---|---|
| v0.0.2 | v4.5.8, v4.5.9, v4.6.0-v4.6.4 | ≥3.12 | >=0.0.18,<0.1.0 | Required | proxmox-sdk>=0.0.12 |
| v0.0.1.post1 | 4.5.8 – 4.6.x | ≥3.12 | >=0.0.18,<0.1.0 | Required | ≥2.33.0 |
| v0.0.1 | 4.5.x – 4.6.x | ≥3.12 | ≥0.0.16.post5 | Required | ≥2.33.0 |

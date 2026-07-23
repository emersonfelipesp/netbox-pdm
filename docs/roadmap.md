# Roadmap

## Released

- **v0.0.1** — Initial plugin scaffold: NetBox installation, navigation,
  overview page, packaging, docs, CI.
- **v0.0.1.post1** — Certification-readiness: package metadata,
  licensing, compatibility evidence, release validation, and docs.
- **v0.0.2** — PDMEndpoint/PDMRemote views, PDMSyncJob (direct proxmox-sdk
  connection to PDM), branching support, PdmPluginSettings singleton.
- **v0.0.2 post-release fix** — corrected the migration `0002` dependency
  graph so it resolves on NetBox 4.5.x (see
  [release notes](release-notes/version-0.0.2.md#post-release-fix-netbox-45x-migration-graph)).

## Planned

- **v0.0.3 / v0.1.0** — Deeper PDM API surface: node resource usage,
  HA state, storage usage reflected as additional NetBox models.
- **Later** — SDN-adjacent state reflection (PDM-managed SDN zones and VNets).
- **Later** — Write-back support: push NetBox-managed PDM config changes
  through proxbox-api.

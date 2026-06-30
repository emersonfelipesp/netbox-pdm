# NetBox Plugin Certification Evidence

This checklist tracks readiness for the NetBox Plugin Certification Program.

| Requirement | Evidence |
| --- | --- |
| Open source license | Apache-2.0 in `LICENSE` and `pyproject.toml` |
| Package metadata | PyPI project `netbox-pdm`, project URLs, classifiers, Python `>=3.12` |
| NetBox compatibility | Plugin config declares `min_version = "4.5.8"` and `max_version = "4.6.99"` |
| Dependency policy | Python dependencies keep `proxmox-sdk>=0.0.12` resolvable; `netbox-proxbox>=0.0.18,<0.1.0` is enforced as a NetBox peer plugin and PDM communicates with `proxbox-api` over HTTP |
| CI | GitHub Actions run lint, compile, pytest, docs, page coverage, screenshot capture, and release validation |
| Documentation | README, MkDocs site, installation, roadmap, release notes, and support links |
| Screenshots | `.github/workflows/docs-screenshots.yml` captures deterministic NetBox v4.6.4 UI screenshots into `docs/assets/screenshots` |
| Icon | NetBox menu uses Material Design Icons class `mdi mdi-server-network` |
| Maintainer access | Repositories stay under `emersonfelipesp`; NetBox Labs staff can be invited as collaborators when requested |

## Application Summary

- Repository: <https://github.com/emersonfelipesp/netbox-pdm>
- Documentation: <https://emersonfelipesp.github.io/netbox-pdm/>
- PyPI: <https://pypi.org/project/netbox-pdm/>
- Support: <https://github.com/emersonfelipesp/netbox-pdm/issues>
- Certification target release: `0.0.2`
- Verified NetBox targets: `v4.5.8`, `v4.5.9`, `v4.6.0`, `v4.6.1`, `v4.6.2`, `v4.6.3`, and `v4.6.4`

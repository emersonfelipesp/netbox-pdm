# NetBox Plugin Certification Evidence

This checklist tracks readiness for the NetBox Plugin Certification Program.

| Requirement | Evidence |
| --- | --- |
| Open source license | Apache-2.0 in `LICENSE` and `pyproject.toml` |
| Package metadata | PyPI project `netbox-pdm`, project URLs, classifiers, Python `>=3.12` |
| NetBox compatibility | Stable `4.5.8`–`4.6.99` plus canonical `v4.7.0-beta2` metadata under the fail-closed v3 identity guard; final/other 4.7 identities remain held |
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
- Verified historical targets extend through `v4.6.4`; the current matrix adds
  v4.6.6 and beta2 revision
  `aa1d49d0f5021a28e6efc2d0364b84c5bcec7137`.

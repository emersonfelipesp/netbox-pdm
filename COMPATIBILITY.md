# Compatibility Matrix

> `proxbox-api` is a separately deployed backend service. `netbox-pdm`
> communicates with it over HTTP.

## Supported NetBox releases

`netbox-pdm` is an Emerson-owned plugin. Its compatibility contract preserves
the historical NetBox `4.5.8` floor and adds official NetBox `4.7.0` GA.
The declared plugin bounds are `4.5.8` through `4.7.0`.

NetBox 4.7 prereleases remain experimental and are not production support.
NetBox 4.7.1 and later are outside this release's tested contract.

The shared compatibility module is vendored byte-identically across
`netbox-proxbox`, `netbox-ceph`, `netbox-pbs`, and `netbox-pdm`.

## Verification matrix

| Plugin release | NetBox releases | Python | proxbox-api |
|---|---|---|---|
| v0.0.2 branch | v4.5.8–v4.6.6 and official v4.7.0 GA | ≥3.12 | Required |
| v0.0.1 | 4.5.x–4.6.x | ≥3.12 | Required |

The legacy 4.5/4.6 cells remain in CI for backward compatibility. The GA cell
uses the exact NetBox source revision
`5f06007e4c9bacc93ce17c1e645fc1143d60df3d`, and the Docker smoke matrix uses
the pinned official image
`netboxcommunity/netbox:v4.7.0-5.1.0@sha256:73a54ff279461170032b59a57a1930929965e3ba15c195af59f4b5f6d39a84a9`.

## Upgrade procedure

Install the GA-capable PDM wheel before upgrading a production NetBox instance.
Run the normal NetBox migration and verify that `netbox_pdm` is registered.
Existing 4.5.8–4.6.x installations retain their supported floor and do not
require a database reset or configuration rewrite.

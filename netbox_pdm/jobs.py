"""Background RQ jobs for netbox-pdm sync operations."""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from netbox.constants import RQ_QUEUE_DEFAULT
from netbox.jobs import JobRunner

PDM_SYNC_JOB_TIMEOUT = 600  # 10 minutes
PDM_SYNC_QUEUE_NAME = RQ_QUEUE_DEFAULT

__all__ = ("PDMSyncJob",)


def _build_pdm_session(endpoint: object) -> object:
    """Build a requests.Session pre-configured with PDM API token auth.

    PDM token format differs from PVE: separator is `:`, prefix is `PDM`.
    Header: ``Authorization: PDMAPIToken=user@realm!tokenname:secret``

    TLS verification is always on unless the operator explicitly sets
    ``verify_ssl=False`` on the PDMEndpoint (for self-signed internal CA certs).
    When disabled, a CRITICAL log entry is emitted — this should only be
    used in air-gapped/internal deployments where a proper CA cannot be added.
    """
    import logging
    import requests

    log = logging.getLogger(__name__)
    session = requests.Session()
    auth_header = f"PDMAPIToken={endpoint.token_id}:{endpoint.token_secret}"
    session.headers["Authorization"] = auth_header
    session.headers["Accept"] = "application/json"
    if not endpoint.verify_ssl:
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        session.verify = False
        log.critical(
            "PDMEndpoint '%s': TLS verification DISABLED (verify_ssl=False). "
            "This allows MITM attacks. Add the server CA to your trust store "
            "or issue a proper certificate for production use.",
            endpoint,
        )
    return session


def _pdm_base_url(endpoint: object) -> str:
    host = endpoint.domain or (
        str(endpoint.ip_address.address.ip) if endpoint.ip_address else None
    )
    if not host:
        raise ValueError(f"PDMEndpoint pk={endpoint.pk} has no host or IP address.")
    return f"https://{host}:{endpoint.port}/api2/json"


def _fetch_pdm_remotes(endpoint: object, log: logging.Logger) -> list[dict]:
    """Call GET /remotes/remote on the PDM endpoint and return raw remote dicts.

    PDM 1.x uses /api2/json/remotes/remote for the combined PVE+PBS remote list.
    The top-level /api2/json/remotes returns a subdir index, not the remote list.
    """
    session = _build_pdm_session(endpoint)
    base = _pdm_base_url(endpoint)
    timeout = endpoint.timeout or 30
    resp = session.get(f"{base}/remotes/remote", timeout=timeout)
    resp.raise_for_status()
    data = resp.json()
    remotes = data.get("data", [])
    log.info("PDM %s returned %d remotes.", endpoint, len(remotes))
    return remotes


def _sync_remotes(endpoint: object, raw_remotes: list[dict], log: logging.Logger) -> dict:
    """Reconcile raw PDM remote dicts into NetBox PDMRemote records."""
    from django.utils.timezone import now
    from netbox_proxbox.models import PDMRemote

    created = updated = 0
    seen_names: set[str] = set()

    for raw in raw_remotes:
        remote_name = raw.get("id") or raw.get("name")
        if not remote_name:
            log.warning("Skipping PDM remote with no id/name: %s", raw)
            continue
        remote_type = raw.get("type", "pve")
        nodes = raw.get("nodes") or []
        hostname = nodes[0].get("hostname", "") if nodes else ""
        fingerprint = nodes[0].get("fingerprint", "") if nodes else (raw.get("fingerprint") or "")
        seen_names.add(remote_name)

        defaults = {
            "type": remote_type,
            "hostname": hostname,
            "fingerprint": fingerprint,
            "version": "",
            "last_seen_at": now(),
        }
        obj, new = PDMRemote.objects.update_or_create(
            pdm_endpoint=endpoint,
            name=remote_name,
            defaults=defaults,
        )
        if new:
            created += 1
            log.info("Created PDMRemote '%s' (type=%s).", remote_name, remote_type)
        else:
            updated += 1
            log.debug("Updated PDMRemote '%s'.", remote_name)

    return {"created": created, "updated": updated, "total": len(raw_remotes)}


class PDMSyncJob(JobRunner):
    """Sync Proxmox Datacenter Manager data into NetBox PDMRemote records.

    Dispatch via::

        PDMSyncJob.enqueue(endpoint_pk=<pk>)

    Note: do NOT pass ``instance=`` — PDMEndpoint is not a jobs-assignable object
    type in the current NetBox plugin configuration.
    """

    class Meta:
        name = "PDM Sync"

    @classmethod
    def enqueue(cls, *args, instance=None, **kwargs):
        endpoint_pk = kwargs.pop("endpoint_pk", None)
        kwargs.setdefault("job_timeout", PDM_SYNC_JOB_TIMEOUT)
        job = super().enqueue(*args, instance=instance, **kwargs)
        data = job.data or {}
        if endpoint_pk is not None:
            data["endpoint_pk"] = endpoint_pk
        job.data = data
        job.save(update_fields=["data"])
        return job

    def run(self, *args: object, **kwargs: object) -> None:
        from netbox_proxbox.models import PDMEndpoint

        raw_data = self.job.data or {}
        endpoint_pk = raw_data.get("endpoint_pk")
        if endpoint_pk is None:
            raise RuntimeError("PDMSyncJob requires endpoint_pk in job data.")

        try:
            endpoint = PDMEndpoint.objects.get(pk=endpoint_pk)
        except PDMEndpoint.DoesNotExist:
            raise RuntimeError(f"PDMEndpoint pk={endpoint_pk} not found.")

        if not endpoint.enabled:
            self.logger.warning("PDMEndpoint '%s' is disabled — skipping sync.", endpoint)
            return

        self.logger.info("Starting PDM sync for endpoint '%s'.", endpoint)

        raw_remotes = _fetch_pdm_remotes(endpoint, self.logger)
        result = _sync_remotes(endpoint, raw_remotes, self.logger)

        data = self.job.data or {}
        data["result"] = result
        self.job.data = data
        self.logger.info(
            "PDM sync complete for '%s': created=%d updated=%d.",
            endpoint,
            result["created"],
            result["updated"],
        )

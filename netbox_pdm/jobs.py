"""Background RQ jobs for netbox-pdm sync operations."""

from __future__ import annotations

import logging

from netbox.constants import RQ_QUEUE_DEFAULT
from netbox.jobs import JobRunner

PDM_SYNC_JOB_TIMEOUT = 600  # 10 minutes
PDM_SYNC_QUEUE_NAME = RQ_QUEUE_DEFAULT

__all__ = ("PDMSyncJob",)


def _make_pdm_client(endpoint: object) -> object:
    """Construct a :class:`~proxmox_sdk.pdm.client.SyncPDMClient` for *endpoint*.

    PDM token format: ``user@realm!tokenname:secret`` (separator ``:``, prefix
    ``PDM``).  :func:`~proxmox_sdk.sdk.auth.token.parse_token_id` splits the
    ``token_id`` field (e.g. ``root@pam!my-token``) into the ``user`` and
    ``token_name`` parts that the SDK expects.

    TLS verification is always on unless the operator explicitly sets
    ``verify_ssl=False`` on the PDMEndpoint (for self-signed internal CA certs).
    When disabled, a CRITICAL log entry is emitted — this should only be used in
    air-gapped/internal deployments where a proper CA cannot be added.
    """
    from proxmox_sdk.pdm.client import SyncPDMClient
    from proxmox_sdk.sdk.auth.token import parse_token_id

    log = logging.getLogger(__name__)

    host = endpoint.domain or (
        str(endpoint.ip_address.address.ip) if endpoint.ip_address else None
    )
    if not host:
        raise ValueError(f"PDMEndpoint pk={endpoint.pk} has no host or IP address.")

    user, token_name = parse_token_id(endpoint.token_id)

    if not endpoint.verify_ssl:
        log.critical(
            "PDMEndpoint '%s': TLS verification DISABLED (verify_ssl=False). "
            "This allows MITM attacks. Add the server CA to your trust store "
            "or issue a proper certificate for production use.",
            endpoint,
        )

    return SyncPDMClient(
        host=host,
        user=user,
        token_name=token_name,
        token_value=endpoint.token_secret,
        port=endpoint.port,
        verify_ssl=endpoint.verify_ssl,
        timeout=endpoint.timeout or 30,
    )


def _fetch_pdm_remotes(endpoint: object, log: logging.Logger) -> list:
    """Return typed ``PDMRemote`` objects from the PDM endpoint.

    Uses :class:`~proxmox_sdk.pdm.client.SyncPDMClient` with the fully typed
    :class:`~proxmox_sdk.pdm.domains.remotes.RemotesDomain` so all PDM API
    path correctness and response parsing is handled by the SDK.
    """
    with _make_pdm_client(endpoint) as client:
        remotes = client.remotes.list()
    log.info("PDM %s returned %d remotes.", endpoint, len(remotes))
    return remotes


def _sync_remotes(endpoint: object, remotes: list, log: logging.Logger) -> dict:
    """Reconcile typed PDM remote objects into NetBox ``PDMRemote`` records."""
    from django.utils.timezone import now
    from netbox_proxbox.models import PDMRemote as PDMRemoteRecord

    created = updated = 0

    for remote in remotes:
        remote_name = remote.id
        if not remote_name:
            log.warning("Skipping PDM remote with no id: %s", remote)
            continue

        remote_type = remote.type or "pve"
        nodes = remote.nodes or []
        hostname = nodes[0].hostname if nodes else ""
        fingerprint = (
            (nodes[0].fingerprint or "") if nodes else (remote.fingerprint or "")
        )

        defaults = {
            "type": remote_type,
            "hostname": hostname,
            "fingerprint": fingerprint,
            "version": "",
            "last_seen_at": now(),
        }
        _obj, new = PDMRemoteRecord.objects.update_or_create(
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

    return {"created": created, "updated": updated, "total": len(remotes)}


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
        # Keep endpoint_pk in kwargs so it flows through RQ to run(**kwargs),
        # AND persist it in job.data for UI inspection.
        kwargs.setdefault("job_timeout", PDM_SYNC_JOB_TIMEOUT)
        endpoint_pk = kwargs.get("endpoint_pk")
        job = super().enqueue(*args, instance=instance, **kwargs)
        if endpoint_pk is not None:
            data = job.data or {}
            data["endpoint_pk"] = endpoint_pk
            job.data = data
            job.save(update_fields=["data"])
        return job

    def run(self, *args: object, **kwargs: object) -> None:
        from netbox_proxbox.models import PDMEndpoint

        # Prefer kwargs (passed directly through RQ), fall back to job.data.
        endpoint_pk = kwargs.get("endpoint_pk")
        if endpoint_pk is None:
            self.job.refresh_from_db(fields=["data"])
            endpoint_pk = (self.job.data or {}).get("endpoint_pk")
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

        remotes = _fetch_pdm_remotes(endpoint, self.logger)
        result = _sync_remotes(endpoint, remotes, self.logger)

        data = self.job.data or {}
        data["result"] = result
        self.job.data = data
        self.logger.info(
            "PDM sync complete for '%s': created=%d updated=%d.",
            endpoint,
            result["created"],
            result["updated"],
        )

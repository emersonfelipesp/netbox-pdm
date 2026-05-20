"""Singleton plugin-settings model for netbox-pdm."""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _
from netbox.models import NetBoxModel

PDM_BRANCH_ON_CONFLICT_CHOICES = (
    ("fail", _("Fail and leave branch open for review")),
    ("acknowledge", _("Acknowledge conflicts and merge anyway")),
)


class PdmPluginSettings(NetBoxModel):
    """Singleton-style settings row for netbox-pdm sync behavior."""

    singleton_key = models.CharField(
        max_length=32,
        unique=True,
        default="default",
        editable=False,
    )
    proxbox_api_url = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("proxbox-api URL"),
        help_text=_(
            "Base URL used when netbox-proxbox FastAPIEndpoint resolution is not available."
        ),
    )
    proxbox_api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_("proxbox-api API key"),
        help_text=_("Optional bearer token used with the standalone proxbox-api URL."),
    )
    branching_enabled = models.BooleanField(
        default=False,
        verbose_name=_("Branching-enabled sync (PDM -> NetBox)"),
        help_text=_(
            "When enabled, PDM sync jobs create a netbox-branching branch, run sync "
            "against that branch, and merge the branch back into main on success."
        ),
    )
    branch_name_prefix = models.CharField(
        max_length=64,
        default="pdm-sync",
        verbose_name=_("Branch name prefix"),
    )
    branch_on_conflict = models.CharField(
        max_length=16,
        choices=PDM_BRANCH_ON_CONFLICT_CHOICES,
        default="fail",
        verbose_name=_("Branch merge conflict policy"),
    )

    class Meta:
        verbose_name = _("PDM plugin settings")
        verbose_name_plural = _("PDM plugin settings")

    def __str__(self) -> str:
        return "PDM plugin settings"

    def save(self, *args: object, **kwargs: object) -> None:
        self.singleton_key = "default"
        super().save(*args, **kwargs)

    @classmethod
    def get_solo(cls) -> "PdmPluginSettings":
        obj, _created = cls.objects.get_or_create(singleton_key="default")
        return obj

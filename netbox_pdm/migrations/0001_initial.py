"""Initial migration: creates PdmPluginSettings table."""

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("extras", "0002_squashed_0059"),
    ]

    operations = [
        migrations.CreateModel(
            name="PdmPluginSettings",
            fields=[
                (
                    "id",
                    models.BigAutoField(auto_created=True, primary_key=True, serialize=False),
                ),
                ("created", models.DateTimeField(auto_now_add=True, null=True)),
                ("last_updated", models.DateTimeField(auto_now=True, null=True)),
                (
                    "custom_field_data",
                    models.JSONField(blank=True, default=dict, encoder=None),
                ),
                (
                    "singleton_key",
                    models.CharField(
                        default="default",
                        editable=False,
                        max_length=32,
                        unique=True,
                    ),
                ),
                (
                    "proxbox_api_url",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="proxbox-api URL",
                    ),
                ),
                (
                    "proxbox_api_key",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        verbose_name="proxbox-api API key",
                    ),
                ),
                (
                    "branching_enabled",
                    models.BooleanField(
                        default=False,
                        verbose_name="Branching-enabled sync (PDM -> NetBox)",
                    ),
                ),
                (
                    "branch_name_prefix",
                    models.CharField(
                        default="pdm-sync",
                        max_length=64,
                        verbose_name="Branch name prefix",
                    ),
                ),
                (
                    "branch_on_conflict",
                    models.CharField(
                        choices=[
                            ("fail", "Fail and leave branch open for review"),
                            ("acknowledge", "Acknowledge conflicts and merge anyway"),
                        ],
                        default="fail",
                        max_length=16,
                        verbose_name="Branch merge conflict policy",
                    ),
                ),
            ],
            options={
                "verbose_name": "PDM plugin settings",
                "verbose_name_plural": "PDM plugin settings",
            },
        ),
    ]

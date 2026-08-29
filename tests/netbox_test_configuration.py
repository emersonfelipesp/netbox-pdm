"""NetBox configuration for real PDM compatibility tests."""

import os

from netbox.configuration_testing import *  # noqa: F403
from netbox.configuration_testing import PLUGINS as BASE_PLUGINS

PLUGINS = [*BASE_PLUGINS, "netbox_proxbox", "netbox_pdm"]

DATABASES["default"].update(  # noqa: F405
    {
        "NAME": os.environ.get("NETBOX_DB_NAME", "netbox"),
        "USER": os.environ.get("NETBOX_DB_USER", "netbox"),
        "PASSWORD": os.environ.get("NETBOX_DB_PASSWORD", "netbox"),
        "HOST": os.environ.get("NETBOX_DB_HOST", "localhost"),
        "PORT": os.environ.get("NETBOX_DB_PORT", ""),
        "CONN_MAX_AGE": 0,
    }
)
for redis_database in REDIS.values():  # noqa: F405
    redis_database["HOST"] = os.environ.get("NETBOX_REDIS_HOST", "localhost")
    redis_database["PORT"] = int(os.environ.get("NETBOX_REDIS_PORT", "6379"))

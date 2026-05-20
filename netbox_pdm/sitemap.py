"""Sitemap view for netbox-pdm — serves a plain-text list of all plugin pages."""

from __future__ import annotations

from importlib.metadata import version as _pkg_version

from django.http import HttpRequest, HttpResponse
from django.views import View
from utilities.views import ConditionalLoginRequiredMixin

_SECTIONS: list[tuple[str, list[tuple[str, str]]]] = [
    (
        "Home",
        [
            ("home", "/plugins/pdm/"),
            ("sitemap", "/plugins/pdm/sitemap.txt"),
        ],
    ),
]


def _build_sitemap(base: str) -> list[str]:
    lines: list[str] = []
    try:
        version = _pkg_version("netbox-pdm")
        lines.append(f"# netbox-pdm {version} — plugin sitemap")
    except Exception:  # noqa: BLE001
        lines.append("# netbox-pdm — plugin sitemap")
    lines.append(f"# Base: {base}")
    for section, pages in _SECTIONS:
        lines.append("")
        lines.append(f"# {section}")
        for label, path in pages:
            lines.append(f"{base}{path}  # {label}")
    return lines


class SitemapView(ConditionalLoginRequiredMixin, View):
    def get(self, request: HttpRequest) -> HttpResponse:
        base = request.build_absolute_uri("/").rstrip("/")
        body = "\n".join(_build_sitemap(base)) + "\n"
        return HttpResponse(body, content_type="text/plain; charset=utf-8")

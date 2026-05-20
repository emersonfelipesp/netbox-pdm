"""Capture Playwright screenshots of the netbox-pdm plugin UI.

Usage:
    pip install playwright requests
    playwright install chromium
    python scripts/capture_screenshots.py

Required environment variables (set by docs-screenshots.yml):
    NETBOX_BASE_URL    http://127.0.0.1:18080
    NETBOX_API_TOKEN   (NetBox admin token)

Optional:
    SCREENSHOTS_DIR    path to write PNGs (default: docs/assets/screenshots)
"""

from __future__ import annotations

import os
import pathlib

_REPO_ROOT = pathlib.Path(__file__).parent.parent

PAGES: list[tuple[str, str]] = [
    ("home", "/plugins/pdm/"),
]


def login(page, base_url: str) -> None:
    page.goto(f"{base_url}/login/")
    page.fill("#id_username", "admin")
    page.fill("#id_password", "admin")
    page.click("[type=submit]")
    page.wait_for_load_state("load")
    print(f"Logged in to NetBox at {base_url}")


def capture(page, base_url: str, slug: str, path: str, out_dir: pathlib.Path) -> None:
    url = f"{base_url}{path}"
    print(f"  Capturing {slug} -> {url}")
    page.goto(url)
    page.wait_for_load_state("load")
    page.wait_for_timeout(1500)
    dest = out_dir / f"{slug}.png"
    page.screenshot(path=str(dest), full_page=True)
    print(f"  Saved: {dest}")


def main() -> None:
    netbox_base_url = os.environ.get("NETBOX_BASE_URL", "http://127.0.0.1:18080").rstrip("/")

    screenshots_dir = pathlib.Path(
        os.getenv("SCREENSHOTS_DIR", str(_REPO_ROOT / "docs" / "assets" / "screenshots"))
    )
    screenshots_dir.mkdir(parents=True, exist_ok=True)

    print(f"Screenshots will be written to: {screenshots_dir}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        login(page, netbox_base_url)

        print(f"Capturing {len(PAGES)} pages...")
        for slug, path in PAGES:
            capture(page, netbox_base_url, slug, path, screenshots_dir)

        browser.close()

    print(f"\nDone. {len(PAGES)} screenshots written to {screenshots_dir}")


if __name__ == "__main__":
    main()

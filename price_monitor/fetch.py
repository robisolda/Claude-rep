from __future__ import annotations

import logging
import random
import time

import requests

log = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "it-IT,it;q=0.9,en;q=0.6",
}


def fetch_requests(session: requests.Session, url: str, retries: int = 3) -> str | None:
    for attempt in range(retries):
        try:
            resp = session.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200 and "captcha" not in resp.url.lower():
                return resp.text
            log.warning("%s -> HTTP %s", url, resp.status_code)
        except requests.RequestException as exc:
            log.warning("%s -> %s", url, exc)
        time.sleep(2 ** attempt + random.random())
    return None


def fetch_browser(url: str) -> str | None:
    """Render with headless Chromium for pages that need JavaScript or block plain HTTP clients."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.info("Playwright not installed, skipping browser fetch for %s", url)
        return None
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(locale="it-IT", user_agent=HEADERS["User-Agent"])
            page.goto(url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_timeout(4_000)
            page.mouse.wheel(0, 6_000)  # trigger lazy-loaded product tiles
            page.wait_for_timeout(2_000)
            html = page.content()
            browser.close()
            return html
    except Exception as exc:  # noqa: BLE001 - any browser failure just means "no page"
        log.warning("Browser fetch failed for %s: %s", url, exc)
        return None

"""Render the BRUMBLE logo and social assets to PNG.
Requires the localhost server: python -m http.server 8741 (run from this folder).
"""
from playwright.sync_api import sync_playwright

BASE = "http://localhost:8741/assets"
OUT = "assets"

JOBS = [
    (f"{BASE}/logo.svg",    1000, 600,  2, f"{OUT}/logo-2000x1200.png"),
    (f"{BASE}/avatar.html", 1024, 1024, 1, f"{OUT}/brumble-avatar-1024.png"),
    (f"{BASE}/banner.html", 1500, 500,  1, f"{OUT}/brumble-banner-1500x500.png"),
]

with sync_playwright() as p:
    browser = p.chromium.launch()
    for url, w, h, scale, out in JOBS:
        page = browser.new_page(viewport={"width": w, "height": h}, device_scale_factor=scale)
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        try:
            page.evaluate("document.fonts.ready")
            page.wait_for_timeout(1200)
        except Exception:
            pass
        page.screenshot(path=out)
        page.close()
        print("wrote", out)
    browser.close()

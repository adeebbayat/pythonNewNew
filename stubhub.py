# filename: stubhub_lowest_price.py
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re
from pathlib import Path
import time

URL = "https://www.stubhub.com/subtronics-las-vegas-tickets-10-18-2025/event/157758258/?quantity=2&sortDirection=0&sortBy=NEWPRICE"

PRICE_RX = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d{2})?)\s*$")

def extract_price(text: str):
    m = PRICE_RX.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None

def click_if_present(page, selectors, timeout=1500):
    for sel in selectors:
        try:
            page.locator(sel).first.wait_for(timeout=timeout)
            page.locator(sel).first.click()
            return True
        except PWTimeoutError:
            pass
    return False

def main():
    with sync_playwright() as p:
        # Try Chromium first; if the page closes or times out, we’ll retry with WebKit
        for engine in ("chromium", "webkit"):
            try:
                browser_type = getattr(p, engine)
                browser = browser_type.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"] if engine == "chromium" else None,
                )
                context = browser.new_context(
                    viewport={"width": 1300, "height": 900},
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/124.0.0.0 Safari/537.36"
                        if engine == "chromium"
                        else "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                             "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
                    ),
                    locale="en-US",
                )
                page = context.new_page()

                # Go to the already-sorted URL; do NOT wait for networkidle
                page.goto(URL, wait_until="domcontentloaded")

                # Clear common overlays if present
                click_if_present(page, [
                    "button:has-text('Accept all')",
                    "button:has-text('Accept All')",
                    "button:has-text('I Accept')",
                    "button:has-text('Agree')",
                    "button:has-text('Continue')",
                    "button[aria-label='Close']",
                ])

                # Some content lazy-loads; scroll a bit
                for _ in range(3):
                    page.mouse.wheel(0, 1200)
                    time.sleep(0.6)

                # Wait specifically for an element that *looks like a price* (regex)
                price_loc = page.locator("text=/^\\$\\d[\\d,]*(?:\\.\\d{2})?$/").first
                price_loc.wait_for(timeout=45000)  # wait up to 45s for first price to appear

                # Read the first (lowest) price
                raw = price_loc.inner_text().strip()
                val = extract_price(raw)
                if val is None:
                    raise RuntimeError(f"Matched a price-looking node but failed to parse: {raw!r}")

                print(f"Lowest ticket price: ${val:,.2f}")

                browser.close()
                return
            except Exception as e:
                # Save diagnostics and retry with another engine if available
                try:
                    Path(f"debug_{engine}.html").write_text(page.content())
                    page.screenshot(path=f"debug_{engine}.png", full_page=True)
                except Exception:
                    pass
                try:
                    browser.close()
                except Exception:
                    pass
                if engine == "webkit":
                    # Already retried with WebKit; re-raise
                    raise

if __name__ == "__main__":
    main()

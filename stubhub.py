# filename: stubhub_read_lowest_price.py
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re, os
from pathlib import Path

URL = "https://www.stubhub.com/subtronics-las-vegas-tickets-10-18-2025/event/157758258/?quantity=2&sortDirection=0&sortBy=NEWPRICE"
USER_DATA_DIR = str(Path.home() / ".stubhub_playwright_profile")
PRICE_RX = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d{2})?)\s*$")

def extract_price(text: str):
    m = PRICE_RX.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None

def main():
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            viewport={"width": 1300, "height": 900},
            timezone_id="America/Los_Angeles",
            locale="en-US",
        )
        page = ctx.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        price = page.locator(r"text=/^\$\d[\d,]*(?:\.\d{2})?$/").first
        try:
            price.wait_for(timeout=30000)
            raw = price.inner_text().strip()
            val = extract_price(raw)
            if val is None:
                print("Failed to get price")
            else:
                print(f"Lowest ticket price: ${val:,.2f}")
        except PWTimeoutError:
            print("Failed to get price")
        finally:
            ctx.close()

if __name__ == "__main__":
    main()

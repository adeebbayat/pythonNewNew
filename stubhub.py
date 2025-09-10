
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re, os, smtplib, ssl
from pathlib import Path

URL = "https://www.stubhub.com/subtronics-los-angeles-tickets-12-6-2025/event/158449443/?quantity=2"
USER_DATA_DIR = str(Path.home() / ".stubhub_playwright_profile")
PRICE_RX = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d{2})?)\s*$")

# ---- Email config ----
SENDER = "adeebautomation01@gmail.com"
PASSWORD = "canwvcbdqdkzrenw"   # Gmail app password
RECEIVER = "adeebbayat@gmail.com"
# ----------------------

def extract_price(text: str):
    m = PRICE_RX.search(text or "")
    return float(m.group(1).replace(",", "")) if m else None

def send_email(message: str):
    email_text = f"""\
From: {SENDER}
To: {RECEIVER}
Subject: StubHub Price Update

{message}
"""
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        server.login(SENDER, PASSWORD)
        server.sendmail(SENDER, RECEIVER, email_text)

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
        result = "Failed to get price"
        try:
            price.wait_for(timeout=30000)
            raw = price.inner_text().strip()
            val = extract_price(raw)
            if val is not None:
                result = f"Lowest ticket price: ${val:,.2f}"
        except PWTimeoutError:
            result = "Failed to get price"
        finally:
            ctx.close()

        print(result)
        send_email(result)

if __name__ == "__main__":
    main()

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re, os, smtplib, ssl, time
from pathlib import Path

URL = "https://www.stubhub.com/disclosure-berkeley-tickets-9-27-2025/event/158459048/?quantity=1"
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

        # Grab first 4 prices on the page
        price_elements = page.locator(r"text=/^\$\d[\d,]*(?:\.\d{2})?$/").all()[:4]
        all_prices = []
        for el in price_elements:
            try:
                el.wait_for(timeout=30000)
                raw = el.inner_text().strip()
                val = extract_price(raw)
                if val is not None:
                    all_prices.append(val)
            except PWTimeoutError:
                pass
        time.sleep(15)
        ctx.close()

    if len(all_prices) >= 4:
        cheapest = all_prices[1]   # using second price as per your logic
        avg_next_two = (all_prices[2] + all_prices[3]) / 2
        diff = cheapest - avg_next_two
        diff_percent = round((diff / avg_next_two) * 100, 2)

        if diff > 0:
            message = f"Cheapest price ${cheapest:.2f} is {diff_percent}% HIGHER than the next two prices averaged ${avg_next_two:.2f}"
        elif diff < 0:
            message = f"Cheapest price ${cheapest:.2f} is {abs(diff_percent)}% LOWER than the next two prices averaged ${avg_next_two:.2f}"
        else:
            message = f"Cheapest price ${cheapest:.2f} is the SAME as the next two prices averaged ${avg_next_two:.2f}"

        print(message)
        send_email(message)
    else:
        print("Not enough prices found to compare (need at least 4).")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(e)
        time.sleep(10)

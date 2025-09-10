from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError
import re, os, smtplib, ssl
import time  
from pathlib import Path
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

URL = "https://www.stubhub.com/disclosure-berkeley-tickets-9-27-2025/event/158459048/?quantity=1"
USER_DATA_DIR = str(Path.home() / ".stubhub_playwright_profile")
PRICE_RX = re.compile(r"^\s*\$\s*([\d,]+(?:\.\d{2})?)\s*$")

# ---- Email config ----
SENDER = "adeebautomation01@gmail.com"
PASSWORD = "canwvcbdqdkzrenw"   # Gmail app password
RECEIVER = "adeebbayat@gmail.com"
# ----------------------

# ---- Mongo config ----
uri = "mongodb+srv://adeebbayat:1onXjDE0WCwXfvhY@cluster0.cki8y81.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(uri, server_api=ServerApi('1'))
db = client["testdb"]
collection = db["price"]
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
        val = None
        try:
            price.wait_for(timeout=30000)
            raw = price.inner_text().strip()
            val = extract_price(raw)
        except PWTimeoutError:
            pass
        finally:
            ctx.close()

    finalResult = ""
    # --- MongoDB insert and compare ---
    if val is not None:
        try:
            # ✅ get all old values before insert
            old_values = [doc["value"] for doc in collection.find()]
            old_avg = sum(old_values) / len(old_values) if old_values else None

            examplePrice = {"value": val}
            collection.insert_one(examplePrice)

            if old_avg is not None:
                diff_percent = ((val - old_avg) / old_avg) * 100
                diff_percent = round(diff_percent, 2)

                if val < old_avg:
                    finalResult = f"The new price {val} is {abs(diff_percent)}% LOWER than the old average {round(old_avg,2)}"
                    send_email(finalResult)
                elif val > old_avg:
                    finalResult = f"The new price {val} is {diff_percent}% HIGHER than the old average {round(old_avg,2)}"
                else:
                    finalResult = f"The new price {val} is the SAME as the old average {round(old_avg,2)}"
                print(finalResult)
            else:
                print(f"This is the first price in the collection: ${val}")
        except Exception as e:
            print(e)

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(e)  
        time.sleep(10)  

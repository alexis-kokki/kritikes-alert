import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import time
import hashlib
import json
import os
import argparse

# === Ρυθμίσεις ===
URL = "https://www.kritikes-aggelies.gr/category/katoikies/polh-hrakleiou?type=4&price=200-600&area=50"

# Μπορείς να τα περάσεις και ως ENV vars (π.χ. από GitHub Secrets)
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "alekos.k94@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "fpkwmntyhxzouyil")  # <-- app password
EMAIL_RECEIVER = os.getenv("EMAIL_RECEIVER", "alexis-kokkinakis@hotmail.com")

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SEEN_FILE = "seen_ids.json"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0 Safari/537.36"
)

# === Βοηθητικές για seen ids ===
def load_seen_ids():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return set(data) if isinstance(data, list) else set()
        except Exception:
            return set()
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids), f, ensure_ascii=False)

# === Email ===
def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, [EMAIL_RECEIVER], msg.as_string())
        print("✅ Εστάλη email")
    except Exception as e:
        print(f"❌ Σφάλμα κατά την αποστολή email: {e}")

# === Scrape ===
def get_listings():
    try:
        resp = requests.get(
            URL,
            headers={"User-Agent": USER_AGENT},
            timeout=20,
        )
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        items = []
        for ad in soup.select("article.classi-list-item"):
            title_tag = ad.select_one("h2 a")
            if not title_tag:
                continue
            title = title_tag.get_text(strip=True)
            href = title_tag.get("href", "")
            if not href:
                continue
            link = "https://www.kritikes-aggelies.gr" + href
            items.append((title, link))
        return items

    except Exception as e:
        print(f"❌ Σφάλμα στο get_listings: {e}")
        return []

def make_unique_id(title, link):
    # χρησιμοποιούμε το link (ή συνδυασμό) για μοναδικότητα
    return hashlib.md5(link.encode("utf-8")).hexdigest()

# === ΕΝΑΣ κύκλος ελέγχου (για Actions) ===
def check_for_new_ads_once():
    print("🔍 Έλεγχος για νέες αγγελίες...")
    seen_ids = load_seen_ids()

    listings = get_listings()
    new_ads = []

    for title, link in listings:
        uid = make_unique_id(title, link)
        if uid not in seen_ids:
            seen_ids.add(uid)
            new_ads.append((title, link))

    if new_ads:
        # Στείλε ένα συνοπτικό email (πιο φιλικό για Actions)
        body_lines = [f"{t}\n{l}" for t, l in new_ads]
        body = "Βρέθηκαν νέες αγγελίες:\n\n" + "\n\n".join(body_lines)
        send_email("🔔 Νέες Αγγελίες", body)
        print(f"📬 Εστάλη email για {len(new_ads)} νέες αγγελίες.")
    else:
        print("ℹ️ Καμία νέα αγγελία σε αυτόν τον κύκλο.")

    save_seen_ids(seen_ids)

# === Συνεχής λειτουργία (για τοπική χρήση) ===
def run_forever(interval_seconds=300):
    print(f"🔄 Συνεχόμενος έλεγχος κάθε {interval_seconds} δευτερόλεπτα...")
    while True:
        try:
            check_for_new_ads_once()
        except Exception as e:
            print(f"❌ Σφάλμα κύκλου: {e}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true", help="Τρέξε έναν και μόνο έλεγχο και τερμάτισε")
    parser.add_argument("--interval", type=int, default=300, help="Διάστημα (δευτ.) για συνεχές run")
    args = parser.parse_args()

    if args.once:
        check_for_new_ads_once()
    else:
        run_forever(args.interval)

import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import time
import hashlib
import json
import os

# === Ρυθμίσεις ===
URL = "https://www.kritikes-aggelies.gr/category/katoikies/polh-hrakleiou?type=4&price=200-600&area=50"

EMAIL_SENDER = "alekos.k94@gmail.com"
EMAIL_PASSWORD = "fpkwmntyhxzouyil"
EMAIL_RECEIVER = "alexis-kokkinakis@hotmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SEEN_FILE = "seen_ids.json"

# === Φόρτωση προηγούμενων IDs ===
def load_seen_ids():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w") as f:
        json.dump(list(seen_ids), f)

seen_ids = load_seen_ids()

def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = EMAIL_SENDER
    msg["To"] = EMAIL_RECEIVER

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())
        print("✅ Εστάλη email")
    except Exception as e:
        print(f"❌ Σφάλμα κατά την αποστολή email: {e}")

def get_listings():
    try:
        response = requests.get(URL)
        soup = BeautifulSoup(response.text, "html.parser")

        new_ads = []

        for ad in soup.select("article.classi-list-item"):
            title_tag = ad.select_one("h2 a")
            if not title_tag:
                continue

            title = title_tag.get_text(strip=True)
            link = "https://www.kritikes-aggelies.gr" + title_tag["href"]

            unique_id = hashlib.md5(link.encode()).hexdigest()
            if unique_id not in seen_ids:
                seen_ids.add(unique_id)
                new_ads.append((title, link))

        return new_ads
    except Exception as e:
        print(f"❌ Σφάλμα στο get_listings: {e}")
        return []

def check_for_new_ads():
    print("🔍 Έλεγχος για νέες αγγελίες...")
    new_ads = get_listings()

    for title, link in new_ads:
        message = f"Νέα αγγελία:\n{title}\n{link}"
        send_email("🔔 Νέα Αγγελία", message)
        print(f"📬 Εστάλη: {title}")

    # Αποθηκεύουμε τα νέα IDs
    save_seen_ids(seen_ids)

if __name__ == "__main__":
    while True:
        check_for_new_ads()
        time.sleep(300)  # κάθε 5 λεπτά

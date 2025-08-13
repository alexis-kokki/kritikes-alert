import requests
from bs4 import BeautifulSoup
import smtplib
from email.mime.text import MIMEText
import hashlib
import json
import os

# === ΡΥΘΜΙΣΕΙΣ ===
URL = "https://www.kritikes-aggelies.gr/category/katoikies/polh-hrakleiou?type=4&price=200-600&area=50"

EMAIL_SENDER   = "alekos.k94@gmail.com"
EMAIL_PASSWORD = "fpkwmntyhxzouyil"  # το app password (χωρίς κενά)
EMAIL_RECEIVER = "alexis-kokkinakis@hotmail.com"

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT   = 587

# Βεβαιωνόμαστε ότι το JSON γράφεται στον φάκελο του script (όχι στο cwd του scheduler)
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
SEEN_FILE = os.path.join(BASE_DIR, "seen_ids.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}

# === ΒΟΗΘΗΤΙΚΑ ===
def load_seen_ids():
    try:
        if os.path.exists(SEEN_FILE):
            with open(SEEN_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
    except Exception:
        pass
    return set()

def save_seen_ids(seen_ids):
    with open(SEEN_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen_ids), f)

def send_email(subject, body):
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"]    = EMAIL_SENDER
    msg["To"]      = EMAIL_RECEIVER
    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.sendmail(EMAIL_SENDER, EMAIL_RECEIVER, msg.as_string())

def get_listings(seen_ids):
    resp = requests.get(URL, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    new_ads = []
    for ad in soup.select("article.classi-list-item"):
        a = ad.select_one("h2 a")
        if not a or not a.get("href"):
            continue
        title = a.get_text(strip=True)
        href  = a["href"]
        link  = href if href.startswith("http") else "https://www.kritikes-aggelies.gr" + href

        uid = hashlib.md5(link.encode()).hexdigest()
        if uid not in seen_ids:
            seen_ids.add(uid)
            new_ads.append((title, link))
    return new_ads

def main():
    print("🔍 Έλεγχος για νέες αγγελίες...")
    seen_ids = load_seen_ids()
    new_ads = get_listings(seen_ids)
    for title, link in new_ads:
        send_email("🔔 Νέα Αγγελία", f"Νέα αγγελία:\n{title}\n{link}")
        print(f"📬 Εστάλη: {title}")
    save_seen_ids(seen_ids)

if __name__ == "__main__":
    main()

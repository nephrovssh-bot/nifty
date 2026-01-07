import requests
import pandas as pd
import numpy as np
import time
import datetime

BOT_TOKEN = "8450458054:AAGB9G17AaS3nRvDJvMeOoiKPGsg0Blwqwc"
CHAT_ID = "@Vigneshsnp"

NSE_URL = "https://www.nseindia.com/api/option-chain-indices?symbol=NIFTY"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain"
}

previous_max_pain = None

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg})

def get_option_chain():
    session = requests.Session()
    session.get("https://www.nseindia.com", headers=HEADERS, timeout=10)
    r = session.get(NSE_URL, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.json()["records"]["data"]

def calculate_max_pain(data):
    strikes = sorted(set(d["strikePrice"] for d in data))
    pain_dict = {}

    for strike in strikes:
        total_pain = 0
        for d in data:
            sp = d["strikePrice"]

            ce_oi = d.get("CE", {}).get("openInterest", 0)
            pe_oi = d.get("PE", {}).get("openInterest", 0)

            total_pain += max(sp - strike, 0) * ce_oi
            total_pain += max(strike - sp, 0) * pe_oi

        pain_dict[strike] = total_pain

    return min(pain_dict, key=pain_dict.get)

while True:
    try:
        now = datetime.datetime.now().time()

        # Market hours only
        if now < datetime.time(9, 15) or now > datetime.time(15, 30):
            time.sleep(600)
            continue

        data = get_option_chain()
        max_pain = calculate_max_pain(data)

        if previous_max_pain and max_pain != previous_max_pain:
            diff = max_pain - previous_max_pain
            send_telegram(
                f"📊 NIFTY MAX PAIN CHANGED\n"
                f"Prev: {previous_max_pain}\n"
                f"Now: {max_pain}\n"
                f"Change: {diff:+} pts"
            )

        previous_max_pain = max_pain
        time.sleep(300)  # every 5 minutes

    except Exception as e:
        send_telegram(f"⚠️ Max Pain Bot Error\n{e}")
        time.sleep(300)

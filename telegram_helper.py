import requests
import os

def send_telegram_message(text):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_ids = os.getenv("TELEGRAM_CHAT_ID").split(',')

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in chat_ids:
        try:
            requests.post(url, data={"chat_id": chat_id.strip(), "text": text})
        except Exception as e:
            print(f"[Telegram Error] {e}")

import requests

from . import config

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"


def send_message(text: str) -> None:
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        print("[warn] Telegram credentials not set — skipping send:\n" + text)
        return
    url = TELEGRAM_API.format(token=config.TELEGRAM_BOT_TOKEN)
    resp = requests.post(
        url,
        data={
            "chat_id": config.TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        },
        timeout=10,
    )
    if resp.status_code != 200:
        print(f"[warn] Telegram send failed: {resp.status_code} {resp.text}")

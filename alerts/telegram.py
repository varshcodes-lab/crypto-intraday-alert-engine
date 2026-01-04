import requests

BOT_TOKEN = "8516027487:AAGiJEA4hmGr4taW49KLqcRtcefkPJu4Vws"
CHAT_ID = "7484881480"


def send_telegram_alert(signal):
    if not signal:
        return

    message = f"""
🚨 *Crypto Trade Alert*

*Pair:* {signal['symbol']}
*Trend:* {signal['trend']}
*Confidence:* {signal['score']}/10

📊 *Reasons:*
- {" | ".join(signal['reasons'])}

🎯 *Trade Plan*
Entry: {signal['trade']['entry']}
SL: {signal['trade']['stop_loss']}
Target: {signal['trade']['target']}
RR: {signal['trade']['rr']}
"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    requests.post(url, data=payload)

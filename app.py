from flask import Flask, request
import requests
import os

app = Flask(__name__)  # 👈 ОБЯЗАТЕЛЬНО ВВЕРХУ

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/')
def home():
    return "WORKING"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    data = request.args  # 👈 Bitrix = query params

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')
    stage = data.get('stage', '—')

    text = f"""📊 Новая заявка:

Ребенок: {child}
Родитель: {parent}
Телефон: {phone}
Дата: {date}
"""

    print("🔥 WEBHOOK HIT:", data)  # лог

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

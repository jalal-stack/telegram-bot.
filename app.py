from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("🔥 WEBHOOK HIT")

    # ✅ получаем данные из Bitrix (URL)
    data = request.args

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')

    print("📦 DATA:", data)

    text = f"""📊 Новая заявка:

👶 Ребенок: {child}
👩 Родитель: {parent}
📞 Телефон: {phone}
📍 Адрес: {address}
📅 Дата: {date}
"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return "OK", 200


@app.route('/')
def home():
    return "WORKING"

app.run(host="0.0.0.0", port=10000)

from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


# Только GET в корень
@app.route('/', methods=['GET'])
def home():
    return "WORKING"


# Только настоящий webhook
@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("🔥 WEBHOOK HIT")

   return str(dict(request.values)), 200

    print("RAW DATA:", dict(data))

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')
    stage = data.get('stage', '').lower()

    print("STAGE:", stage)

    if "жалобы" in stage:
        text = f"""🚨 ЖАЛОБЫ!

👶 Ребёнок: {child}
👩 Родитель: {parent}
📞 Телефон: {phone}
"""

    elif "резерв" in stage:
        text = f"""📌 РЕЗЕРВ:

👶 ФИО ребенка: {child}
👩 ФИО родителя: {parent}
🎂 Возраст ребенка: {age}
📍 Адрес: {address}
📞 Телефон: {phone}
"""

    else:
        text = f"""👀 Заявка на Диагностику:

1. ФИО ребенка: {child}
2. ФИО родителя: {parent}
3. Возраст ребенка: {age}
4. Адрес желаемого садика: {address}
5. Телефон номер родителя: {phone}
6. Дата и время пробного дня: {date}
"""

    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    print("TELEGRAM STATUS:", r.status_code)

    return {"ok": True}, 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

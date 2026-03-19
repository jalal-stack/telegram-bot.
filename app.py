from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/')
def home():
    return "WORKING"


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("🔥 WEBHOOK HIT")

    data = request.args

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')
    complaint = data.get('complaint', '—')
    stage = data.get('stage', '').lower()

    # 🔥 разные тексты
   if any(word in stage for word in ["жалоб", "жалоба", "complaint"]):
        text = f"""🚨 ЖАЛОБА!

👶 Ребёнок: {child}
👩 Родитель: {parent}
📞 Телефон: {phone}

📝 Жалоба:
{complaint}
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

    # 📲 отправка в Telegram
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

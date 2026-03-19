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
    data = request.args

parent = data.get('parent', '—')
child = data.get('child', '—')
age = data.get('age', '—')
phone = data.get('phone', '—')
address = data.get('address', '—')
date = data.get('date', '—')
email = data.get('email', '—')
stage = data.get('stage', '').lower()

# 🔥 разные тексты
if "жалоб" in stage:
    text = f"""🚨 ЖАЛОБА!

👩 Родитель: {parent}
👶 Ребенок: {child}
📞 Телефон: {phone}
📝 Комментарий: {address}
"""

elif "резерв" in stage:
    text = f"""📌 РЕЗЕРВ:

👩 Родитель: {parent}
📞 Телефон: {phone}
📅 Дата: {date}
"""

else:
    text = f"""👀 Заявка на Диагностику:

1. ФИО ребенка: {child}
2. ФИО родителя: {parent}
3. Возраст ребенка: {age}
4. Адрес желаемого садика: {address}
5. Телефон номер родителя: {phone}
6. Дата и время Диагностики: {date}
7. Почта родителя: {email}
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

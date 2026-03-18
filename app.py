from flask import Flask, request
import requests
import os

app = Flask(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json

    parent = data.get('PARENT', '—')
    child = data.get('CHILD', '—')
    age = data.get('AGE', '—')
    phone = data.get('PHONE', '—')
    address = data.get('ADDRESS', '—')
    date = data.get('DATE', '—')
    stage = data.get('STAGE', '—')

    # 🎯 Разные тексты по стадиям
    if "Жалоба" in stage:
        text = f"""🚨 Новая жалоба!

Родитель: {parent}
Ребенок: {child}
Телефон: {phone}
Комментарий: {address}
"""
    elif "Резерв" in stage:
        text = f"""📌 Резерв:

Родитель: {parent}
Телефон: {phone}
Дата: {date}
"""
    else:
        text = f"""📊 Запись на Диагностику Навыков:

ФИО ребенка: {child}
ФИО родителя: {parent}
Возраст ребенка: {age}
Адрес садика: {address}
Телефон: {phone}
Дата: {date}
"""

    # 📲 Отправка в Telegram
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}

@app.route('/')
def home():
    return "WORKING"

app.run(host="0.0.0.0", port=10000)

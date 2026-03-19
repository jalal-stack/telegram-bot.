@app.route('/webhook', methods=['POST'])
def webhook():
    print("WEBHOOK HIT")

    data = request.args

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')

    text = f"""📊 Диагностика Навыков:

Ребенок: {child}
Родитель: {parent}
Возраст: {age}
Телефон: {phone}
Адрес: {address}
Дата: {date}
"""

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}

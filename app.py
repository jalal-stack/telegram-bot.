@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    data = request.args

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

    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    return {"ok": True}
   

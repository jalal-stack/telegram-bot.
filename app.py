from flask import Flask, request
import requests

app = Flask(__name__)

# ⚠️ ЗАМЕНИТЕ на свой новый токен!
TELEGRAM_TOKEN = "8675300847:AAHClwA7GEU04l1YbBslgoimFp_2QVPQGRI"
CHAT_ID = "1003865656272"


@app.route('/', methods=['GET'])
def home():
    return "WORKING"


@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    print("🔥 WEBHOOK HIT")

    data = request.values
    print("DATA:", dict(data))

    # 🔹 Получаем данные из Bitrix
    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date')
    complaint = data.get('complaint')

    # ❌ защита от пустых
    if child == '—' and parent == '—':
        print("EMPTY → SKIP")
        return {"ignored": True}, 200

    # 🔥 ЛОГИКА (приоритет по данным)
    if complaint:
        text = f"""🚨 ЖАЛОБА!

👶 {child}
👩 {parent}
📞 {phone}
📝 {complaint}
"""

    elif date:
        text = f"""👀 ДИАГНОСТИКА:

👶 {child}
👩 {parent}
🎂 {age}
📍 {address}
📞 {phone}
📅 {date}
"""

    else:
        text = f"""📌 РЕЗЕРВ:

👶 {child}
👩 {parent}
🎂 {age}
📍 {address}
📞 {phone}
"""

    # 📲 отправка в Telegram
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        data={
            "chat_id": CHAT_ID,
            "text": text
        }
    )

    print("TELEGRAM:", r.status_code, r.text)

    return {"ok": True}, 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

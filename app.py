from flask import Flask, request
import requests

app = Flask(__name__)

# ВРЕМЕННО напрямую (для теста)
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

    parent = data.get('parent', '—')
    child = data.get('child', '—')
    age = data.get('age', '—')
    phone = data.get('phone', '—')
    address = data.get('address', '—')
    date = data.get('date', '—')
    stage = data.get('stage', '').lower()

    if not child or child == '—':
        print("EMPTY → SKIP")
        return {"ignored": True}, 200

    text = f"""👀 Заявка:

👶 {child}
👩 {parent}
📞 {phone}
"""

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

import json
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/api/webhook", methods=["POST"])
def webhook():
    print("🔥 Webhook ricevuto!")

    payload = request.data.decode("utf-8")
    event = json.loads(payload)

    # Debug
    print("📨 Evento ricevuto:", event)

    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run()
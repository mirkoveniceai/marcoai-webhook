import json
import os
import stripe
import logging
import pymongo
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import requests

app = FastAPI()

# ---------------------------------------------------
#  CONFIG
# ---------------------------------------------------
STRIPE_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
MONGO_URI = os.getenv("MONGO_URI")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ADMIN_TELEGRAM_ID = os.getenv("ADMIN_TELEGRAM_ID", "738446337")

# ---------------------------------------------------
#  MONGO
# ---------------------------------------------------
client = pymongo.MongoClient(MONGO_URI)
db = client["marcoai"]
users = db["user_profiles"]

# ---------------------------------------------------
#  STRIPE
# ---------------------------------------------------
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


def send_telegram(chat_id: str, text: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text})
    except Exception as e:
        logging.error(f"Errore Telegram: {e}")


# ---------------------------------------------------
#  WEBHOOK HANDLER
# ---------------------------------------------------
@app.post("/api/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Verifica della firma Stripe
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_SECRET
        )
    except Exception as e:
        logging.error(f"⚠️ Errore firma STRIPE: {e}")
        raise HTTPException(status_code=400, detail="Invalid signature")

    event_type = event["type"]

    # ---------------------------------------------------
    # 1) Pagamento completato → attiva PREMIUM
    # ---------------------------------------------------
    if event_type == "checkout.session.completed":
        session = event["data"]["object"]

        # Metadata inviato da Stripe Checkout
        user_id = session["metadata"].get("telegram_id")
        product_id = session["metadata"].get("product")

        # ---------------------------------------------------
        # Aggiorna profilo MongoDB
        # ---------------------------------------------------
        users.update_one(
            {"telegram_id": str(user_id)},
            {
                "$set": {
                    "premium": True,
                    "premium_since": datetime.utcnow(),
                    "premium_product": product_id,
                }
            },
            upsert=True
        )

        # ---------------------------------------------------
        # Messaggi
        # ---------------------------------------------------
        send_telegram(
            user_id,
            "✨ *Complimenti!* Hai attivato MarcoAI Premium.\n"
            "Da questo momento hai accesso a tutte le funzionalità avanzate:"
            "\n\n• Percorsi Premium\n• VCNet Access\n• FoodShield Pro\n"
            "• Consigli personalizzati\n• Voice Mode\n\nBenvenuto nella versione PRO di Venezia."
        )

        send_telegram(
            ADMIN_TELEGRAM_ID,
            f"🔔 NUOVO UTENTE PREMIUM\nID: {user_id}\nProdotto: {product_id}"
        )

        return JSONResponse({"status": "premium_activated"})

    # ---------------------------------------------------
    # 2) Subscription renew
    # ---------------------------------------------------
    if event_type == "invoice.payment_succeeded":
        invoice = event["data"]["object"]
        user_id = invoice["metadata"].get("telegram_id", None)

        if user_id:
            send_telegram(user_id, "🔄 Il tuo abbonamento Premium è stato rinnovato!")

    return JSONResponse({"status": "ok"})
# Commit per redeploy
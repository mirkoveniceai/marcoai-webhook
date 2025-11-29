import os
import stripe
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from pymongo import MongoClient

# -------------------------------------------------------
# CONFIG
# -------------------------------------------------------
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI")

app = FastAPI()
stripe.api_key = STRIPE_SECRET

mongo = MongoClient(MONGO_URI)
db = mongo["marcoai"]
premium_users = db["premium_users"]

# -------------------------------------------------------
# SEND TELEGRAM MESSAGE
# -------------------------------------------------------
import requests

def send_telegram_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    })

# -------------------------------------------------------
# WEBHOOK ENDPOINT
# -------------------------------------------------------
@app.post("/api/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # -----------------------------
    # EVENTO PAGAMENTO COMPLETATO
    # -----------------------------
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        telegram_id = session["metadata"].get("telegram_id")

        if telegram_id:
            premium_users.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"premium": True}},
                upsert=True
            )

            send_telegram_message(
    telegram_id,
    "🔥 <b>Benvenuto in FOOD TRAP PREMIUM!</b>\n\n"
    "Da questo momento hai attivato il sistema anti-trappola più intelligente di Venezia.\n\n"
    "<b>Cosa puoi fare ora:</b>\n"
    "• Analisi completa di qualsiasi ristorante\n"
    "• Verifica immediata trappola / non trappola\n"
    "• Rating reale da database + AI\n"
    "• Alternative consigliate vicino a te\n"
    "• Protezione totale durante la vacanza\n\n"
    "Scrivi il nome di un ristorante e ti proteggo subito."
)

    return JSONResponse({"status": "ok"})
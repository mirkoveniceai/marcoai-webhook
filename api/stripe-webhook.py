import json
import os
import stripe
from pymongo import MongoClient

# === Stripe Setup ===
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
endpoint_secret = os.environ.get("STRIPE_WEBHOOK_SECRET")

# === MongoDB Setup ===
MONGO_URL = os.environ.get("MONGO_URL")
mongo_client = MongoClient(MONGO_URL)
db = mongo_client["marcoai"]
users = db["user_profiles"]


def handler(request):
    # 1) Leggiamo il body grezzo (Stripe lo richiede per la signature)
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )
    except Exception as e:
        return {
            "statusCode": 400,
            "body": f"Webhook signature verification failed: {str(e)}"
        }

    # =========================================================
    # 2) EVENTI DA GESTIRE
    # =========================================================

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # L'utente Telegram ID lo passiamo nei metadata
        telegram_id = session["metadata"].get("telegram_id")

        if telegram_id:
            users.update_one(
                {"telegram_id": telegram_id},
                {"$set": {"is_premium": True}},
                upsert=True
            )
            print(f"UTENTE {telegram_id} ATTIVATO PREMIUM!")

    # Stripe richiede SEMPRE una risposta 200
    return {"statusCode": 200, "body": "OK"}
# api/webhook_activator.py
import json
import os
import stripe
from pymongo import MongoClient
from datetime import datetime, timedelta

# -------------------------------------------------------------
# CONFIGURAZIONI STRIPE (DA METTERE IN VERCEL ENV)
# -------------------------------------------------------------
STRIPE_SECRET = os.environ.get("STRIPE_SECRET")
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")

stripe.api_key = STRIPE_SECRET

# -------------------------------------------------------------
# CONFIG MONGO (DA METTERE IN VERCEL ENV)
# -------------------------------------------------------------
MONGO_URI = os.environ.get("MONGO_URI")

def activate_user_in_db(user_id: str):
    """Attiva l'utente Premium nel DB."""
    if not MONGO_URI:
        print("ERRORE: MONGO_URI non configurato")
        return False

    try:
        client = MongoClient(MONGO_URI)
        db = client.MarcoAIDB
        users = db.users

        expiry_date = datetime.utcnow() + timedelta(days=30)

        result = users.update_one(
            {"_id": int(user_id)},
            {
                "$set": {
                    "is_premium": True,
                    "premium_expiry": expiry_date
                }
            },
            upsert=True
        )

        client.close()
        print(f"OK: Utente {user_id} attivato premium.")
        return True
    except Exception as e:
        print(f"ERRORE MONGO: {e}")
        return False


# -------------------------------------------------------------
# HANDLER HTTP VERCEL
# -------------------------------------------------------------
def handler(request):
    """Gestione Webhook Stripe."""
    try:
        payload = request.body
        sig = request.headers.get("Stripe-Signature")

        # Verifica firma
        event = stripe.Webhook.construct_event(
            payload, sig, STRIPE_WEBHOOK_SECRET
        )

        print("STRIPE EVENT:", event["type"])

        # SOLO eventi di pagamento riuscito
        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]

            # Recupera il Telegram user_id dal metadata
            user_id = session.get("metadata", {}).get("telegram_id")

            if user_id:
                activate_user_in_db(user_id)

        return {
            "statusCode": 200,
            "body": json.dumps({"received": True})
        }

    except Exception as e:
        print("ERRORE HANDLER:", e)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }


# Compatibilità con Vercel
def main(request):
    return handler(request)
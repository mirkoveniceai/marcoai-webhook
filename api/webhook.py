import os
import stripe
from fastapi import FastAPI, Request, HTTPException
from pymongo import MongoClient

app = FastAPI()

# ====== ENV ======
STRIPE_SECRET = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
MONGO_URI = os.getenv("MONGO_URI")

stripe.api_key = STRIPE_SECRET

# ====== MONGO ======
mongo = MongoClient(MONGO_URI)
db = mongo["marcoai"]
users = db["premium_users"]


@app.post("/webhook")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    # ====== EVENTI STRIPE CHE CI INTERESSANO ======
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        telegram_id = session["metadata"].get("telegram_id")

        if telegram_id:
            users.update_one(
                {"telegram_id": telegram_id},
                {"$set": {
                    "premium": True,
                    "activated_at": session["created"],
                    "plan": "premium",
                }},
                upsert=True
            )
            print(f"PREMIUM ATTIVATO per {telegram_id}")

    return {"status": "ok"}
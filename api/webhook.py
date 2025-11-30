# api/webhook.py
# Webhook Stripe minimale per Vercel (Python)
# - Risponde 200 a GET (così non vedi più 404 nel browser)
# - Gestisce POST da Stripe e manda un messaggio a Telegram (admin)

from http.server import BaseHTTPRequestHandler
import os
import json
import stripe
import requests

# Chiavi da ENV su Vercel
STRIPE_WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
ADMIN_CHAT_ID = os.environ.get("ADMIN_CHAT_ID")  # tuo chat_id Telegram per le notifiche

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")


def send_telegram_message(text: str):
    """Manda un messaggio al tuo Telegram (admin) per conferma pagamento."""
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": ADMIN_CHAT_ID,
        "text": text,
        "parse_mode": "Markdown",
    }
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception:
        pass


class handler(BaseHTTPRequestHandler):
    def _send_json(self, status_code: int, data: dict):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send_json(200, {"status": "ok", "message": "MarcoAI webhook attivo"})

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(content_length)
        sig_header = self.headers.get("Stripe-Signature", "")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=STRIPE_WEBHOOK_SECRET,
            )
        except Exception as e:
            self._send_json(400, {"status": "error", "message": str(e)})
            return

        if event.get("type") == "checkout.session.completed":
            session = event["data"]["object"]

            amount_total = session.get("amount_total")
            currency = session.get("currency", "").upper()
            customer_email = session.get("customer_details", {}).get("email", "n/d")

            euro = None
            if amount_total is not None:
                euro = amount_total / 100.0

            text_lines = [
                "💳 *Nuovo pagamento ricevuto*",
                "",
                f"- Email: `{customer_email}`",
                f"- Importo: {euro} {currency}" if euro is not None else f"- Valuta: {currency}",
                "",
                "Fonte: Stripe → Webhook Vercel → MarcoAI",
            ]
            send_telegram_message("\n".join(text_lines))

        self._send_json(200, {"status": "success"})
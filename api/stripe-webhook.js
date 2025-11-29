import Stripe from "stripe";
import { buffer } from "micro";

export const config = {
  api: {
    bodyParser: false,
  },
};

const stripe = new Stripe(process.env.STRIPE_SECRET_KEY);

export default async function handler(req, res) {
  if (req.method !== "POST") {
    return res.status(405).send("Method Not Allowed");
  }

  let event;
  const buf = await buffer(req);
  const sig = req.headers["stripe-signature"];

  try {
    event = stripe.webhooks.constructEvent(
      buf,
      sig,
      process.env.STRIPE_WEBHOOK_SECRET
    );
  } catch (err) {
    console.error("❌ Webhook signature verification failed:", err.message);
    return res.status(400).send(`Webhook Error: ${err.message}`);
  }

  console.log("Evento Stripe ricevuto:", event.type);

  // Esempio gestione evento di successo
  if (event.type === "checkout.session.completed") {
    console.log("Pagamento completato:", event.data.object.id);
  }

  res.status(200).send("OK");
}
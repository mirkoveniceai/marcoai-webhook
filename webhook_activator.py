import os
from pymongo import MongoClient

# --- CONFIGURAZIONE CRITICA MongoDB ---
# DEVI CONFIGURARE LA VARIABILE D'AMBIENTE "MONGO_URI" SU VERCEL!
# (Es. mongodb+srv://<utente>:<password>@cluster0.mongodb.net/MarcoAIDB?retryWrites=true&w=majority)
MONGO_URI = os.environ.get("MONGO_URI")

def activate_user_in_db(user_id: str):
    """
    ATTIVAZIONE FINALE: Connette a MongoDB e imposta lo stato Premium.
    Questa funzione va usata nel tuo webhook_handler.py al posto dello stub.
    """
    if not MONGO_URI:
        print("ERRORE: Variabile MONGO_URI non configurata.")
        return False
        
    try:
        client = MongoClient(MONGO_URI)
        # Sostituisci 'MarcoAIDB' con il nome del tuo database effettivo
        db = client.MarcoAIDB 
        
        # Sostituisci 'users' con la tua collezione che contiene gli stati utente
        users_collection = db.users 
        
        # Calcola la data di scadenza (30 giorni da adesso)
        from datetime import datetime, timedelta
        expiry_date = datetime.utcnow() + timedelta(days=30)
        
        # Aggiorna o Inserisci il profilo utente
        result = users_collection.update_one(
            {"_id": int(user_id)}, # Assumendo che l'ID Utente Telegram sia un INT
            {"$set": {
                "is_premium": True,
                "premium_expiry": expiry_date
            }},
            upsert=True # Inserisce se non esiste
        )
        
        client.close()
        
        if result.modified_count > 0 or result.upserted_id is not None:
            print(f"SUCCESSO DB: Utente {user_id} attivato Premium fino a {expiry_date}.")
            return True
        else:
            print(f"WARNING DB: Nessuna modifica per utente {user_id}. Stato non chiaro.")
            return True # Assumiamo successo per non bloccare Stripe con un errore
            
    except Exception as e:
        print(f"ERRORE CRITICO MONGO DB: Impossibile connettersi o scrivere: {e}")
        return False # Fallimento nell'attivazione

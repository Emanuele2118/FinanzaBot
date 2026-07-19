import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import ApplicationBuilder, CommandHandler
from datetime import datetime

# --- CONFIGURAZIONE VIA VARIABILI D'AMBIENTE ---
CREDS_JSON = os.environ.get('CREDENTIALS_JSON')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SHEET_NAME = 'Il Mio Futuro Finanziario'

# Connessione a Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).worksheet('Flussi di Cassa')  # Specifica la scheda corretta

# Funzione per registrare una spesa
async def spesa(update, context):
    try:
        # Prende l'importo scritto dopo il comando (es. /spesa 10)
        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        
        # Ottiene la data odierna nel formato GG/MM/AAAA o AAAA-MM-DD come usi tu
        data_odierna = datetime.now().strftime('%d/%m/%Y')
        
        # Struttura delle colonne nel tuo foglio:
        # [Data, Categoria, Prodotto, Prezzo €, Entrata, Uscita]
        # Mettiamo Entrata a 0 e Uscita pari all'importo
        nuova_riga = [
            data_odierna,  # Colonna A: Data
            'Spesa',       # Colonna B: Categoria
            'Telegram',    # Colonna C: Prodotto
            importo,       # Colonna D: Prezzo €
            0,             # Colonna E: Entrata
            importo        # Colonna F: Uscita
        ]
        
        sheet.append_row(nuova_riga)
        await update.message.reply_text(f"✅ Spesa di {importo}€ registrata correttamente nel foglio!")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nella formattazione o scrittura: {e}")

# Avvio del Bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("spesa", spesa))
    
    print("🤖 Bot avviato su Railway con struttura corretta...")
    app.run_polling()

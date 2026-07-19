import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import ApplicationBuilder, CommandHandler

# --- CONFIGURAZIONE VIA VARIABILI D'AMBIENTE ---
# Queste variabili le imposteremo nel pannello di controllo di Railway
CREDS_JSON = os.environ.get('CREDENTIALS_JSON')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SHEET_NAME = 'Il Mio Futuro Finanziario'

# Connessione a Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
sheet = client.open(SHEET_NAME).sheet1

# Funzione per registrare una spesa
async def spesa(update, context):
    try:
        importo = context.args[0]
        # Inserisce la data odierna e l'importo
        sheet.append_row(['2026-07-19', importo, 'Spesa'])
        await update.message.reply_text(f"✅ Spesa di {importo}€ registrata su Railway!")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {e}")

# Avvio del Bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("spesa", spesa))
    
    print("🤖 Bot avviato su Railway...")
    app.run_polling()

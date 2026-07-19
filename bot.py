import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import ApplicationBuilder, CommandHandler
from datetime import datetime

# --- CONFIGURAZIONE ---
CREDS_JSON = os.environ.get('CREDENTIALS_JSON')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SHEET_NAME = 'Il Mio Futuro Finanziario'

# Connessione
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)
# Apriamo il foglio e forziamo la tab "Flussi di Cassa"
sh = client.open(SHEET_NAME)
sheet = sh.worksheet('Flussi di Cassa') 

async def spesa(update, context):
    try:
        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        data = datetime.now().strftime('%d/%m/%Y')
        
        # Scriviamo esattamente nelle colonne A, B, C, D, E, F
        # [Data, Categoria, Prodotto, Prezzo, Entrata, Uscita]
        row = [data, 'Spesa', 'Telegram', importo, 0, importo]
        
        sheet.append_row(row)
        await update.message.reply_text(f"✅ Registrato: {importo}€ in 'Flussi di Cassa'")
    except Exception as e:
        await update.message.reply_text(f"Errore: {str(e)}")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("spesa", spesa))
    print("🤖 Bot avviato su Railway...")
    app.run_polling()

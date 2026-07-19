import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from telegram.ext import ApplicationBuilder, CommandHandler
from datetime import datetime

# --- CONFIGURAZIONE ---
# Assicurati che le variabili siano impostate su Railway
CREDS_JSON = os.environ.get('CREDENTIALS_JSON')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SHEET_NAME = 'Il Mio Futuro Finanziario'
WORKSHEET_NAME = 'Flussi di Cassa'

# Connessione a Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

# Apertura foglio e scheda specifica
sh = client.open(SHEET_NAME)
sheet = sh.worksheet(WORKSHEET_NAME)

async def spesa(update, context):
    try:
        if not context.args:
            await update.message.reply_text("Uso: /spesa [importo]")
            return

        # Prepara i dati
        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        data = datetime.now().strftime('%d/%m/%Y')
        
        # Struttura riga: [Data, Categoria, Prodotto, Prezzo €, Entrata, Uscita]
        # La categoria 'Spesa' deve corrispondere esattamente a quella nella tua tendina
        row = [data, 'Spesa', 'Telegram', importo, 0, importo]
        
        # Aggiunge la riga in fondo al foglio
        sheet.append_row(row)
        
        await update.message.reply_text(f"✅ Registrato: {importo}€ nella categoria 'Spesa'.")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore durante la scrittura: {str(e)}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not CREDS_JSON:
        print("Errore: Variabili d'ambiente non trovate!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("spesa", spesa))
        print("🤖 Bot avviato correttamente!")
        app.run_polling()

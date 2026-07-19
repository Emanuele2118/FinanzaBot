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
WORKSHEET_NAME = 'Flussi di Cassa'

# Connessione a Google Sheets
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
creds_dict = json.loads(CREDS_JSON)
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(creds)

sh = client.open(SHEET_NAME)
sheet = sh.worksheet(WORKSHEET_NAME)

async def spesa(update, context):
    try:
        if not context.args:
            await update.message.reply_text("Uso: /spesa [importo]")
            return

        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        data = datetime.now().strftime('%d/%m/%Y')
        
        # Legge tutti i valori della colonna A (Data) per trovare la prima cella vuota
        colonna_date = sheet.col_values(1)
        
        # Trova la prima riga libera partendo dall'alto (saltando l'intestazione riga 1)
        # Se ci sono 17 righe piene, la prima libera sarà la 18.
        prossima_riga = len(colonna_date) + 1
        
        # Dati da inserire nelle colonne A, B, C, D, E, F
        row = [data, 'Spesa', 'Telegram', importo, 0, importo]
        
        # Aggiorna esattamente la riga vuota trovata, preservando colori e formattazione
        sheet.update(f'A{prossima_riga}:F{prossima_riga}', [row])
        
        await update.message.reply_text(f"✅ Spesa di {importo}€ inserita nella tua riga colorata (Riga {prossima_riga})!")
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

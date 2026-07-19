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
        
        # Legge tutti i valori della colonna C (Prodotto)
        colonna_prodotti = sheet.col_values(3)
        
        # Cerca la prima riga dove la colonna C è vuota (partendo dall'alto)
        prossima_riga = 2
        while prossima_riga <= len(colonna_prodotti):
            if colonna_prodotti[prossima_riga - 1].strip() == "":
                break
            prossima_riga += 1
            
        # Dati da scrivere a partire dalla colonna B alla F
        # (La colonna A viene saltata per lasciare spazio alla tua formula automatica)
        dati_riga = [
            'Spesa',    # Colonna B: Categoria
            'Telegram', # Colonna C: Prodotto
            importo,    # Colonna D: Prezzo €
            0,          # Colonna E: Entrata
            importo     # Colonna F: Uscita
        ]
        
        # Aggiorna esattamente le colonne da B a F della riga libera trovata
        sheet.update(f'B{prossima_riga}:F{prossima_riga}', [dati_riga])
        
        await update.message.reply_text(f"✅ Spesa di {importo}€ registrata correttamente alla riga {prossima_riga}!")
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

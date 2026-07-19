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
            await update.message.reply_text("Uso corretto: /spesa [importo] [nome prodotto]\nEsempio: /spesa 10 Caffè")
            return

        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        
        if len(context.args) > 1:
            prodotto = " ".join(context.args[1:])
        else:
            prodotto = "Telegram"

        data = datetime.now().strftime('%d/%m/%Y')
        
        # Legge la colonna C (Prodotto) per trovare la prima riga libera partendo dall'alto
        colonna_prodotti = sheet.col_values(3)
        prossima_riga = 2
        while prossima_riga <= len(colonna_prodotti):
            if colonna_prodotti[prossima_riga - 1].strip() == "":
                break
            prossima_riga += 1
            
        # Prepara la riga da inserire
        row = [data, 'Spesa', prodotto, importo]
        
        # Scrive esattamente nella prima riga libera trovata in alto (dalla A alla D)
        sheet.update(f'A{prossima_riga}:D{prossima_riga}', [row])
        
        await update.message.reply_text(f"✅ Registrato: {importo}€ ({prodotto}) alla riga {prossima_riga}!")
    except ValueError:
        await update.message.reply_text("❌ L'importo inserito non è valido. Usa i numeri (es. /spesa 12.50)")
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

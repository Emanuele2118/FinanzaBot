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
sh = client.open(SHEET_NAME)

# Schede
sheet_flussi = sh.worksheet('Flussi di Cassa')
sheet_dashboard = sh.worksheet('Dashboard')

async def registra(update, context, categoria):
    try:
        if not context.args:
            await update.message.reply_text(f"Uso: /{categoria.lower()} [importo] [prodotto]\nEsempio: /{categoria.lower()} 15 Maglia")
            return
        
        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        
        if len(context.args) > 1:
            prodotto = " ".join(context.args[1:])
        else:
            prodotto = "Telegram"

        data = datetime.now().strftime('%d/%m/%Y')
        
        # Cerca la prima riga libera nella colonna C di 'Flussi di Cassa'
        colonna_prodotti = sheet_flussi.col_values(3)
        prossima_riga = 2
        while prossima_riga <= len(colonna_prodotti):
            if colonna_prodotti[prossima_riga - 1].strip() == "":
                break
            prossima_riga += 1
            
        row = [data, categoria, prodotto, importo]
        sheet_flussi.update(f'A{prossima_riga}:D{prossima_riga}', [row])
        
        await update.message.reply_text(f"✅ Registrato {categoria}: {importo}€ ({prodotto}) alla riga {prossima_riga}!")
    except ValueError:
        await update.message.reply_text("❌ L'importo non è valido. Usa i numeri (es. 12.50)")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def spesa(update, context): 
    await registra(update, context, "Spesa")

async def vendita(update, context): 
    await registra(update, context, "Vendita")

async def bilancio(update, context):
    try:
        # Legge le celle forzando il recupero del valore calcolato dalle formule
        tot_guadagno = sheet_dashboard.acell('B4', value_render_option='FORMATTED_VALUE').value or "0"
        tot_uscite = sheet_dashboard.acell('B7', value_render_option='FORMATTED_VALUE').value or "0"
        saldo_finale = sheet_dashboard.acell('B10', value_render_option='FORMATTED_VALUE').value or "0"
        
        # Funzione per pulire il valore e trasformarlo in numero per il calcolo del 30%
        def pulisci_numero(valore):
            if not valore:
                return 0.0
            val_str = str(valore).replace('€', '').replace(' ', '').replace(',', '.')
            try:
                return float(val_str)
            except ValueError:
                return 0.0

        saldo_num = pulisci_numero(saldo_finale)
        sfizi = saldo_num * 0.30

        await update.message.reply_text(
            f"📊 **Dashboard Finanziaria**\n\n"
            f"🟢 Totale Guadagno: {tot_guadagno}€\n"
            f"🔴 Totale Uscite: {tot_uscite}€\n"
            f"💰 Saldo Finale: {saldo_finale}€\n\n"
            f"🎯 Budget per sfizi (30%): {sfizi:.2f}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nella lettura della Dashboard: {str(e)}")

if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not CREDS_JSON:
        print("Errore: Variabili d'ambiente non trovate!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("spesa", spesa))
        app.add_handler(CommandHandler("vendita", vendita))
        app.add_handler(CommandHandler("bilancio", bilancio))
        print("🤖 Bot avviato correttamente!")
        app.run_polling()

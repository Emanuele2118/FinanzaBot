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

sheet_flussi = sh.worksheet('Flussi di Cassa')

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
        
        # Cerca la prima riga libera basandosi sulla colonna C (Prodotti)
        colonna_prodotti = sheet_flussi.col_values(3)
        prossima_riga = 2
        while prossima_riga <= len(colonna_prodotti):
            if colonna_prodotti[prossima_riga - 1].strip() == "":
                break
            prossima_riga += 1
            
        # Scrive Data (A), Categoria (B), Prodotto (C) e Prezzo (D)
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
        righe = sheet_flussi.get_all_values()
        tot_guadagno = 0.0
        tot_uscite = 0.0
        
        print("\n--- DEBUG BILANCIO ---")
        for r in righe[1:]:
            if len(r) >= 4:
                # Stampiamo quello che legge per capire cosa c'è nelle celle B e D
                cat = r[1].strip()
                val = r[3].strip()
                print(f"Colonna B (Cat): '{cat}' | Colonna D (Val): '{val}'")
                
                if val != "":
                    try:
                        importo = float(val.replace(',', '.'))
                        # Controlliamo sia minuscolo che maiuscolo senza problemi
                        cat_lower = cat.lower()
                        if "vendita" in cat_lower:
                            tot_guadagno += importo
                        elif "spesa" in cat_lower:
                            tot_uscite += importo
                    except ValueError:
                        continue
                        
        print(f"Totali calcolati -> Guadagni: {tot_guadagno}, Uscite: {tot_uscite}")
        print("----------------------\n")

        saldo_finale = tot_guadagno - tot_uscite
        sfizi = saldo_finale * 0.30

        await update.message.reply_text(
            f"📊 **Bilancio Snc**\n\n"
            f"🟢 Totale Guadagno: {tot_guadagno:.2f}€\n"
            f"🔴 Totale Uscite: {tot_uscite:.2f}€\n"
            f"💰 Saldo Finale: {saldo_finale:.2f}€\n\n"
            f"🎯 Budget per sfizi (30%): {sfizi:.2f}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nel calcolo del bilancio: {str(e)}")

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

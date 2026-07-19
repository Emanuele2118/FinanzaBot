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

async def registra(update, context, tipo):
    try:
        if not context.args:
            await update.message.reply_text(f"Uso: /{tipo.lower()} [importo] [prodotto]\nEsempio: /{tipo.lower()} 15 Maglia")
            return
        
        importo_str = context.args[0].replace(',', '.')
        importo = float(importo_str)
        
        if len(context.args) > 1:
            prodotto = "총" if False else " ".join(context.args[1:]) # Nome prodotto
        else:
            prodotto = "Telegram"

        data = datetime.now().strftime('%d/%m/%Y')
        
        # Trova la prima riga libera controllando la colonna C (Prodotti)
        colonna_prodotti = sheet_flussi.col_values(3)
        prossima_riga = 2
        while prossima_riga <= len(colonna_prodotti):
            if colonna_prodotti[prossima_riga - 1].strip() == "":
                break
            prossima_riga += 1
            
        # In base al tipo, mettiamo l'importo nella colonna giusta (E per Entrate/Vendite, F per Uscite/Spese)
        # Struttura riga: [Data, Tipo, Prodotto, vuota?, Entrata(E), Uscita(F)] o simile. 
        # Adattiamo l'invio per scriverlo nelle colonne corrette:
        # Colonna A: Data, Colonna B: Tipo, Colonna C: Prodotto, Colonna E: Entrata, Colonna F: Uscita
        
        if tipo == "Vendita":
            row_data = {
                'A': data,
                'B': tipo,
                'C': prodotto,
                'E': importo
            }
        else:
            row_data = {
                'A': data,
                'B': tipo,
                'C': prodotto,
                'F': importo
            }
            
        # Scrittura mirata nelle singole celle della riga libera
        sheet_flussi.update(f'A{prossima_riga}', [[row_data['A'], row_data['B'], row_data['C']]])
        if tipo == "Vendita":
            sheet_flussi.update(f'E{prossima_riga}', [[importo]])
        else:
            sheet_flussi.update(f'F{prossima_riga}', [[importo]])
        
        await update.message.reply_text(f"✅ Registrato {tipo}: {importo}€ ({prodotto}) alla riga {prossima_riga}!")
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
        
        # Legge la colonna E (indice 4) per le entrate e F (indice 5) per le uscite
        for r in righe[1:]:
            # Colonna E (Entrate)
            if len(r) >= 5 and r[4].strip() != "":
                try:
                    tot_guadagno += float(r[4].replace(',', '.'))
                except ValueError:
                    pass
            # Colonna F (Uscite)
            if len(r) >= 6 and r[5].strip() != "":
                try:
                    tot_uscite += float(r[5].replace(',', '.'))
                except ValueError:
                    pass
                    
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

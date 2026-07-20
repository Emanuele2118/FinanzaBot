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
# Apriamo anche il foglio della Dashboard per leggere i totali riassuntivi
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
        # Legge direttamente i valori formattati e calcolati dal foglio Dashboard
        tot_guadagno = sheet_dashboard.acell('B4').value
        tot_uscite = sheet_dashboard.acell('B6').value
        saldo_finale = sheet_dashboard.acell('B10').value
        
        tot_vendite = sheet_dashboard.acell('D4').value
        tot_investimenti = sheet_dashboard.acell('D6').value
        tot_spese = sheet_dashboard.acell('D10').value
        
        tasso_efficienza = sheet_dashboard.acell('H4').value
        guadagno_netto = sheet_dashboard.acell('H7').value
        
        v_settimana = sheet_dashboard.acell('B14').value
        s_settimana = sheet_dashboard.acell('D14').value
        i_settimana = sheet_dashboard.acell('F14').value
        
        v_mese = sheet_dashboard.acell('B16').value
        s_mese = sheet_dashboard.acell('D16').value
        i_mese = sheet_dashboard.acell('F16').value

        await update.message.reply_text(
            f"📊 **Dashboard & Risultato Economico**\n\n"
            f"🟢 **Totale Guadagno:** {tot_guadagno}\n"
            f"🔴 **Uscite Generali:** {tot_uscite}\n"
            f"💰 **Saldo Finale:** {saldo_finale}\n\n"
            f"📈 **Performance Attività**\n"
            f"• Totale Vendite: {tot_vendite}\n"
            f"• Totale Investimenti: {tot_investimenti}\n"
            f"• Totale Spese: {tot_spese}\n\n"
            f"🔍 **Analisi**\n"
            f"• Tasso di Efficienza: {tasso_efficienza}\n"
            f"• Guadagno Netto: {guadagno_netto}\n\n"
            f"📅 **Periodo (Settimana)**\n"
            f"• Vendite: {v_settimana} | Spese: {s_settimana} | Inv: {i_settimana}\n\n"
            f"📆 **Periodo (Mese)**\n"
            f"• Vendite: {v_mese} | Spese: {s_mese} | Inv: {i_mese}"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore nel recupero della Dashboard: {str(e)}")

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

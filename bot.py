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

# --- NUOVI COMANDI DEDICATI ---

async def bilancio(update, context):
    try:
        guadagno = sheet_dashboard.acell('B4').value
        uscite = sheet_dashboard.acell('B7').value
        saldo = sheet_dashboard.acell('B10').value
        
        # Calcolo opzionale sfizi
        try:
            sfizi = float(saldo.replace(',', '.')) * 0.30
        except:
            sfizi = 0.0

        await update.message.reply_text(
            f"📊 **Risultato Economico**\n\n"
            f"🟢 Totale Guadagno: {guadagno}€\n"
            f"🔴 Totale Uscite: {uscite}€\n"
            f"💰 Saldo Finale: {saldo}€\n\n"
            f"🎯 Budget per sfizi (30%): {sfizi:.2f}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def performance(update, context):
    try:
        vendite = sheet_dashboard.acell('D4').value
        investimenti = sheet_dashboard.acell('D7').value
        spese = sheet_dashboard.acell('D10').value

        await update.message.reply_text(
            f"📈 **Performance Attività**\n\n"
            f"• Totale Vendite: {vendite}€\n"
            f"• Totale Investimenti: {investimenti}€\n"
            f"• Totale Spese: {spese}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def analisi(update, context):
    try:
        tasso = sheet_dashboard.acell('H4').value
        netto = sheet_dashboard.acell('H7').value

        await update.message.reply_text(
            f"🔍 **Analisi**\n\n"
            f"• Tasso di Efficienza: {tasso}\n"
            f"• Guadagno Netto: {netto}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def settimana(update, context):
    try:
        v_sett = sheet_dashboard.acell('B14').value
        s_sett = sheet_dashboard.acell('D14').value
        i_sett = sheet_dashboard.acell('F14').value

        await update.message.reply_text(
            f"📅 **Dati Settimanali**\n\n"
            f"• Vendite Settimana: {v_sett}€\n"
            f"• Spese Settimana: {s_sett}€\n"
            f"• Investimenti Settimana: {i_sett}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def mese(update, context):
    try:
        v_mese = sheet_dashboard.acell('B17').value
        s_mese = sheet_dashboard.acell('D17').value
        i_mese = sheet_dashboard.acell('F17').value

        await update.message.reply_text(
            f"📆 **Dati Mensili**\n\n"
            f"• Vendite Mese: {v_mese}€\n"
            f"• Spese Mese: {s_mese}€\n"
            f"• Investimenti Mese: {i_mese}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")


if __name__ == '__main__':
    if not TELEGRAM_TOKEN or not CREDS_JSON:
        print("Errore: Variabili d'ambiente non trovate!")
    else:
        app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
        app.add_handler(CommandHandler("spesa", spesa))
        app.add_handler(CommandHandler("vendita", vendita))
        app.add_handler(CommandHandler("bilancio", bilancio))
        app.add_handler(CommandHandler("performance", performance))
        app.add_handler(CommandHandler("analisi", analisi))
        app.add_handler(CommandHandler("settimana", settimana))
        app.add_handler(CommandHandler("mese", mese))
        
        print("🤖 Bot avviato correttamente!")
        app.run_polling()

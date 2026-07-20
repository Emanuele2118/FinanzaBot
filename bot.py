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
        
        prodotto = " ".join(context.args[1:]) if len(context.args) > 1 else "Telegram"
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

# --- DEBUG MAPPA DASHBOARD ---
async def debug_dashboard(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        print("\n--- MAPPA COMPLETA DASHBOARD ---")
        for r_idx, riga in enumerate(valori):
            print(f"Riga {r_idx + 1} (indice {r_idx}): {riga}")
        print("---------------------------------\n")
        await update.message.reply_text("🔍 Mappa della Dashboard stampata nei log di Railway!")
    except Exception as e:
        await update.message.reply_text(f"❌ Errore debug: {str(e)}")

# --- COMANDI DASHBOARD ---

async def bilancio(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        # Stampa nei log per sicurezza
        print(f"[BILANCIO] Righe totali lette: {len(valori)}")

        # Tentiamo di leggere in modo flessibile o provvisorio (puoi aggiustare in base ai log)
        # Usiamo i comandi sicuri basati sulle righe che funzionano già
        await update.message.reply_text(
            f"📊 **Risultato Economico**\n\n"
            f"🟢 Totale Guadagno: {valori[3][1]}€\n"
            f"🔴 Totale Uscite: {valori[6][1]}€\n"
            f"💰 Saldo Finale: {valori[9][1]}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Bilancio: {str(e)}")

async def performance(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        await update.message.reply_text(
            f"📈 **Performance Attività**\n\n"
            f"• Totale Vendite: {valori[3][3]}€\n"
            f"• Totale Investimenti: {valori[6][3]}€\n"
            f"• Totale Spese: {valori[9][3]}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Performance: {str(e)}")

async def analisi(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        # Verifica se la riga e la colonna esistono prima di leggerle
        tasso = valori[3][7] if len(valori) > 3 and len(valori[3]) > 7 else "N/D"
        netto = valori[6][7] if len(valori) > 6 and len(valori[6]) > 7 else "N/D"

        await update.message.reply_text(
            f"🔍 **Analisi**\n\n"
            f"• Tasso di Efficienza: {tasso}\n"
            f"• Guadagno Netto: {netto}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Analisi: {str(e)}")

async def settimana(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        await update.message.reply_text(
            f"📅 **Dati Settimanali**\n\n"
            f"• Vendite Settimana: {valori[13][1]}€\n"
            f"• Spese Settimana: {valori[13][3]}€\n"
            f"• Investimenti Settimana: {valori[13][5]}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def mese(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        await update.message.reply_text(
            f"📆 **Dati Mensili**\n\n"
            f"• Vendite Mese: {valori[16][1]}€\n"
            f"• Spese Mese: {valori[16][3]}€\n"
            f"• Investimenti Mese: {valori[16][5]}€"
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
        app.add_handler(CommandHandler("debug", debug_dashboard))
        
        print("🤖 Bot avviato correttamente!")
        app.run_polling()

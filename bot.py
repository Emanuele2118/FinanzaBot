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

# --- COMANDI DASHBOARD (LEGCONO I RISULTATI DELLE FORMULE) ---

async def bilancio(update, context):
    try:
        # get_all_values con value_render_option='FORMATTED_VALUE' legge il risultato calcolato dalla formula
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        guadagno = valori[3][1]  # B4
        uscite = valori[6][1]    # B7
        saldo = valori[9][1]     # B10
        
        try:
            sfizi = float(str(saldo).replace('€', '').replace(' ', '').replace(',', '.')) * 0.30
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
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        vendite = valori[3][3]       # D4
        investimenti = valori[6][3]  # D7
        spese = valori[9][3]         # D10

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
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        tasso = valori[3][7]  # H4
        netto = valori[6][7]  # H7

        await update.message.reply_text(
            f"🔍 **Analisi**\n\n"
            f"• Tasso di Efficienza: {tasso}\n"
            f"• Guadagno Netto: {netto}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore: {str(e)}")

async def settimana(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        v_sett = valori[13][1]  # B14
        s_sett = valori[13][3]  # D14
        i_sett = valori[13][5]  # F14

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
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        v_mese = valori[16][1]  # B17
        s_mese = valori[16][3]  # D17
        i_mese = valori[16][5]  # F17

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

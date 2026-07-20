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

# --- COMANDI DASHBOARD ---

async def bilancio(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        
        # Colonna A: A4 (Guadagno), A7 (Uscite), A10 (Saldo)
        guadagno = valori[3][0] if len(valori) > 3 and len(valori[3]) > 0 else "0"
        uscite = valori[6][0] if len(valori) > 6 and len(valori[6]) > 0 else "0"
        saldo = valori[9][0] if len(valori) > 9 and len(valori[9]) > 0 else "0"
        
        try:
            val_saldo_clean = float(str(saldo).replace('€', '').replace(' ', '').replace(',', '.'))
            sfizi = val_saldo_clean * 0.30
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
        await update.message.reply_text(f"❌ Errore Bilancio: {str(e)}")

async def performance(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        vendite = valori[3][3] if len(valori) > 3 and len(valori[3]) > 3 else "0"
        investimenti = valori[6][3] if len(valori) > 6 and len(valori[6]) > 3 else "0"
        spese = valori[9][3] if len(valori) > 9 and len(valori[9]) > 3 else "0"

        await update.message.reply_text(
            f"📈 **Performance Attività**\n\n"
            f"• Totale Vendite: {vendite}€\n"
            f"• Totale Investimenti: {investimenti}€\n"
            f"• Totale Spese: {spese}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Performance: {str(e)}")

async def analisi(update, context):
    try:
        # Lettura mirata delle celle H4 (Tasso di Efficienza) e H7 (Guadagno Netto)
        tasso = sheet_dashboard.acell('H4', value_render_option='FORMATTED_VALUE').value
        netto = sheet_dashboard.acell('H7', value_render_option='FORMATTED_VALUE').value

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
        v_sett = valori[13][1] if len(valori) > 13 and len(valori[13]) > 1 else "0"
        s_sett = valori[13][3] if len(valori) > 13 and len(valori[13]) > 3 else "0"
        i_sett = valori[13][5] if len(valori) > 13 and len(valori[13]) > 5 else "0"

        await update.message.reply_text(
            f"📅 **Dati Settimanali**\n\n"
            f"• Vendite Settimana: {v_sett}€\n"
            f"• Spese Settimana: {s_sett}€\n"
            f"• Investimenti Settimana: {i_sett}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Settimana: {str(e)}")

async def mese(update, context):
    try:
        valori = sheet_dashboard.get_all_values(value_render_option='FORMATTED_VALUE')
        v_mese = valori[16][1] if len(valori) > 16 and len(valori[16]) > 1 else "0"
        s_mese = valori[16][3] if len(valori) > 16 and len(valori[16]) > 3 else "0"
        i_mese = valori[16][5] if len(valori) > 16 and len(valori[16]) > 5 else "0"

        await update.message.reply_text(
            f"📆 **Dati Mensili**\n\n"
            f"• Vendite Mese: {v_mese}€\n"
            f"• Spese Mese: {s_mese}€\n"
            f"• Investimenti Mese: {i_mese}€"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Errore Mese: {str(e)}")


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

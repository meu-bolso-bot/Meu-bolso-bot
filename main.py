import os, re, sqlite3, threading, asyncio
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")
print(f"TOKEN ok? {'SIM' if TOKEN else 'NAO'}")

flask_app = Flask(__name__)
@flask_app.route('/')
def home():
    return "Meu-bolso-bot online!"

conn = sqlite3.connect("gastos.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS gastos (valor REAL, descricao TEXT, categoria TEXT, data TEXT)")
conn.commit()

def parse(text: str):
    m = re.search(r"(\d+[.,]?\d*)", text.lower())
    if not m: return None
    v = float(m.group(1).replace(",", "."))
    t = text.lower()
    cat = "combustivel" if "gasolina" in t or "diesel" in t or "combust" in t else "adubo" if "adubo" in t else "semente" if "semente" in t else "outros"
    return v, text, cat

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Olá! Bot funcionando! Me diga: 50 reais de diesel")

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = parse(update.message.text)
    if not r:
        await update.message.reply_text("Não entendi. Ex: 100 de adubo")
        return
    v,d,c = r
    conn.execute("INSERT INTO gastos VALUES (?,?,?,?)", (v,d,c,datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"Salvo: R$ {v} em {c}")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = conn.execute("SELECT valor, descricao, categoria FROM gastos").fetchall()
    if not rows:
        await update.message.reply_text("Nenhum gasto ainda.")
        return
    total = sum(x[0] for x in rows)
    txt = f"Total: R$ {total:.2f}\n\n" + "\n".join([f"- R$ {v} | {c} | {d}" for v,d,c in rows[-10:]])
    await update.message.reply_text(txt)

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Flask em thread separada
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Bot no processo principal (corrige o erro de event loop)
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("relatorio", relatorio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    print("Bot iniciado - polling...")
    app.run_polling(drop_pending_updates=True)

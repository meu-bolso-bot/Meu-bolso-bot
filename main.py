import os, re, sqlite3, threading
from datetime import datetime
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Aceita TOKEN ou TELEGRAM_TOKEN
TOKEN = os.getenv("TELEGRAM_TOKEN") or os.getenv("TOKEN")
print(f"TOKEN encontrado: {'Sim' if TOKEN else 'NAO - configure TELEGRAM_TOKEN no Render'}")

flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Meu-bolso-bot online!"

conn = sqlite3.connect("gastos.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS gastos (valor REAL, descricao TEXT, categoria TEXT, data TEXT)")

def parse(text: str):
    t = text.lower()
    m = re.search(r"(\d+[.,]?\d*)", t)
    if not m:
        return None
    v_str = m.group(1).replace(",", ".")
    try:
        v = float(v_str)
    except:
        return None
    
    c = t
    if "gasolina" in c or "combustivel" in c:
        cat = "combustivel"
    elif "diesel" in c:
        cat = "combustivel"
    elif "adubo" in c:
        cat = "adubo"
    elif "semente" in c:
        cat = "semente"
    else:
        cat = "outros"
    
    d = text
    return v, d, cat

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"Olá! Eu sou seu Meu-bolso-bot. Me diga um gasto tipo: '50 reais de diesel'")

async def msg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    r = parse(update.message.text)
    if not r:
        await update.message.reply_text("Não entendi o valor. Ex: '100 de adubo'")
        return
    v, d, c = r
    conn.execute("INSERT INTO gastos VALUES (?,?,?,?)", (v, d, c, datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"Salvo: R$ {v} em {c} - {d}")

async def relatorio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cur = conn.execute("SELECT valor, descricao, categoria FROM gastos")
    rows = cur.fetchall()
    if not rows:
        await update.message.reply_text("Nenhum gasto ainda.")
        return
    total = sum(x[0] for x in rows)
    texto = f"Relatório - Total: R$ {total:.2f}\n\n"
    for valor, desc, cat in rows[-10:]:
        texto += f"- R$ {valor} | {cat} | {desc}\n"
    await update.message.reply_text(texto)

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("relatorio", relatorio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    print("Bot iniciado - polling...")
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    flask_app.run(host="0.0.0.0", port=port)

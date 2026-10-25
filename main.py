import os, re, sqlite3, threading
from datetime import datetime
from flask import Flask
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

TOKEN = os.getenv("TELEGRAM_TOKEN")
flask_app = Flask(__name__)

@flask_app.route('/')
def home():
    return "Meu-bolso-bot online!"

conn = sqlite3.connect("gastos.db", check_same_thread=False)
conn.execute("CREATE TABLE IF NOT EXISTS gastos (id INTEGER PRIMARY KEY, user_id INTEGER, valor REAL, descricao TEXT, categoria TEXT, data TEXT)")

def parse(t):
    t=t.lower()
    m=re.search(r"(\d+[.,]?\d*)", t.replace(",","."))
    if not m: return None
    v=float(m.group(1).replace(",","."))
    d=t.replace(m.group(0),"").strip() or "gasto"
    c="outro"
    if "diesel" in t: c="combustivel"
    elif "adubo" in t: c="adubo"
    elif "semente" in t: c="semente"
    return v,d,c

async def start(update, context):
    await update.message.reply_text("🌱 Pronto! Manda: 420 diesel")

async def msg(update, context):
    r=parse(update.message.text)
    if not r:
        await update.message.reply_text("Ex: 73 diesel")
        return
    v,d,c=r
    conn.execute("INSERT INTO gastos VALUES (NULL,?,?,?, ?,?)", (update.effective_user.id, v, d, c, datetime.now().isoformat()))
    conn.commit()
    await update.message.reply_text(f"✅ R$ {v:.2f} | {d} | {c}")

async def relatorio(update, context):
    cur=conn.execute("SELECT valor, descricao FROM gastos WHERE user_id=?", (update.effective_user.id,))
    rows=cur.fetchall()
    total=sum(x[0] for x in rows)
    await update.message.reply_text(f"TOTAL: R$ {total:.2f} | {len(rows)} gastos")

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("relatorio", relatorio))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, msg))
    app.run_polling()

if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))

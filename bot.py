import os
import json
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import datetime

# ── CONFIG ──────────────────────────────────────────────────────────────────
BOT_TOKEN  = os.environ.get("BOT_TOKEN",  "8714914060:AAET07qw3Z_CJnyLEEwJjooTCPxuz03Tf2Q")
JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")   # Your JSONBin Master Key
JSONBIN_BIN = os.environ.get("JSONBIN_BIN", "")   # Your Bin ID
# ────────────────────────────────────────────────────────────────────────────

HEADERS = {
    "Content-Type": "application/json",
    "X-Master-Key": JSONBIN_KEY
}

def fmt(n):
    return f"{abs(n):,.0f}"

def get_transactions():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN}/latest", headers=HEADERS)
        return r.json().get("record", {}).get("transactions", [])
    except:
        return []

def save_transactions(txs):
    requests.put(
        f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN}",
        headers=HEADERS,
        json={"transactions": txs}
    )

def calc_balance(txs):
    bal = 0
    for t in txs:
        bal += t["amount"] if t["type"] == "add" else -t["amount"]
    return bal

# ── COMMANDS ─────────────────────────────────────────────────────────────────

async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = (
        "👋 *Abrham & Biruk Cash Tracker Bot*\n\n"
        "Here are the commands you can use:\n\n"
        "➕ `/add 25000 agent deposit` — Add money\n"
        "➖ `/sub 6860 withdrawal` — Subtract money\n"
        "💰 `/balance` — Check current balance\n"
        "📜 `/history` — Last 10 transactions\n"
        "🗑️ `/clear` — Clear all history\n\n"
        "_Both Abrham and Biruk can use these commands!_"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def balance(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txs = get_transactions()
    bal = calc_balance(txs)
    tin  = sum(t["amount"] for t in txs if t["type"] == "add")
    tout = sum(t["amount"] for t in txs if t["type"] == "sub")

    sign = "+" if bal >= 0 else "-"
    emoji = "🟢" if bal >= 0 else "🔴"

    msg = (
        f"{emoji} *Current Balance*\n"
        f"`{sign}{fmt(bal)} Birr`\n\n"
        f"📈 Total In:  `+{fmt(tin)} Birr`\n"
        f"📉 Total Out: `-{fmt(tout)} Birr`\n"
        f"📊 Transactions: `{len(txs)}`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: `/add 25000 your note here`", parse_mode="Markdown")
        return
    try:
        amount = float(args[0].replace(",", ""))
        note = " ".join(args[1:]) if len(args) > 1 else "Added funds"
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Example: `/add 25000 agent deposit`", parse_mode="Markdown")
        return

    who = update.effective_user.first_name or "Someone"
    txs = get_transactions()
    txs.insert(0, {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "add",
        "amount": amount,
        "who": who,
        "note": note,
        "date": datetime.now().strftime("%b %d, %I:%M %p")
    })
    save_transactions(txs)
    bal = calc_balance(txs)

    msg = (
        f"✅ *Added {fmt(amount)} Birr*\n"
        f"📝 Note: _{note}_\n"
        f"👤 By: {who}\n\n"
        f"💰 New Balance: `{fmt(bal)} Birr`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args
    if not args:
        await update.message.reply_text("Usage: `/sub 6860 your note here`", parse_mode="Markdown")
        return
    try:
        amount = float(args[0].replace(",", ""))
        note = " ".join(args[1:]) if len(args) > 1 else "Withdrawn"
    except ValueError:
        await update.message.reply_text("❌ Invalid amount. Example: `/sub 6860 cash out`", parse_mode="Markdown")
        return

    who = update.effective_user.first_name or "Someone"
    txs = get_transactions()
    txs.insert(0, {
        "id": int(datetime.now().timestamp() * 1000),
        "type": "sub",
        "amount": amount,
        "who": who,
        "note": note,
        "date": datetime.now().strftime("%b %d, %I:%M %p")
    })
    save_transactions(txs)
    bal = calc_balance(txs)

    msg = (
        f"🔻 *Subtracted {fmt(amount)} Birr*\n"
        f"📝 Note: _{note}_\n"
        f"👤 By: {who}\n\n"
        f"💰 New Balance: `{fmt(bal)} Birr`"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    txs = get_transactions()
    if not txs:
        await update.message.reply_text("📭 No transactions yet.")
        return

    lines = ["📜 *Last 10 Transactions*\n"]
    for t in txs[:10]:
        icon = "↑" if t["type"] == "add" else "↓"
        sign = "+" if t["type"] == "add" else "-"
        lines.append(f"{icon} `{sign}{fmt(t['amount'])}` — {t['note']} _{t['who']} · {t['date']}_")

    bal = calc_balance(txs)
    lines.append(f"\n💰 *Balance: {fmt(bal)} Birr*")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def clear(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    save_transactions([])
    await update.message.reply_text("🗑️ All transactions cleared. Balance reset to 0.")

# ── MAIN ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start",   start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("add",     add))
    app.add_handler(CommandHandler("sub",     sub))
    app.add_handler(CommandHandler("history", history))
    app.add_handler(CommandHandler("clear",   clear))
    print("🤖 Bot is running...")
    app.run_polling()

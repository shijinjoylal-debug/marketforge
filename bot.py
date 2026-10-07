from ml_model import load_or_train
from backtest import backtest
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import BOT_TOKEN, ADMIN_IDS, SYMBOLS, CROWNSHIP_URL, CROWNSHIP_BOT_SECRET
from strategy import analyze_symbol, scan_market
from database import add_user, is_user_approved, get_approved_users, log_history
import os
import requests

approved_users = get_approved_users()


# =============================
# COMMAND: /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    log_history(
        "command",
        {
            "command": "/start",
            "user_id": chat_id
        }
    )

    # Normal /start without arguments
    if not context.args:
        await update.message.reply_text(
            "⚡ MarketForge v2\n\n"
            "Type BTC / ETH / SOL\n"
            "Use /scan for full market scan\n"
            "Use /stats for strategy stats"
        )
        return

    # /start TOKEN
    token = context.args[0].strip()

    if not CROWNSHIP_URL or not CROWNSHIP_BOT_SECRET:
        print("Crownship integration error: CROWNSHIP_URL or CROWNSHIP_BOT_SECRET is missing.")
        await update.message.reply_text(
            "⚠️ Activation service is temporarily unavailable.\n\n"
            "Please try again in a few moments."
        )
        return

    try:
        connect_endpoint = f"{CROWNSHIP_URL}/api/telegram/connect"
        response = requests.post(
            connect_endpoint,
            json={
                "token": token,
                "telegramId": chat_id
            },
            headers={
                "Authorization": f"Bearer {CROWNSHIP_BOT_SECRET}",
                "Content-Type": "application/json"
            },
            timeout=10
        )

        try:
            data = response.json()
        except Exception:
            data = {}

        if response.status_code == 200 and data.get("success"):
            # Crownship confirmed the purchase
            add_user(chat_id)
            approved_users.add(chat_id)

            log_history(
                "approval",
                {
                    "admin_id": "CROWNSHIP",
                    "approved_user": chat_id,
                    "token": token
                }
            )

            await update.message.reply_text(
                "✅ Purchase Activated!\n\n"
                "Your Crownship purchase has been connected to this Telegram account.\n\n"
                "You can now use:\n\n"
                "• BTC\n"
                "• ETH\n"
                "• SOL\n"
                "• /scan\n"
                "• /stats"
            )
        elif response.status_code in [400, 401, 404, 409] or not data.get("success"):
            await update.message.reply_text(
                "❌ This activation link is invalid or has already been used.\n\n"
                "Please contact Crownship support if you believe this is an error."
            )
        else:
            await update.message.reply_text(
                "⚠️ Activation service is temporarily unavailable.\n\n"
                "Please try again in a few moments."
            )

    except (requests.RequestException, Exception) as e:
        print("Crownship connection error:", e)
        await update.message.reply_text(
            "⚠️ Activation service is temporarily unavailable.\n\n"
            "Please try again in a few moments."
        )


# =============================
# COMMAND: /approve
# =============================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admin_id = update.effective_chat.id
    if admin_id not in ADMIN_IDS:
        await update.message.reply_text("❌ Not authorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <chat_id>")
        return
    try:
        uid = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat_id")
        return
    if uid in approved_users:
        await update.message.reply_text("User already approved")
        return

    add_user(uid)
    approved_users.add(uid)
    log_history("approval", {"admin_id": admin_id, "approved_user": uid})
    await update.message.reply_text(f"✅ Approved {uid}")


# =============================
# COMMAND: /scan
# =============================
async def scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in approved_users:
        await update.message.reply_text("⏳ Access pending")
        return

    results, bias = scan_market(SYMBOLS)
    log_history("command", {"command": "/scan", "user_id": chat_id, "bias": bias})

    msg = "📊 MARKET SCAN (1D)\n\n"

    for r in results:
        msg += (
            f"{r['symbol']} | {r['action']}\n"
            f"📈 Bull: {r['bull_prob']}%\n"
            f"📉 Bear: {r['bear_prob']}%\n"
        )

    msg += f"\n{bias}"

    await update.message.reply_text(msg)


# =============================
# COMMAND: /stats
# =============================
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    if chat_id not in approved_users:
        await update.message.reply_text("⏳ Access pending")
        return

    msg = "📊 STRATEGY STATS (1D)\n\n"
    log_history("command", {"command": "/stats", "user_id": chat_id})

    for sym in SYMBOLS:
        res = backtest(sym)
        msg += (
            f"🪙 {sym}\n"
            f"Winrate: {res['winrate']}%\n"
            f"Trades: {res['trades']} ({res['wins']}W / {res['losses']}L)\n\n"
        )

    await update.message.reply_text(msg)


# =============================
# MESSAGE HANDLER (BTC / ETH / SOL)
# =============================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text.upper()

    if chat_id not in approved_users:
        await update.message.reply_text("⏳ Access pending")
        return

    if text in ["BTC", "ETH", "SOL"]:
        symbol = text + "/USDT"
        action, confidence, price, reason = analyze_symbol(symbol)
        log_history("query", {"symbol": symbol, "user_id": chat_id, "action": action, "confidence": confidence})

        message = (
            f"📊 {symbol} Signal\n"
            f"──────────────\n"
            f"Action: {action}\n"
            f"Confidence: {confidence:.1f}%\n"
            f"──────────────\n"
            f"Reasoning:\n{reason}"
        )

        await update.message.reply_text(message)

    else:
        await update.message.reply_text(
            "Type BTC / ETH / SOL\nor use /scan"
        )


# =============================
# RUN BOT
# =============================
app = ApplicationBuilder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("approve", approve))
app.add_handler(CommandHandler("scan", scan))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

if __name__ == "__main__":
    app.run_polling()

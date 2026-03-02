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

from config import BOT_TOKEN, ADMIN_ID, SYMBOLS
from strategy import analyze_symbol, scan_market
from database import add_user, is_user_approved, get_approved_users, log_history


# =============================
# LOAD ML MODEL (optional)
# =============================
# ml_model = load_or_train("BTC/USDT") # Removed: Now handled inside strategy.py

approved_users = get_approved_users()



# =============================
# COMMAND: /start
# =============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log_history("command", {"command": "/start", "user_id": update.effective_chat.id})
    await update.message.reply_text(
        "🚀 MarketForge v2\n\n"
        "Type BTC / ETH / SOL\n"
        "Use /scan for full market scan\n"
        "Use /stats for strategy stats"
    )



# =============================
# COMMAND: /approve
# =============================
async def approve(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        await update.message.reply_text("❌ Not authorized")
        return

    if not context.args:
        await update.message.reply_text("Usage: /approve <chat_id>")
        return
    try:
        uid=int(context.args[0])
    except ValueError:
        await update.message.reply_text("Invalid chat_id")
        return
    if uid in approved_users:
        await update.message.reply_text("User already approved")
        return

    add_user(uid)
    approved_users.add(uid)
    log_history("approval", {"admin_id": ADMIN_ID, "approved_user": uid})
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
    for sym, result in results.items():
        msg += f"{sym} | Result: {result[action]} / {result[confidence]}%\n"
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
        result = backtest(sym)
        msg += f"{sym} | Result: {result[action]} / {result[confidence]}%\n"

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
        action, confidence, price = analyze_symbol(symbol)
        log_history("query", {"symbol": symbol, "user_id": chat_id, "action": action, "confidence": confidence})

        message = (
            f"📊 {symbol} Signal\n"
            f"━━━━━━━━━━━━━━\n"
            f"Action: {action}\n"
            f"Confidence: {confidence:.1f}%\n"
            #f Price: {price}\n"
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

app.run_polling()

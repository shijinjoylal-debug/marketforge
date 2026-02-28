import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
SYMBOLS = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")

# Hybrid Strategy Settings
ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.5"))
STRATEGY_WEIGHT = float(os.getenv("STRATEGY_WEIGHT", "0.5"))
THRESHOLD_BUY = int(os.getenv("THRESHOLD_BUY", "65"))
THRESHOLD_SELL = int(os.getenv("THRESHOLD_SELL", "35"))
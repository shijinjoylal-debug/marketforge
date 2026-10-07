import os
from dotenv import load_dotenv

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

BOT_TOKEN = os.getenv("BOT_TOKEN")

# Admin IDs
ADMIN_IDS = []
for key in ["ADMIN_ID", "ADMIN_ID2"]:
    val = os.getenv(key)
    if val:
        try:
            ADMIN_IDS.append(int(val.strip()))
        except ValueError:
            continue
# For backward compatibility if needed
ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0

SYMBOLS = os.getenv("SYMBOLS", "BTC/USDT,ETH/USDT,SOL/USDT").split(",")
TIMEFRAME = os.getenv("TIMEFRAME", "1h")
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("DB_NAME", "marketforge")

# Crownship Integration
CROWNSHIP_URL = os.getenv("CROWNSHIP_URL", "https://crownship.vercel.app").rstrip("/")
CROWNSHIP_BOT_SECRET = os.getenv("CROWNSHIP_BOT_SECRET", "")

# Hybrid Strategy Settings
ML_WEIGHT = float(os.getenv("ML_WEIGHT", "0.5"))
STRATEGY_WEIGHT = float(os.getenv("STRATEGY_WEIGHT", "0.5"))
THRESHOLD_BUY = int(os.getenv("THRESHOLD_BUY", "65"))
THRESHOLD_SELL = int(os.getenv("THRESHOLD_SELL", "35"))

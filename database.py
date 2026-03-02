import pymongo
from datetime import datetime
from config import MONGO_URI, DB_NAME, ADMIN_ID

client = pymongo.MongoClient(MONGO_URI)
db = client[DB_NAME]

# Collections
users_col = db["users"]
history_col = db["history"]
models_col = db["models"]

# ================= USER MANAGEMENT =================

def init_db():
    """Initialize database with admin if not exists"""
    if not users_col.find_one({"user_id": ADMIN_ID}):
        users_col.update_one(
            {"user_id": ADMIN_ID},
            {"$set": {"approved": True, "added_at": datetime.now()}},
            upsert=True
        )

def add_user(user_id):
    users_col.update_one(
        {"user_id": user_id},
        {"$set": {"approved": True, "added_at": datetime.now()}},
        upsert=True
    )

def is_user_approved(user_id):
    user = users_col.find_one({"user_id": user_id, "approved": True})
    return user is not None

def get_approved_users():
    users = users_col.find({"approved": True})
    return {user["user_id"] for user in users}

# ================= HISTORY LOGGING =================

def log_history(event_type, data):
    entry = {
        "event_type": event_type,
        "data": data,
        "timestamp": datetime.now()
    }
    history_col.insert_one(entry)

# ================= ML MODEL KNOWLEDGE =================

def save_model_metadata(symbol, accuracy, timeframe, metadata=None):
    entry = {
        "symbol": symbol,
        "accuracy": accuracy,
        "timeframe": timeframe,
        "metadata": metadata or {},
        "updated_at": datetime.now()
    }
    models_col.update_one(
        {"symbol": symbol, "timeframe": timeframe},
        {"$set": entry},
        upsert=True
    )

def get_model_knowledge(symbol, timeframe):
    return models_col.find_one({"symbol": symbol, "timeframe": timeframe})

# Initialize on import
init_db()

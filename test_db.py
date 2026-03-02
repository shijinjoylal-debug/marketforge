from database import add_user, is_user_approved, get_approved_users, log_history, save_model_metadata, get_model_knowledge
import time

def test_mongodb_integration():
    print("--- Testing MongoDB Integration ---")
    
    # 1. Test User Management
    test_user_id = 999999
    print(f"Adding test user {test_user_id}...")
    add_user(test_user_id)
    
    if is_user_approved(test_user_id):
        print("✅ User approval check passed.")
    else:
        print("❌ User approval check failed.")
        
    approved = get_approved_users()
    if test_user_id in approved:
        print("✅ Approved users list check passed.")
    else:
        print("❌ Approved users list check failed.")

    # 2. Test History Logging
    print("Logging test event...")
    log_history("test_event", {"message": "Verification test", "value": 42})
    print("✅ History logging called (check DB manually for persistence).")

    # 3. Test ML Model Metadata
    print("Saving test model metadata...")
    save_model_metadata("TEST/USDT", 0.85, "1h", {"note": "unit test"})
    
    knowledge = get_model_knowledge("TEST/USDT", "1h")
    if knowledge and knowledge["accuracy"] == 0.85:
        print("✅ Model metadata storage passed.")
    else:
        print("❌ Model metadata storage failed.")

    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    test_mongodb_integration()

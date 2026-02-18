import sys
import os

# Ensure verification script can import from current directory
sys.path.append(os.getcwd())

from strategy import analyze_symbol
from ml_model import train_model

def test_ml_integration():
    print("Testing ML Integration...")
    symbol = "BTC/USDT"
    
    # 1. Force train a model first to ensure it exists
    print("Training model...")
    # SMA200 requires at least 200 points + some buffer for drops
    model = train_model(symbol, limit=1000)
    if model:
        print("Model trained successfully.")
    else:
        print("Model training failed.")
        return

    # 2. Run analysis
    print(f"Analyzing {symbol}...")
    action, confidence, price = analyze_symbol(symbol)
    
    print(f"Result: Action={action}, Confidence={confidence}, Price={price}")
    
    # 3. Assertions
    if confidence == 0 and action != "WAIT":
        print("FAIL: Confidence is 0 for non-WAIT action.")
    else:
        print("PASS: Confidence seems valid (non-zero or WAIT).")

    if isinstance(confidence, (int, float)):
        print(f"PASS: Confidence is a number ({type(confidence)}).")
    else:
        print(f"FAIL: Confidence is not a number ({type(confidence)}).")

    if 0 <= confidence <= 100:
        print("PASS: Confidence is within 0-100 range.")
    else:
        print("FAIL: Confidence out of range.")

if __name__ == "__main__":
    test_ml_integration()

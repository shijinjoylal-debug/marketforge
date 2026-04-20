import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from strategy import analyze_symbol

def test_reasoning():
    symbols = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    for sym in symbols:
        print(f"Testing {sym}...")
        try:
            action, confidence, price, reason = analyze_symbol(sym)
            print(f"Action: {action}")
            print(f"Confidence: {confidence}%")
            print(f"Price: {price}")
            print("Reasoning:")
            print(reason)
            print("-" * 30)
        except Exception as e:
            print(f"Error testing {sym}: {e}")

if __name__ == "__main__":
    test_reasoning()

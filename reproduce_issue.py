from strategy import analyze_symbol

print("Testing analyze_symbol('BTC/USDT')...")
try:
    action, confidence, price = analyze_symbol("BTC/USDT")
    print(f"Action: {action}, Confidence: {confidence}%, Price: {price}")
except Exception as e:
    print(f"Caught exception: {e}")
    import traceback
    traceback.print_exc()

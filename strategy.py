import ccxt
import pandas as pd
import ta
from ml_model import predict_confidence

exchange = ccxt.binance()

def get_indicators(symbol, timeframe="1h", limit=150):
    df = pd.DataFrame(
        exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit),
        columns=["time","open","high","low","close","volume"]
    )

    # Indicators
    df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)

    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()

    return df


def analyze_symbol(symbol):
    try:
        # 🔹 Get ML Confidence
        # This returns the probability (0-100) that the price will go UP (Bullish)
        bullish_prob = predict_confidence(symbol, "1d")
        
        # 🔹 Heuristic Analysis (Legacy/Hybrid)
        # We still keep this to get the current price and ensure data availability
        lt_df = get_indicators(symbol, "1h")
        if lt_df.empty:
            return "WAIT", 0, 0
            
        current_price = lt_df["close"].iloc[-1]

        # 🔹 Decision Logic based on ML
        if bullish_prob >= 55:
            action = "BUY"
            display_confidence = bullish_prob
        elif bullish_prob <= 45:
            action = "SELL"
            display_confidence = 100 - bullish_prob
        else:
            action = "WAIT"
            display_confidence = abs(bullish_prob - 50) * 2

        return action, display_confidence, current_price

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return "WAIT", 0, 0


def scan_market(symbols):
    results = []
    bull = bear = 0

    for sym in symbols:
        action, confidence, price = analyze_symbol(sym)
        
        # Determine bull/bear probabilities for the display
        if action == "BUY":
            bull_prob = confidence
            bear_prob = 100 - confidence
        elif action == "SELL":
            bull_prob = 100 - confidence
            bear_prob = confidence
        else:
            bull_prob = 50
            bear_prob = 50

        results.append({
            "symbol": sym,
            "action": action,
            "confidence": confidence,
            "bull_prob": bull_prob,
            "bear_prob": bear_prob,
            "price": price
        })

        if action == "BUY":
            bull += 1
        elif action == "SELL":
            bear += 1

    if bull > bear:
        bias = "📈 Bullish Market"
    elif bear > bull:
        bias = "📉 Bearish Market"
    else:
        bias = "⚖️ Sideways Market"

    return results, bias

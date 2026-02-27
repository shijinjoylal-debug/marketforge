import ccxt
import pandas as pd
import ta

exchange = ccxt.binance()

def get_indicators(symbol, timeframe="4h", limit=3000):
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
        print(f"Analyzing {symbol}...")
        # 🔹 Higher timeframe (trend)
        ht_df = get_indicators(symbol, "4h")
        
        # 🔹 Lower timeframe (entry)
        lt_df = get_indicators(symbol, "1h")

        ht_last = ht_df.iloc[-1]
        lt_last = lt_df.iloc[-1]
        
        print("HT Last:\n", ht_last[["EMA20", "EMA50"]])
        print("LT Last:\n", lt_last[["RSI", "MACD", "MACD_signal", "close", "EMA20"]])

        score = 0

        # =========================
        # 🔥 TREND CONFIRMATION
        # =========================

        if ht_last["EMA20"] > ht_last["EMA50"]:
            print("Trend: Bullish (+25)")
            score += 25
        else:
            print("Trend: Bearish (-25)")
            score -= 25

        # =========================
        # ⚡ ENTRY SIGNAL
        # =========================

        if lt_last["RSI"] < 35:
            print("RSI: Oversold (+20)")
            score += 20
        elif lt_last["RSI"] > 65:
            print("RSI: Overbought (-20)")
            score -= 20
        else:
            print("RSI: Neutral (0)")

        if lt_last["MACD"] > lt_last["MACD_signal"]:
            print("MACD: Bullish (+20)")
            score += 20
        else:
            print("MACD: Bearish (-20)")
            score -= 20

        if lt_last["close"] > lt_last["EMA20"]:
            print("Price vs EMA: Bullish (+15)")
            score += 15
        else:
            print("Price vs EMA: Bearish (-15)")
            score -= 15
            
        print(f"Final Score: {score}")

        # =========================
        # 🎯 DECISION
        # =========================

        confidence = max(0, min(100, score + 50))
        print(f"Confidence: {confidence}")

        if confidence >= 70:
            action = "BUY"
        elif confidence <= 30:
            action = "SELL"
        else:
            action = "WAIT"

        return action, confidence

    except Exception as e:
        print("Error:", e)
        import traceback
        traceback.print_exc()
        return "WAIT", 0

if __name__ == "__main__":
    analyze_symbol("BTC/USDT")

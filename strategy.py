import ccxt
import pandas as pd
import ta
from ml_model import predict_confidence
from config import ML_WEIGHT, STRATEGY_WEIGHT, THRESHOLD_BUY, THRESHOLD_SELL

exchange = ccxt.binance()

def get_indicators(symbol, timeframe="1h", limit=3000):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    if not ohlcv:
        return pd.DataFrame()
        
    df = pd.DataFrame(
        ohlcv,
        columns=["time","open","high","low","close","volume"]
    )

    # Indicators
    df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
    df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
    df["SMA200"] = ta.trend.sma_indicator(df["close"], window=200)
    df["RSI"] = ta.momentum.rsi(df["close"], window=14)
    df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)

    macd = ta.trend.MACD(df["close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()

    return df

def get_technical_score(df):
    """
    Calculates a technical score from -100 (Strong Bearish) to 100 (Strong Bullish)
    基于技术指标计算一个从 -100 到 100 的分值
    """
    if df.empty:
        return 0
        
    last = df.iloc[-1]
    score = 0
    
    # 1. Trend Filter (EMA Cross) - weight: 30
    if last["EMA20"] > last["EMA50"]:
        score += 30
    else:
        score -= 30
        
    # 2. Momentum (RSI) - weight: 20
    if last["RSI"] > 60:
        score += 20
    elif last["RSI"] < 40:
        score -= 20
        
    # 3. MACD Confirmation - weight: 20
    if last["MACD"] > last["MACD_signal"]:
        score += 20
    else:
        score -= 20
        
    # 4. Long-term Trend (SMA200) - weight: 20
    if last["close"] > last["SMA200"]:
        score += 20
    else:
        score -= 20
        
    # 5. Trend Strength (ADX) - weight: 10
    # If trend is strong (>25), we add 10 points in the direction of the trend
    if last["ADX"] > 25:
        if last["EMA20"] > last["EMA50"]:
            score += 10
        else:
            score -= 10
            
    return score

def analyze_symbol(symbol):
    try:
        # =============================
        # 🔹 ML Prediction (0 to 100)
        # =============================
        ml_prob = predict_confidence(symbol, "1h")
        ml_score = (ml_prob - 50) * 2  # Normalize to -100 to 100
        
        # =============================
        # 🔹 Technical Score (-100 to 100)
        # =============================
        df = get_indicators(symbol, "1h")
        if df.empty:
            return "WAIT", 0, 0
            
        current_price = df["close"].iloc[-1]
        tech_score = get_technical_score(df)
        
        # =============================
        # 🔹 Volatility Adjustment
        # =============================
        volatility = df["close"].pct_change().rolling(20).std().iloc[-1]
        vol_multiplier = 1.0
        if volatility < 0.0015:  # extremely low volatility
            vol_multiplier = 0.5
        elif volatility > 0.01:   # high volatility risk
            vol_multiplier = 0.8
            
        # =============================
        # 🔹 Hybrid Fusion
        # =============================
        hybrid_score_raw = (ml_score * ML_WEIGHT) + (tech_score * STRATEGY_WEIGHT)
        hybrid_score = hybrid_score_raw * vol_multiplier
        
        # Convert hybrid score back to 0-100 confidence for display
        display_confidence = (hybrid_score / 2) + 50
        
        # =============================
        # 🔹 Action Decision
        # =============================
        if display_confidence >= THRESHOLD_BUY:
            action = "BUY"
            final_conf = display_confidence
        elif display_confidence <= THRESHOLD_SELL:
            action = "SELL"
            final_conf = 100 - display_confidence
        else:
            action = "WAIT"
            final_conf = abs(display_confidence - 50) * 2
            
        return action, round(final_conf, 2), current_price

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
        return "WAIT", 0, 0
        
def scan_market(symbols):
    results = []
    bull = bear = 0

    for sym in symbols:
        action, confidence, price = analyze_symbol(sym)
        
        # Determine bull/bear probabilities for the display logic
        # Here confidence is "how sure we are of the action"
        if action == "BUY":
            bull_prob = confidence
            bear_prob = 100 - confidence
        elif action == "SELL":
            bull_prob = 100 - confidence
            bear_prob = confidence
        else:
            # For WAIT, we show a neutral split but offset by our slight bias
            bull_prob = 50 + (confidence / 4 if action == "WAIT" else 0)
            bear_prob = 50 - (confidence / 4 if action == "WAIT" else 0)

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

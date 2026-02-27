import os
import time
import joblib
import pandas as pd
import ccxt
import ta
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

exchange = ccxt.binance()

# Create models directory if not exists
if not os.path.exists("models"):
    os.makedirs("models")

def get_model_path(symbol, timeframe):
    safe_symbol = symbol.replace("/", "_")
    return f"models/{safe_symbol}_{timeframe}.pkl"

# ================= TRAIN MODEL =================

def train_model(symbol="BTC/USDT", timeframe="1d", limit=3000):
    print(f"Training model for {symbol} ({timeframe})...")
    
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        if not ohlcv or len(ohlcv) < 50:
            print(f"Not enough data for {symbol}")
            return None
            
        df = pd.DataFrame(
            ohlcv,
            columns=["time","open","high","low","close","volume"]
        )

        # --- Indicators ---
        # Trend
        df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
        df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
        df["SMA200"] = ta.trend.sma_indicator(df["close"], window=200)
        
        # Momentum
        df["RSI"] = ta.momentum.rsi(df["close"], window=14)
        macd = ta.trend.MACD(df["close"])
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()
        
        # Volatility
        bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
        df["BB_HIGH"] = bb.bollinger_hband()
        df["BB_LOW"] = bb.bollinger_lband()
        df["ATR"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
        
        # Trend Strength
        df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)

        df.dropna(inplace=True)

        # --- Features ---
        df["ema_diff"] = (df["EMA20"] - df["EMA50"]) / df["close"]
        df["price_dist_ema20"] = (df["close"] - df["EMA20"]) / df["close"]
        df["price_dist_sma200"] = (df["close"] - df["SMA200"]) / df["close"]
        df["rsi"] = df["RSI"] / 100.0
        df["macd_diff"] = (df["MACD"] - df["MACD_SIGNAL"]) / df["close"]
        df["bb_width"] = (df["BB_HIGH"] - df["BB_LOW"]) / df["close"]
        df["atr_ratio"] = df["ATR"] / df["close"]
        df["adx_ratio"] = df["ADX"] / 100.0
        
        # --- Labeling ---
        # Predict if price will be higher in next candle
        # Can be tuned to predict % change, but classification is simpler for confidence
        df["target"] = (df["close"].shift(-1) > df["close"]).astype(int)
        
        df.dropna(inplace=True)

        feature_cols = [
            "ema_diff", "price_dist_ema20", "price_dist_sma200", 
            "rsi", "macd_diff", "bb_width", "atr_ratio", "adx_ratio"
        ]
        
        X = df[feature_cols]
        y = df["target"]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, shuffle=False
        )

        # RandomForest is generally more robust for this than LogisticRegression
        pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model", RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42))
        ])

        pipeline.fit(X_train, y_train)

        # Accuracy check
        preds = pipeline.predict(X_test)
        acc = accuracy_score(y_test, preds)
        print(f"Model Accuracy for {symbol}: {round(acc*100, 2)}%")

        # Save model
        model_path = get_model_path(symbol, timeframe)
        joblib.dump(pipeline, model_path)
        
        return pipeline

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Error training model for {symbol}: {e}")
        return None


# ================= LOAD MODEL =================

def load_or_train(symbol="BTC/USDT", timeframe="1h"):
    model_path = get_model_path(symbol, timeframe)
    if os.path.exists(model_path):
        age = time.time() - os.path.getmtime(model_path)
        if age < 24 * 3600:
            try:
                return joblib.load(model_path)
            except:
                pass
        return train_model(symbol,timeframe)


    # Reload model if it's older than 1 day
    if os.path.exists(model_path):
        age = time.time() - os.path.getmtime(model_path)
        if age < 24 * 3600:
            try:
                return joblib.load(model_path)
            except:
                pass
    
    return train_model(symbol, timeframe)


# ================= PREDICT =================

def predict_confidence(symbol="BTC/USDT", timeframe="1h"):
    # Ensure we have a model
    model = load_or_train(symbol, timeframe)
    if model is None:
        return 0.5, 50.0 # Neutral

    try:
        # Fetch fresh data for prediction
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=3000)
        df = pd.DataFrame(
            ohlcv,
            columns=["time","open","high","low","close","volume"]
        )

        # Recreate indicators exactly as in training
        df["EMA20"] = ta.trend.ema_indicator(df["close"], window=20)
        df["EMA50"] = ta.trend.ema_indicator(df["close"], window=50)
        df["SMA200"] = ta.trend.sma_indicator(df["close"], window=200)
        
        df["RSI"] = ta.momentum.rsi(df["close"], window=14)
        macd = ta.trend.MACD(df["close"])
        df["MACD"] = macd.macd()
        df["MACD_SIGNAL"] = macd.macd_signal()
        
        bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
        df["BB_HIGH"] = bb.bollinger_hband()
        df["BB_LOW"] = bb.bollinger_lband()
        df["ATR"] = ta.volatility.average_true_range(df["high"], df["low"], df["close"], window=14)
        df["ADX"] = ta.trend.adx(df["high"], df["low"], df["close"], window=14)

        df.dropna(inplace=True)
        last = df.iloc[-1]

        # Calculate features for the last candle
        features = pd.DataFrame([{
            "ema_diff": (last["EMA20"] - last["EMA50"]) / last["close"],
            "price_dist_ema20": (last["close"] - last["EMA20"]) / last["close"],
            "price_dist_sma200": (last["close"] - last["SMA200"]) / last["close"],
            "rsi": last["RSI"] / 100.0,
            "macd_diff": (last["MACD"] - last["MACD_SIGNAL"]) / last["close"],
            "bb_width": (last["BB_HIGH"] - last["BB_LOW"]) / last["close"],
            "atr_ratio": last["ATR"] / last["close"],
            "adx_ratio": last["ADX"] / 100.0
        }])

        # Predict probability of class 1 (Bullish/Up)
        probs = model.predict_proba(features)[0]
        bullish_prob = probs[1]
        
        # If bullish_prob > 0.5, we lean BULL. If < 0.5, we lean BEAR.
        # Confidence is distance from 0.5 scaled or just the raw probability?
        # Let's return the raw probability of it going UP.
        # The caller can decide if it's a BUY or SELL signal.
        
        return bullish_prob * 100

    except Exception as e:
        print(f"Error predicting for {symbol}: {e}")
        return 50.0  # Neutral

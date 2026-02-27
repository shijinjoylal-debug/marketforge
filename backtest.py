import ccxt
import pandas as pd
import ta

exchange = ccxt.binance()

def backtest(symbol, timeframe="4h", limit=3000):
    df = pd.DataFrame(
        exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit),
        columns=["time","open","high","low","close","volume"]
    )

    df["EMA20"] = ta.trend.ema_indicator(df["close"], 20)
    df["EMA50"] = ta.trend.ema_indicator(df["close"], 50)
    df["RSI"] = ta.momentum.rsi(df["close"], 14)
    df["MACD"] = ta.trend.macd(df["close"])

    wins = 0
    losses = 0
    trades = 0

    for i in range(50, len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]

        score = 0
        if row["EMA20"] > row["EMA50"]:
            score += 1
        if row["close"] > row["EMA20"]:
            score += 1
        if row["RSI"] > 50:
            score += 1
        if row["MACD"] > 0:
            score += 1

        # Only strong signals
        if score >= 3:
            trades += 1
            entry = row["close"]
            exit_price = next_row["close"]

            if exit_price > entry:
                wins += 1
            else:
                losses += 1

    winrate = round((wins / trades) * 100, 2) if trades > 0 else 0

    return {
        "symbol": symbol,
        "trades": trades,
        "wins": wins,
        "losses": losses,
        "winrate": winrate
    }
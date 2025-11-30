import pandas as pd
import numpy as np

from technical import compute_all_indicators
from signal_logic import decide_signal


# -------------------------------------------
# CONFIG
# -------------------------------------------
CSV_PATH = "../data/nifty_5m.csv"   # change if needed
TAKE_PROFIT_PCT = 0.003          # 0.3% target
STOP_LOSS_PCT = 0.002            # 0.2% sl
HOLD_CANDLES_MAX = 5             # max candles to hold


def load_data(path):
    df = pd.read_csv(path)

    # Try to normalize column names
    df.columns = [c.lower() for c in df.columns]

    # Expect at least: open, high, low, close
    required = {"open", "high", "low", "close"}
    if not required.issubset(set(df.columns)):
        raise ValueError(f"CSV must contain {required}, got {df.columns}")

    # If timestamp/datetime exists, parse it
    for col in ["timestamp", "datetime", "date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])
            df = df.sort_values(col)
            break

    return df


def backtest():
    print("Loading data...")
    df = load_data(CSV_PATH)

    print("Computing indicators...")
    df = compute_all_indicators(df)

    # Drop initial NaNs from indicators
    df = df.replace([np.inf, -np.inf], np.nan).dropna().reset_index(drop=True)

    # We'll store trade results
    trades = []

    print("Running backtest over", len(df), "candles...")
    
    # Try to load ML models for backtesting
    try:
        from ml.ml_model import predict_next
        ml_enabled = True
        print("✅ ML models loaded for backtesting")
    except Exception as e:
        print(f"⚠️ ML not available for backtest: {e}")
        ml_enabled = False
        def predict_next(df):
            return {"enabled": False}
    
    # Debug: check signals for all rows
    print("\n=== Signal Analysis ===")
    for idx in range(min(len(df), 10)):
        row = df.iloc[idx].to_dict()
        # Get ML prediction for first 10 rows
        ml_pred = predict_next(df.iloc[max(0, idx-49):idx+1]) if ml_enabled and idx >= 50 else {"enabled": False}
        signal = decide_signal(row, ml_pred)
        print(f"Candle {idx}: {signal.get('action', 'WAIT')} (conf: {signal.get('confidence', 0)}%) [ML: {ml_pred.get('final_ml_score', 'N/A')}]")

    # Track ML vs Non-ML results
    trades_with_ml = []
    trades_without_ml = []

    i = 0
    while i < len(df) - HOLD_CANDLES_MAX - 1:
        row = df.iloc[i].to_dict()
        
        # Get ML prediction using last 50 candles
        ml_pred = None
        if ml_enabled and i >= 50:
            try:
                ml_pred = predict_next(df.iloc[i-49:i+1])
            except Exception as e:
                ml_pred = {"enabled": False, "error": str(e)}
        else:
            ml_pred = {"enabled": False}
        
        # Get signal with ML
        signal = decide_signal(row, ml_pred)
        
        # Get signal without ML for comparison
        signal_no_ml = decide_signal(row, None)

        action = signal.get("action", "WAIT")
        price = float(row["close"])

        # Only enter on BUY/SELL, skip WAIT
        if action not in ["BUY", "SELL", "STRONG BUY", "STRONG SELL"]:
            i += 1
            continue

        direction = 1 if "BUY" in action else -1

        entry_idx = i + 1  # enter on next candle open (realistic)
        if entry_idx >= len(df):
            break

        entry_row = df.iloc[entry_idx]
        entry_price = float(entry_row["open"])

        tp = entry_price * (1 + direction * TAKE_PROFIT_PCT)
        sl = entry_price * (1 - direction * STOP_LOSS_PCT)

        exit_price = None
        exit_idx = None
        exit_reason = "max_hold"

        # Simulate bar-by-bar after entry
        for j in range(entry_idx, min(entry_idx + HOLD_CANDLES_MAX, len(df))):
            bar = df.iloc[j]

            high = float(bar["high"])
            low = float(bar["low"])
            close = float(bar["close"])

            if direction == 1:
                # Long: SL if low <= sl, TP if high >= tp
                if low <= sl:
                    exit_price = sl
                    exit_idx = j
                    exit_reason = "SL"
                    break
                if high >= tp:
                    exit_price = tp
                    exit_idx = j
                    exit_reason = "TP"
                    break
            else:
                # Short: SL if high >= sl, TP if low <= tp
                if high >= sl:
                    exit_price = sl
                    exit_idx = j
                    exit_reason = "SL"
                    break
                if low <= tp:
                    exit_price = tp
                    exit_idx = j
                    exit_reason = "TP"
                    break

        # If still no exit, close at last bar close
        if exit_price is None:
            last_bar = df.iloc[min(entry_idx + HOLD_CANDLES_MAX, len(df)) - 1]
            exit_price = float(last_bar["close"])
            exit_idx = min(entry_idx + HOLD_CANDLES_MAX, len(df)) - 1

        ret_pct = (exit_price - entry_price) / entry_price * direction * 100.0

        trade_record = {
            "entry_idx": entry_idx,
            "exit_idx": exit_idx,
            "direction": "LONG" if direction == 1 else "SHORT",
            "entry_price": entry_price,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "ret_pct": ret_pct,
            "signal_action": action,
            "ml_enabled": ml_pred.get("enabled", False) if ml_pred else False,
            "ml_score": ml_pred.get("final_ml_score") if ml_pred and ml_pred.get("enabled") else None,
        }
        
        trades.append(trade_record)
        
        # Separate tracking for ML vs non-ML
        if ml_pred and ml_pred.get("enabled"):
            trades_with_ml.append(trade_record)
        
        # Also track what the signal would be without ML
        trade_no_ml = trade_record.copy()
        trade_no_ml["signal_action"] = signal_no_ml.get("action", "WAIT")
        trades_without_ml.append(trade_no_ml)

        # Move index to after exit to avoid overlapping trades
        i = exit_idx + 1

    if not trades:
        print("No trades generated.")
        return

    trades_df = pd.DataFrame(trades)

    total_trades = len(trades_df)
    wins = (trades_df["ret_pct"] > 0).sum()
    losses = (trades_df["ret_pct"] <= 0).sum()
    win_rate = wins / total_trades * 100

    avg_win = trades_df[trades_df["ret_pct"] > 0]["ret_pct"].mean()
    avg_loss = trades_df[trades_df["ret_pct"] <= 0]["ret_pct"].mean()
    avg_ret = trades_df["ret_pct"].mean()

    max_gain = trades_df["ret_pct"].max()
    max_drawdown = trades_df["ret_pct"].min()

    print("\n========== BACKTEST RESULTS ==========")
    print(f"Total trades      : {total_trades}")
    print(f"Win rate          : {win_rate:.1f}%")
    print(f"Avg return / trade: {avg_ret:.2f}%")
    print(f"Avg win           : {avg_win:.2f}%")
    print(f"Avg loss          : {avg_loss:.2f}%")
    print(f"Best trade        : {max_gain:.2f}%")
    print(f"Worst trade       : {max_drawdown:.2f}%")

    # Simple equity curve
    trades_df["equity"] = (1 + trades_df["ret_pct"] / 100.0).cumprod()
    final_equity = trades_df["equity"].iloc[-1]
    print(f"Equity multiple   : {final_equity:.2f}x")
    
    # ML vs Non-ML comparison
    if ml_enabled and len(trades_with_ml) > 0:
        ml_df = pd.DataFrame(trades_with_ml)
        ml_wins = (ml_df["ret_pct"] > 0).sum()
        ml_win_rate = ml_wins / len(ml_df) * 100
        ml_avg_ret = ml_df["ret_pct"].mean()
        
        print("\n========== ML ENHANCED RESULTS ==========")
        print(f"ML trades         : {len(trades_with_ml)}")
        print(f"ML win rate       : {ml_win_rate:.1f}%")
        print(f"ML avg return     : {ml_avg_ret:.2f}%")
        print(f"Improvement       : {ml_win_rate - win_rate:+.1f}% win rate, {ml_avg_ret - avg_ret:+.2f}% return")

    # Optional: save trades for later analysis
    trades_df.to_csv("backtest_trades.csv", index=False)
    print("\n💾 Saved trade-by-trade details to backtest_trades.csv")


if __name__ == "__main__":
    backtest()

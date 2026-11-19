"""A simple z-score mean-reversion test on the spread.

Rule: when z > +entry, bet the spread will narrow (short the spread).
      when z < -entry, bet the spread will widen (long the spread).
      Exit when |z| falls back below `exit`.
PnL is measured in $/barrel of spread change. No transaction costs, no position sizing,
and you cannot actually trade spot prices directly, so this is an illustration, not a strategy.
"""
import numpy as np
import pandas as pd


def positions(z: pd.Series, entry: float = 2.0, exit: float = 0.5) -> pd.Series:
    pos = np.zeros(len(z))
    current = 0
    for i, value in enumerate(z.to_numpy()):
        if np.isnan(value):
            current = 0
        elif current == 0:
            if value > entry:
                current = -1
            elif value < -entry:
                current = 1
        elif abs(value) < exit:
            current = 0
        pos[i] = current
    return pd.Series(pos, index=z.index, name="position")


def run_backtest(df: pd.DataFrame, entry: float = 2.0, exit: float = 0.5) -> tuple[pd.DataFrame, dict]:
    out = df.copy()
    out["position"] = positions(out["zscore"], entry, exit)
    # Trade on the next day's move: yesterday's signal earns today's change (no look-ahead)
    out["daily_pnl"] = out["position"].shift(1).fillna(0) * out["spread"].diff().fillna(0)
    out["cum_pnl"] = out["daily_pnl"].cumsum()

    trade_id = (out["position"] != out["position"].shift()).cumsum()
    trades = []
    for _, days in out.groupby(trade_id):
        if days["position"].iloc[0] == 0:
            continue
        # PnL of a trade = PnL earned on the days after each day the position was held
        held_days = days.index
        nxt = out.index.get_indexer(held_days) + 1
        nxt = nxt[nxt < len(out)]
        trades.append(float(out["daily_pnl"].iloc[nxt].sum()))

    trades = np.array(trades)
    stats = {
        "entry_z": entry,
        "exit_z": exit,
        "num_trades": int(len(trades)),
        "hit_rate_pct": round(float((trades > 0).mean() * 100), 1) if len(trades) else None,
        "avg_trade_pnl": round(float(trades.mean()), 2) if len(trades) else None,
        "total_pnl_per_bbl": round(float(trades.sum()), 2) if len(trades) else 0.0,
    }
    return out, stats

"""Spread, rolling statistics, and dislocation detection."""
import pandas as pd


def add_spread(prices: pd.DataFrame) -> pd.DataFrame:
    """Brent minus WTI, in $/barrel. Positive means Brent trades at a premium."""
    out = prices.copy()
    out["spread"] = out["brent"] - out["wti"]
    return out


def add_rolling_stats(df: pd.DataFrame, window: int = 60) -> pd.DataFrame:
    """Rolling mean, standard deviation, and z-score of the spread.

    Uses only data up to and including each day, so there is no look-ahead.
    z = (today's spread - rolling mean) / rolling std
    """
    out = df.copy()
    roll = out["spread"].rolling(window=window, min_periods=window)
    out["roll_mean"] = roll.mean()
    out["roll_std"] = roll.std()
    out["zscore"] = (out["spread"] - out["roll_mean"]) / out["roll_std"]
    return out


def find_dislocations(df: pd.DataFrame, threshold: float = 2.0) -> pd.DataFrame:
    """Group consecutive days with |z| above the threshold into episodes.

    Returns one row per episode: start, end, length in trading days, and the peak z-score.
    """
    flag = df["zscore"].abs() > threshold
    episode_id = (flag != flag.shift()).cumsum()[flag]
    rows = []
    for _, days in df[flag].groupby(episode_id):
        peak_idx = days["zscore"].abs().idxmax()
        rows.append({
            "start": days.index[0].date(),
            "end": days.index[-1].date(),
            "days": len(days),
            "peak_z": round(float(days.loc[peak_idx, "zscore"]), 2),
            "spread_at_peak": round(float(days.loc[peak_idx, "spread"]), 2),
        })
    return pd.DataFrame(rows, columns=["start", "end", "days", "peak_z", "spread_at_peak"])


def summary_stats(df: pd.DataFrame) -> dict:
    s = df["spread"]
    return {
        "first_date": str(df.index[0].date()),
        "last_date": str(df.index[-1].date()),
        "years": round((df.index[-1] - df.index[0]).days / 365.25, 1),
        "trading_days": int(len(df)),
        "mean_spread": round(float(s.mean()), 2),
        "median_spread": round(float(s.median()), 2),
        "max_spread": round(float(s.max()), 2),
        "max_spread_date": str(s.idxmax().date()),
        "min_spread": round(float(s.min()), 2),
        "min_spread_date": str(s.idxmin().date()),
    }

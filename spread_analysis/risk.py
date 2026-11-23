"""Risk metrics for a daily PnL series measured in $/bbl of spread.

There is no capital base for a spread position, so the Sharpe ratio here is the annualized
mean daily PnL divided by its standard deviation (an information ratio on PnL), not a return on capital.
"""
import numpy as np
import pandas as pd


def max_drawdown(pnl: pd.Series) -> tuple[float, str, str]:
    """Largest peak-to-trough fall in cumulative PnL, with the peak and trough dates."""
    cum = pnl.cumsum()
    peak = cum.cummax()
    dd = cum - peak
    trough = dd.idxmin()
    start = cum.loc[:trough].idxmax()
    return float(dd.min()), str(pd.Timestamp(start).date()), str(pd.Timestamp(trough).date())


def sharpe(pnl: pd.Series, periods_per_year: int = 252, active_only: bool = False) -> float:
    s = pnl[pnl != 0] if active_only else pnl
    if len(s) < 2 or s.std() == 0:
        return float("nan")
    return float(s.mean() / s.std() * np.sqrt(periods_per_year))


def risk_metrics(pnl: pd.Series) -> dict:
    dd, start, trough = max_drawdown(pnl)
    return {
        "max_drawdown_per_bbl": round(dd, 2),
        "max_drawdown_start": start,
        "max_drawdown_trough": trough,
        "sharpe_annualized": round(sharpe(pnl), 2),
        "worst_day_per_bbl": round(float(pnl.min()), 2),
        "best_day_per_bbl": round(float(pnl.max()), 2),
    }


def autocorr_by_year(spread: pd.Series, exclude: tuple[str, str] | None = ("2020-03-01", "2020-06-30")) -> dict:
    """Lag-one autocorrelation of daily spread changes: overall, excluding a stress window, and per calendar year.

    A consistently negative value means a move one day tends to reverse the next. If it holds in every
    year, a few outlier days cannot explain it, which points to a structural cause such as Brent and WTI
    spot prices being assessed at different times (nonsynchronous pricing).
    """
    d = spread.diff().dropna()
    out = {"overall": round(float(d.autocorr(1)), 3)}
    if exclude:
        keep = (d.index < exclude[0]) | (d.index > exclude[1])
        out["excluding_window"] = round(float(d[keep].autocorr(1)), 3)
    years = {str(y): round(float(g.autocorr(1)), 3) for y, g in d.groupby(d.index.year) if len(g) > 20}
    out["by_year"] = years
    out["years_negative"] = int(sum(v < 0 for v in years.values()))
    out["years_tested"] = len(years)
    return out

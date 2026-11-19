import numpy as np
import pandas as pd

from spread_analysis.backtest import positions, run_backtest


def test_positions_follow_rules():
    z = pd.Series([0, 2.5, 1.5, 0.3, -2.5, -1.0, -0.2, np.nan])
    assert positions(z, 2.0, 0.5).tolist() == [0, -1, -1, 0, 1, 1, 0, 0]


def test_short_spread_profits_when_spread_falls():
    idx = pd.bdate_range("2021-01-01", periods=4)
    df = pd.DataFrame({"spread": [10.0, 10.0, 8.0, 8.0], "zscore": [0.0, 3.0, 0.1, 0.0]}, index=idx)
    out, stats = run_backtest(df, 2.0, 0.5)
    assert out["daily_pnl"].tolist() == [0.0, 0.0, 2.0, 0.0]
    assert stats["num_trades"] == 1
    assert stats["hit_rate_pct"] == 100.0

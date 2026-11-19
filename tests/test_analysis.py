import numpy as np
import pandas as pd

from spread_analysis.analysis import add_rolling_stats, add_spread, find_dislocations


def make_prices(n=300, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2020-01-01", periods=n)
    wti = 60 + rng.normal(0, 1, n).cumsum()
    brent = wti + 5 + rng.normal(0, 0.5, n)
    return pd.DataFrame({"brent": brent, "wti": wti}, index=idx)


def test_spread_is_brent_minus_wti():
    df = add_spread(make_prices())
    assert np.allclose(df["spread"], df["brent"] - df["wti"])
    assert df["spread"].notna().all()


def test_rolling_stats_have_no_lookahead():
    df = add_rolling_stats(add_spread(make_prices()), window=20)
    # changing a future value must not change today's z-score
    altered = make_prices()
    altered.iloc[-1, 0] += 1000
    df2 = add_rolling_stats(add_spread(altered), window=20)
    assert np.allclose(df["zscore"].iloc[:-1].dropna(), df2["zscore"].iloc[:-1].dropna())


def test_first_window_is_nan():
    df = add_rolling_stats(add_spread(make_prices()), window=20)
    assert df["zscore"].iloc[:19].isna().all()
    assert df["zscore"].iloc[19:].notna().all()


def test_dislocation_detected_for_spike():
    prices = make_prices()
    prices.iloc[200:203, 0] += 30  # three-day Brent spike
    df = add_rolling_stats(add_spread(prices), window=60)
    episodes = find_dislocations(df, threshold=2.0)
    assert len(episodes) >= 1
    assert episodes["peak_z"].max() > 2

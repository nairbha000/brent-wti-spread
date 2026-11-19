"""Run the full analysis: load data, compute the spread, find dislocations, backtest, save charts.

Examples:
    python run_analysis.py                     # EIA spreadsheets, no key needed
    python run_analysis.py --source api        # EIA API, needs EIA_API_KEY
    python run_analysis.py --xls-dir data     # use RBRTEd.xls and RWTCd.xls saved in data/
    python run_analysis.py --source csv --csv data/prices.csv
"""
import argparse
import json
from pathlib import Path

from spread_analysis.analysis import add_rolling_stats, add_spread, find_dislocations, summary_stats
from spread_analysis.backtest import run_backtest
from spread_analysis.risk import risk_metrics
from spread_analysis.data import load_prices
from spread_analysis.plots import plot_prices, plot_spread, plot_zscore_and_pnl


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--source", choices=["xls", "api", "csv"], default="xls")
    p.add_argument("--csv", help="path to CSV with date, brent, wti columns")
    p.add_argument("--xls-dir", help="folder containing RBRTEd.xls and RWTCd.xls downloaded from eia.gov")
    p.add_argument("--start", default="2010-01-01")
    p.add_argument("--window", type=int, default=60)
    p.add_argument("--entry", type=float, default=2.0)
    p.add_argument("--exit", type=float, default=0.5)
    p.add_argument("--out", default="outputs")
    args = p.parse_args()

    out = Path(args.out)
    out.mkdir(exist_ok=True)

    prices = load_prices(args.source, args.start, args.csv, args.xls_dir)
    prices.to_csv(Path("data") / "prices.csv")

    df = add_rolling_stats(add_spread(prices), args.window)
    episodes = find_dislocations(df, args.entry)
    df, bt = run_backtest(df, args.entry, args.exit)

    plot_prices(df, out / "prices.png")
    plot_spread(df, out / "spread.png")
    plot_zscore_and_pnl(df, args.entry, out / "zscore_pnl.png")
    episodes.to_csv(out / "dislocations.csv", index=False)

    bt.update(risk_metrics(df["daily_pnl"]))
    results = {"summary": summary_stats(df), "dislocation_episodes": int(len(episodes)), "backtest": bt}
    (out / "results.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print(f"\nTop 5 dislocations by |peak z|:\n{episodes.reindex(episodes['peak_z'].abs().sort_values(ascending=False).index).head()}")


if __name__ == "__main__":
    main()

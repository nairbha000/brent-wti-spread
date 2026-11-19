"""Charts for the README."""
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# Well-known events that moved the spread. Verify each one yourself before you cite it.
EVENTS = [
    ("2011-09-23", "2011: spread peaks near $30 (Cushing glut)"),
    ("2015-12-18", "U.S. lifts crude export ban"),
    ("2020-04-20", "WTI prices go negative"),
    ("2026-02-28", "Middle East war, Hormuz closes"),
    ("2026-10-02", "Spot spread peaks at $37.62"),
]


def _annotate(ax, df):
    for date, label in EVENTS:
        d = pd.Timestamp(date)
        if df.index[0] <= d <= df.index[-1]:
            ax.axvline(d, color="gray", linestyle="--", linewidth=0.8)
            ax.text(d, ax.get_ylim()[1], " " + label, rotation=90, va="top", fontsize=8, color="dimgray",
                    bbox=dict(facecolor="white", alpha=0.8, edgecolor="none", pad=1))


def plot_prices(df, path):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(df.index, df["brent"], label="Brent", linewidth=1)
    ax.plot(df.index, df["wti"], label="WTI", linewidth=1)
    ax.set_ylabel("$ per barrel")
    ax.set_title("Brent and WTI daily spot prices")
    ax.legend()
    _annotate(ax, df)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_spread(df, path):
    fig, ax = plt.subplots(figsize=(11, 4.5))
    ax.plot(df.index, df["spread"], linewidth=1, label="Brent − WTI")
    ax.plot(df.index, df["roll_mean"], linewidth=1, label="60-day mean")
    ax.axhline(0, color="black", linewidth=0.6)
    ax.set_ylabel("$ per barrel")
    ax.set_title("Brent–WTI spread")
    ax.legend()
    _annotate(ax, df)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def plot_zscore_and_pnl(df, entry, path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=True)
    ax1.plot(df.index, df["zscore"], linewidth=0.8)
    for level in (entry, -entry):
        ax1.axhline(level, color="red", linestyle="--", linewidth=0.8)
    ax1.set_ylabel("z-score")
    ax1.set_title(f"Spread z-score (60-day) with ±{entry} entry bands")
    ax2.plot(df.index, df["cum_pnl"], linewidth=1)
    ax2.set_ylabel("Cumulative PnL ($/bbl)")
    ax2.set_title("Mean-reversion backtest (no costs)")
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)

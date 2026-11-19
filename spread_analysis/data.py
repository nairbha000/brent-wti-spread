"""Load daily Brent and WTI spot prices from the U.S. Energy Information Administration (EIA).

Three ways to get the data:
  1. "api": EIA API v2 (free key from https://www.eia.gov/opendata/register.php, set EIA_API_KEY)
  2. "xls": EIA's public history spreadsheets (no key needed)
  3. "csv": a CSV you saved yourself with columns date, brent, wti
"""
import os
import pandas as pd

SERIES = {"brent": "RBRTE", "wti": "RWTC"}  # Brent (Europe) and WTI (Cushing, OK) daily spot, $/barrel
XLS_URL = "https://www.eia.gov/dnav/pet/hist_xls/{series}d.xls"
API_URL = "https://api.eia.gov/v2/petroleum/pri/spt/data/"


def load_from_api(start="2010-01-01", api_key=None):
    import requests

    api_key = api_key or os.environ.get("EIA_API_KEY")
    if not api_key:
        raise ValueError("Set the EIA_API_KEY environment variable or pass api_key.")
    frames = {}
    for name, series in SERIES.items():
        rows, offset = [], 0
        while True:  # the API returns at most 5000 rows per request, so page through results
            params = {
                "api_key": api_key,
                "frequency": "daily",
                "data[0]": "value",
                "facets[series][]": series,
                "start": start,
                "sort[0][column]": "period",
                "sort[0][direction]": "asc",
                "offset": offset,
                "length": 5000,
            }
            resp = requests.get(API_URL, params=params, timeout=60)
            resp.raise_for_status()
            batch = resp.json()["response"]["data"]
            rows.extend(batch)
            if len(batch) < 5000:
                break
            offset += 5000
        s = pd.DataFrame(rows)[["period", "value"]]
        s["period"] = pd.to_datetime(s["period"])
        frames[name] = s.set_index("period")["value"].astype(float)
    return _combine(frames, start)


def load_from_xls(start="2010-01-01", local_dir=None):
    """Read EIA history spreadsheets, from the web or from RBRTEd.xls / RWTCd.xls in local_dir."""
    frames = {}
    for name, series in SERIES.items():
        src = os.path.join(local_dir, f"{series}d.xls") if local_dir else XLS_URL.format(series=series)
        # EIA history files: sheet "Data 1", two header rows above the column names
        df = pd.read_excel(src, sheet_name="Data 1", skiprows=2)
        df.columns = ["date", "value"]
        df["date"] = pd.to_datetime(df["date"])
        frames[name] = df.set_index("date")["value"].astype(float)
    return _combine(frames, start)


def load_from_csv(path, start="2010-01-01"):
    df = pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()
    return df.loc[start:, ["brent", "wti"]].dropna()


def _combine(frames, start):
    """Join the two series on date and keep only days where both benchmarks traded."""
    df = pd.DataFrame(frames).sort_index()
    df.index.name = "date"
    return df.loc[start:].dropna()


def load_prices(source="xls", start="2010-01-01", csv_path=None, xls_dir=None):
    if source == "api":
        return load_from_api(start)
    if source == "xls":
        return load_from_xls(start, xls_dir)
    if source == "csv":
        return load_from_csv(csv_path, start)
    raise ValueError(f"Unknown source: {source}")

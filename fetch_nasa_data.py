"""
CropCast AI — NASA POWER Data Fetcher
Fetches 33 years of real monthly weather for any lat/lon.
Usage:
  python fetch_nasa_data.py                        # defaults to Coimbatore
  python fetch_nasa_data.py 28.61 77.20            # Delhi
  python fetch_nasa_data.py 13.08 80.27            # Chennai
Saves: data/nasa_weather_<lat>_<lon>.csv
"""

import sys
import time
import json
import requests
import pandas as pd
from pathlib import Path

Path("data").mkdir(exist_ok=True)

NASA_API = "https://power.larc.nasa.gov/api/temporal/monthly/point"
PARAMS   = "T2M,PRECTOTCORR,RH2M,WS2M,T2M_MAX,T2M_MIN"


def fetch(lat: float, lon: float, start: int = 1990, end: int = 2023) -> pd.DataFrame:
    print(f"\n🌍 Fetching NASA POWER data for ({lat}, {lon}) ...")
    url = (
        f"{NASA_API}?parameters={PARAMS}"
        f"&community=AG&longitude={lon}&latitude={lat}"
        f"&start={start}&end={end}&format=JSON"
    )

    for attempt in range(3):
        try:
            r = requests.get(url, timeout=60)
            r.raise_for_status()
            break
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            time.sleep(5)
    else:
        raise RuntimeError("NASA API unreachable after 3 attempts.")

    raw = r.json()["properties"]["parameter"]

    # raw keys: {"T2M": {"199001": 24.3, "199002": 25.1, ...}, ...}
    rows = []
    for yyyymm, t2m in raw["T2M"].items():
        year  = int(yyyymm[:4])
        month = int(yyyymm[4:])
        if month == 13:          # NASA uses 13 = annual mean — skip
            continue
        rows.append({
            "year":       year,
            "month":      month,
            "month_sin":  __import__("math").sin(2 * __import__("math").pi * month / 12),
            "month_cos":  __import__("math").cos(2 * __import__("math").pi * month / 12),
            "temp_avg":   round(t2m, 2),
            "temp_max":   round(raw["T2M_MAX"][yyyymm], 2),
            "temp_min":   round(raw["T2M_MIN"][yyyymm], 2),
            # NASA gives mm/day → multiply by days in month
            "rainfall":   round(max(0, raw["PRECTOTCORR"][yyyymm] * _days(year, month)), 2),
            "humidity":   round(min(99, max(10, raw["RH2M"][yyyymm])), 2),
            "wind_speed": round(max(0, raw["WS2M"][yyyymm] * 3.6), 2),  # m/s → km/h
        })

    df = pd.DataFrame(rows).sort_values(["year", "month"]).reset_index(drop=True)
    out = f"data/nasa_weather_{lat}_{lon}.csv"
    df.to_csv(out, index=False)
    print(f"✅ Saved {len(df)} rows → {out}")
    print(df.groupby("month")[["temp_avg","rainfall","humidity"]].mean().round(1).to_string())
    return df


def _days(year: int, month: int) -> int:
    import calendar
    return calendar.monthrange(year, month)[1]


if __name__ == "__main__":
    lat = float(sys.argv[1]) if len(sys.argv) > 1 else 11.00   # Coimbatore
    lon = float(sys.argv[2]) if len(sys.argv) > 2 else 76.95
    fetch(lat, lon)

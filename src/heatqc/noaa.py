"""Retrieve NOAA USCRN Daily01 (QC-screened), never raw/pre-QC data.

Official source: https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01/
Daily01 whitespace columns (zero-indexed): WBANNO 0; LST_DATE 1; LON 3;
LAT 4; T_DAILY_MAX 5. LST dates are station-local standard dates.
"""
from __future__ import annotations
from io import StringIO
from pathlib import Path
import hashlib
import re
import time
import requests
import pandas as pd
import numpy as np

BASE = "https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01"
PREFERRED_STATES = ("AZ","CA","FL","TX","CO","KS","GA","NC","NY","WA",
                    "WI","NM","OR","MT","UT","MO","SC","VA","AL","NV","ND","IL")
FILE_RE = re.compile(r'CRND0103-(\d{4})-([A-Z]{2}_[A-Za-z0-9_.-]+)\.txt')
CONUS_EXCLUDED = {"AK","HI","PR","GU","VI"}

def get_text(url: str, cache_path: Path | None = None) -> str:
    if cache_path is not None and cache_path.exists():
        return cache_path.read_text(encoding="utf-8")
    last = None
    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=35, headers={"User-Agent":"heatwave-qc-research/0.1 (academic data retrieval)"})
            resp.raise_for_status()
            text = resp.text
            if cache_path is not None:
                cache_path.parent.mkdir(parents=True, exist_ok=True)
                cache_path.write_text(text, encoding="utf-8")
            return text
        except requests.RequestException as exc:
            last = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"NOAA download failed: {url} ({last})")

def list_year_stations(year: int, cache_dir: Path) -> dict[str,str]:
    html = get_text(f"{BASE}/{year}/", cache_dir / f"index_{year}.html")
    found = {}
    for yr, slug in FILE_RE.findall(html):
        if int(yr) == year and slug.split("_")[0] not in CONUS_EXCLUDED:
            found[slug] = f"CRND0103-{year}-{slug}.txt"
    if not found:
        raise ValueError(f"No Daily01 station files found in {year} directory")
    return found

def select_stations(cache_dir: Path, n: int = 12, start: int = 2010, end: int = 2025) -> list[str]:
    """Predefined state order; no selection using extreme/QC outcomes."""
    a = list_year_stations(start, cache_dir)
    b = list_year_stations(end, cache_dir)
    common = set(a) & set(b)
    selected = []
    for state in PREFERRED_STATES:
        options = sorted(slug for slug in common if slug.startswith(state+"_"))
        if options:
            selected.append(options[0])
        if len(selected) >= n:
            break
    if len(selected) < n:
        selected.extend(s for s in sorted(common) if s not in selected)
    if len(selected) < n:
        raise ValueError(f"Only {len(selected)} stations occur in both {start} and {end}; requested {n}")
    return selected[:n]

def parse_daily(text: str, station_slug: str, source_url: str) -> pd.DataFrame:
    """Parse NOAA product as documented; preserve source provenance."""
    if not text.strip():
        raise ValueError(f"Empty NOAA file: {source_url}")
    d = pd.read_csv(StringIO(text), sep=r"\s+", header=None, comment="#")
    if d.shape[1] < 6:
        raise ValueError(f"NOAA file unexpectedly has {d.shape[1]} columns: {source_url}")
    out = pd.DataFrame({
        "station_id": station_slug,
        "wban": d.iloc[:,0].astype(str),
        "date": pd.to_datetime(d.iloc[:,1].astype(str),format="%Y%m%d",errors="coerce"),
        "lon": pd.to_numeric(d.iloc[:,3], errors="coerce"),
        "lat": pd.to_numeric(d.iloc[:,4], errors="coerce"),
        "tmax_c": pd.to_numeric(d.iloc[:,5], errors="coerce"),
        "source_url": source_url,
    })
    out.loc[out.tmax_c <= -9990, "tmax_c"] = np.nan
    if out.date.isna().any() or out.date.duplicated().any():
        raise ValueError(f"Invalid/duplicate NOAA dates in {source_url}")
    if not out.tmax_c.dropna().between(-80,65).all():
        raise ValueError(f"Unusual Tmax values in {source_url}; inspect rather than silently clip")
    return out

def load_real(stations: list[str], start_year: int, end_year: int, cache_dir: Path) -> pd.DataFrame:
    frames=[]; inventory=[]
    for slug in stations:
        for year in range(start_year,end_year+1):
            name=f"CRND0103-{year}-{slug}.txt"
            url=f"{BASE}/{year}/{name}"
            path=cache_dir / str(year) / name
            try:
                content=get_text(url,path)
                frame=parse_daily(content,slug,url)
                frames.append(frame)
                inventory.append({"station_id":slug,"year":year,"url":url,
                                  "sha256":hashlib.sha256(content.encode("utf-8")).hexdigest(),
                                  "rows":len(frame),"status":"downloaded"})
            except (requests.HTTPError,RuntimeError) as exc:
                inventory.append({"station_id":slug,"year":year,"url":url,"status":str(exc)})
                print(f"WARNING: unavailable {slug} {year}: {exc}")
    if not frames:
        raise ValueError("No real NOAA data available")
    df=pd.concat(frames,ignore_index=True).sort_values(["station_id","date"])
    if df.duplicated(["station_id","date"]).any():
        raise ValueError("Duplicate station-date pairs")
    return df, pd.DataFrame(inventory)

def make_demo(n_stations: int = 4, seed: int = 1126) -> pd.DataFrame:
    """ENTIRELY SYNTHETIC. For software smoke tests only; not scientific results."""
    rng=np.random.default_rng(seed)
    dates=pd.date_range("2010-01-01","2025-12-31",freq="D")
    frames=[]
    for i in range(n_stations):
        season = 13*np.cos(2*np.pi*(dates.dayofyear.to_numpy()-195)/365.25)
        noise = rng.normal(0,3.2,len(dates))
        values = 18 + i*1.3 + season + noise
        for yr in range(2010,2026):
            for start_day in (185,221,250):
                ix=(dates.year==yr) & (dates.dayofyear>=start_day) & (dates.dayofyear<start_day+5)
                values[ix]+=8
        values[rng.choice(len(dates),size=23,replace=False)] = np.nan
        frames.append(pd.DataFrame({"station_id":f"DEMO_{i+1:02d}","wban":f"9{i:04d}",
                     "date":dates,"lat":35+i,"lon":-110+i*3,"tmax_c":values,
                     "source_url":"SYNTHETIC_NOT_NOAA"}))
    return pd.concat(frames,ignore_index=True)

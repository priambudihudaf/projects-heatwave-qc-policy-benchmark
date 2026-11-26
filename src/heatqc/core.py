"""Heatwave event logic, policy handling, and event-level comparison."""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

def calendar_day(dates):
    """1..365 non-leap calendar ordinal; Feb 29 maps to Feb 28 (excluded from fitting)."""
    d=pd.DatetimeIndex(dates)
    doy=d.dayofyear.to_numpy(dtype=int)
    leap=d.is_leap_year
    after=(d.month > 2)
    doy = doy - (leap & after).astype(int)
    doy[(d.month==2) & (d.day==29)] = 59
    return doy

def fit_p90(train: pd.DataFrame, window: int = 7, percentile: float = 90.0) -> np.ndarray:
    """Day-of-calendar percentile with cyclic +/- window; training dates only."""
    d=train.copy()
    d=d[d.tmax_c.notna() & ~((d.date.dt.month==2)&(d.date.dt.day==29))]
    days=calendar_day(d.date)
    temps=d.tmax_c.to_numpy(dtype=float)
    thresholds=np.full(366,np.nan)
    for day in range(1,366):
        dist=np.abs(days-day)
        dist=np.minimum(dist,365-dist)
        sample=temps[dist<=window]
        if len(sample)<40: raise ValueError(f"Insufficient train data near calendar day {day}")
        thresholds[day]=np.percentile(sample,percentile)
    return thresholds

def attach_threshold(d: pd.DataFrame, thresholds: np.ndarray) -> pd.DataFrame:
    out=d.copy()
    out["heat_threshold_c"]=thresholds[calendar_day(out.date)]
    return out

@dataclass(frozen=True)
class Event:
    start: pd.Timestamp
    end: pd.Timestamp
    days: tuple[pd.Timestamp,...]
    peak_c: float
    @property
    def duration(self): return len(self.days)

def find_events(df:pd.DataFrame,min_length:int=3,season_months:tuple[int,...]=(5,6,7,8,9)) -> list[Event]:
    """Missing days break runs. Sorting and full daily continuity checked explicitly."""
    d=df.sort_values("date").reset_index(drop=True)
    if d.date.duplicated().any(): raise ValueError("Duplicate dates in event series")
    good=(d.date.dt.month.isin(season_months) &
          d.tmax_c.notna() & d.heat_threshold_c.notna() &
          (d.tmax_c>d.heat_threshold_c)).to_numpy()
    dates=pd.DatetimeIndex(d.date)
    events=[]; run=[]
    for i,flag in enumerate(good):
        if flag and (not run or (dates[i]-dates[run[-1]]).days==1):
            run.append(i)
        else:
            if len(run)>=min_length:
                events.append(Event(dates[run[0]],dates[run[-1]],
                              tuple(dates[run]),float(d.loc[run,"tmax_c"].max())))
            run=[i] if flag else []
    if len(run)>=min_length:
        events.append(Event(dates[run[0]],dates[run[-1]],
                      tuple(dates[run]),float(d.loc[run,"tmax_c"].max())))
    return events

def apply_policy(df:pd.DataFrame, flag:np.ndarray, policy:str, cap_c:float)->pd.DataFrame:
    out=df.copy()
    flag=np.asarray(flag,dtype=bool)
    if len(flag)!=len(out):raise ValueError("QC mask length differs from time series")
    if policy=="preserve":
        pass
    elif policy=="remove":
        out.loc[flag,"tmax_c"]=np.nan
    elif policy=="cap":
        out.loc[flag,"tmax_c"]=np.minimum(out.loc[flag,"tmax_c"],cap_c)
    else:raise ValueError("Unknown handling policy: "+policy)
    out["qc_flag_simulated"]=flag
    return out

def event_metrics(reference:list[Event],candidate:list[Event],candidate_series:pd.DataFrame)->dict:
    """Overlap-based event recall; split events and disappeared events separate.

    Candidate events touching multiple reference events are counted as overlaps
    for diagnostic purposes, not a claimed one-to-one event match.
    """
    predsets=[set(e.days) for e in candidate]
    matched=0;fragmented=0;disappeared=0;losses=[];peak_errors=[]
    for e in reference:
        r=set(e.days)
        overlaps=[p for p in predsets if r & p]
        if overlaps:
            matched+=1
            if len(overlaps)>=2:fragmented+=1
            retained=set().union(*(r & p for p in overlaps))
            losses.append(len(r-retained))
            vals=candidate_series[candidate_series.date.isin(retained)].tmax_c
            peak_errors.append(float(vals.max()-e.peak_c))
        else:
            disappeared+=1
            losses.append(len(r))
    novel=sum(not any(set(c.days)&set(r.days) for r in reference) for c in candidate)
    return {"reference_events":len(reference),"candidate_events":len(candidate),
            "matched_events":matched,"fragmented_events":fragmented,
            "disappeared_events":disappeared,"unmatched_candidate_events":novel,
            "event_recall":matched/len(reference) if reference else np.nan,
            "fragmentation_rate":fragmented/len(reference) if reference else np.nan,
            "disappearance_rate":disappeared/len(reference) if reference else np.nan,
            "mean_lost_reference_days":float(np.mean(losses)) if losses else np.nan,
            "mean_peak_error_c":float(np.mean(peak_errors)) if peak_errors else np.nan}

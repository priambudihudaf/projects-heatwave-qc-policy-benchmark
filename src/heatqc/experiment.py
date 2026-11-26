"""Controlled experiment holding identical QC flag masks across policies.

NOTE: reference values are provider-QC-screened, not certified ground truth.
Error locations are synthetic/oracle experimental interventions only.
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from .core import find_events,apply_policy,event_metrics

SCENARIOS = ("clean_start","clean_middle","clean_end",
             "spike_inside","spike_outside","offset_inside","offset_outside","mixed")
POLICIES = ("preserve","remove","cap")

def make_scenario(base:pd.DataFrame,reference_events,scenario:str,rng:np.random.Generator):
    contaminated=base.copy().reset_index(drop=True)
    n=len(base)
    error=np.zeros(n,dtype=bool)
    flags=np.zeros(n,dtype=bool)
    if not reference_events:
        return None
    event=reference_events[int(rng.integers(0,len(reference_events)))]
    positions=np.flatnonzero(contaminated.date.isin(event.days))
    if not len(positions):raise AssertionError("Reference event missing from series")
    if scenario in ("clean_start","clean_middle","clean_end"):
        pos=positions[0] if scenario=="clean_start" else positions[-1] if scenario=="clean_end" else positions[len(positions)//2]
        flags[pos]=True
    elif scenario in ("spike_inside","offset_inside","mixed"):
        pos=int(positions[len(positions)//2])
        error[pos]=True
        if scenario=="offset_inside":
            for j in (pos-1,pos+1):
                if 0<=j<n and contaminated.date.iloc[j].month in (5,6,7,8,9) and pd.notna(contaminated.tmax_c.iloc[j]):
                    error[j]=True
        if scenario=="mixed":
            # false flag on a separate clean heatwave date, in addition to true error.
            clean=int(positions[0] if positions[0]!=pos else positions[-1])
            if clean!=pos:flags[clean]=True
        contaminated.loc[error,"tmax_c"]+=5.0 if scenario!="offset_inside" else 3.0
        flags |= error
    elif scenario in ("spike_outside","offset_outside"):
        in_event=np.zeros(n,dtype=bool)
        for ev in reference_events:
            in_event |= contaminated.date.isin(ev.days).to_numpy()
        candidates=np.flatnonzero((~in_event)&contaminated.tmax_c.notna().to_numpy()&
                                  contaminated.date.dt.month.isin((5,6,7,8,9)).to_numpy())
        if not len(candidates):return None
        pos=int(rng.choice(candidates))
        error[pos]=True
        if scenario=="offset_outside":
            for j in (pos-1,pos+1):
                if 0<=j<n and not in_event[j] and pd.notna(contaminated.tmax_c.iloc[j]):
                    error[j]=True
        contaminated.loc[error,"tmax_c"]+=10.0 if scenario=="spike_outside" else 5.0
        flags |= error
    else:raise ValueError(scenario)
    return contaminated,flags,error,event

def run_experiments(test:pd.DataFrame,thresholds:dict,cap_by_station:dict,
                    reps:int=30,seed:int=20261126):
    rows=[]
    for (station,year),subset in test.groupby(["station_id",test.date.dt.year],sort=True):
        d=subset.sort_values("date").reset_index(drop=True).copy()
        d["heat_threshold_c"]=thresholds[station][__import__("heatqc.core",fromlist=["calendar_day"]).calendar_day(d.date)]
        ref=find_events(d)
        if not ref:continue
        for scenario_i,scenario in enumerate(SCENARIOS):
            for rep in range(reps):
                # stable independent RNG per station/year/scenario/rep across reruns
                key=sum(ord(c) for c in station)
                rng=np.random.default_rng(seed + key*10000 + year*101 + scenario_i*1000000 + rep)
                sample=make_scenario(d,ref,scenario,rng)
                if sample is None:continue
                contaminated,flags,errors,target=sample
                for policy in POLICIES:
                    handled=apply_policy(contaminated,flags,policy,cap_by_station[station])
                    cand=find_events(handled)
                    result=event_metrics(ref,cand,handled)
                    rows.append({"station_id":station,"year":year,"scenario":scenario,"replicate":rep,
                         "policy":policy,"n_flags":int(flags.sum()),"n_injected_errors":int(errors.sum()),
                         "n_false_flags":int((flags&~errors).sum()),
                         "target_reference_start":target.start.strftime("%Y-%m-%d"),
                         **result})
    return pd.DataFrame(rows)

def summarize(runs:pd.DataFrame,n_boot:int=300,seed:int=27):
    """Uncertainty from station-level cluster bootstrap, NOT resampled masks as independent data."""
    if runs.empty:raise ValueError("No events: cannot evaluate")
    cols=("event_recall","fragmentation_rate","disappearance_rate",
          "mean_lost_reference_days","mean_peak_error_c")
    unit=runs.groupby(["station_id","year","scenario","policy"],as_index=False)[list(cols)].mean()
    rows=[]
    for (scenario,policy),g in unit.groupby(["scenario","policy"],sort=True):
        for metric in cols:
            v=g[metric].dropna()
            estimate=float(v.mean()) if len(v) else np.nan
            stations=sorted(g.station_id.unique())
            cluster_means=g.groupby("station_id")[metric].mean()
            arr=cluster_means.reindex(stations).to_numpy(dtype=float)
            arr=arr[np.isfinite(arr)]
            if len(arr)>=2:
                rng=np.random.default_rng(seed)
                boot=np.array([rng.choice(arr,size=len(arr),replace=True).mean() for _ in range(n_boot)])
                lo,hi=np.percentile(boot,[2.5,97.5])
            else:lo,hi=np.nan,np.nan
            rows.append({"scenario":scenario,"policy":policy,"metric":metric,
                         "estimate":estimate,"station_bootstrap_low":float(lo),
                         "station_bootstrap_high":float(hi),
                         "n_stations":len(stations),"n_station_years":int(g[metric].notna().sum())})
    return pd.DataFrame(rows)

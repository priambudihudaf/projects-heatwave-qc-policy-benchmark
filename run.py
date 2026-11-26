#!/usr/bin/env python3
"""Command-line research workflow; --mode demo produces NO scientific results."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"src"))
from heatqc.noaa import make_demo,load_real,select_stations
from heatqc.core import fit_p90,attach_threshold,find_events
from heatqc.experiment import run_experiments,summarize

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=("demo","real"),default="demo")
    p.add_argument("--stations",type=int,default=12)
    p.add_argument("--reps",type=int,default=30)
    p.add_argument("--start-year",type=int,default=2010)
    p.add_argument("--end-year",type=int,default=2025)
    p.add_argument("--output",default=None)
    args=p.parse_args()
    if args.start_year>2010 or args.end_year<2025:
        raise ValueError("This preregistered pilot requires 2010-2025; do not change the split silently")
    if args.reps<1 or args.stations<1:raise ValueError("stations/reps must be >=1")
    out=Path(args.output) if args.output else HERE/"outputs"/("SYNTHETIC_DEMO_NOT_RESULTS" if args.mode=="demo" else "NOAA_PILOT")
    out.mkdir(parents=True,exist_ok=True)
    if args.mode=="demo":
        obs=make_demo(n_stations=min(args.stations,4))
        inventory=pd.DataFrame()
    else:
        cache=HERE/"data"/"raw"
        # Oversample candidate stations so completeness exclusions do not
        # silently reduce the final target sample unnecessarily.
        names=select_stations(cache,args.stations+max(3,args.stations//2),args.start_year,args.end_year)
        obs,inventory=load_real(names,args.start_year,args.end_year,cache)
        inventory.to_csv(out/"source_manifest.csv",index=False)
    obs=obs[(obs.date.dt.year>=2010)&(obs.date.dt.year<=2025)].copy()
    obs=obs.sort_values(["station_id","date"])
    # Never compare discontinuous station series without inserting explicit missing dates.
    frames=[]
    for station,sub in obs.groupby("station_id"):
        full=pd.DataFrame({"date":pd.date_range("2010-01-01","2025-12-31")})
        re=full.merge(sub,on="date",how="left",validate="one_to_one")
        re["station_id"]=station
        frames.append(re)
    obs=pd.concat(frames,ignore_index=True)
    keep=[];thresholds={};caps={};report=[]
    for station,sub in obs.groupby("station_id"):
        train=sub[sub.date.dt.year.between(2010,2020)]
        val=sub[sub.date.dt.year.between(2021,2022)]
        tst=sub[sub.date.dt.year.between(2023,2025)]
        heat=lambda f:f[f.date.dt.month.isin([5,6,7,8,9])]
        completeness=[heat(x).tmax_c.notna().mean() for x in [train,val,tst]]
        report.append({"station_id":station,"train_coverage":completeness[0],
                       "validation_coverage":completeness[1],"test_coverage":completeness[2]})
        if min(completeness)<0.95:
            print(f"EXCLUDE {station}: seasonal completeness={completeness}")
            continue
        thresholds[station]=fit_p90(train)
        caps[station]=float(np.nanpercentile(train.tmax_c,99.5))
        if len(keep)<args.stations:
            keep.append(station)
    pd.DataFrame(report).to_csv(out/"coverage_audit.csv",index=False)
    if len(keep)<2:
        raise ValueError(f"Only {len(keep)} stations pass >=95% seasonal completeness; adjust candidates, never lower threshold silently")
    test=obs[obs.station_id.isin(keep)&obs.date.dt.year.between(2023,2025)].copy()
    ref_rows=[]
    for (sid,year),g in test.groupby(["station_id",test.date.dt.year]):
        e=find_events(attach_threshold(g,thresholds[sid]))
        for event in e:
            ref_rows.append({"station_id":sid,"year":year,"start":event.start,
                             "end":event.end,"duration":event.duration,"peak_c":event.peak_c})
    events=pd.DataFrame(ref_rows)
    if events.empty:raise ValueError("No reference heatwaves in test")
    events.to_csv(out/"reference_heatwaves.csv",index=False)
    runs=run_experiments(test,thresholds,caps,reps=args.reps)
    runs.to_csv(out/"replicate_results.csv",index=False)
    summ=summarize(runs)
    summ.to_csv(out/"summary_station_bootstrap.csv",index=False)
    for metric,filename in [("event_recall","figure_event_recall.png"),
                            ("fragmentation_rate","figure_fragmentation.png"),
                            ("disappearance_rate","figure_disappearance.png")]:
        sel=summ[summ.metric==metric]
        pivot=sel.pivot(index="scenario",columns="policy",values="estimate")
        ax=pivot.plot(kind="bar",figsize=(12,4.5),rot=25)
        ax.set_ylabel(metric.replace("_"," ").title())
        ax.set_xlabel("Synthetic intervention scenario")
        ax.set_title("SYNTHETIC SOFTWARE DEMO - NOT SCIENTIFIC RESULTS" if args.mode=="demo" else "NOAA CONTROLLED EXPERIMENT (NOT OBSERVED NOAA QC ACTIONS)")
        ax.legend(title="Analysis policy")
        plt.tight_layout();plt.savefig(out/filename,dpi=160);plt.close()
    meta={"mode":args.mode,"warning":"DEMO IS FULLY SYNTHETIC" if args.mode=="demo" else "NOAA DAILY01 ALREADY QC-SCREENED; FLAGS AND ERRORS ARE SYNTHETIC",
      "stations_used":keep,"n_reference_events":len(events),"n_simulation_rows":len(runs),
      "start_year":2010,"end_year":2025,"train_years":"2010-2020","validation_years":"2021-2022",
      "test_years":"2023-2025","heatwave":"P90 +/-7 calendar days, > threshold, >=3 consecutive May-Sep days",
      "policies":["preserve","remove","cap"],"cap":"station-specific train P99.5, on flagged values only",
      "seed":20261126,"reps":args.reps,
      "limitations":["Provider QC-passed does not equal verified ground truth",
         "Synthetic QC flags are not NOAA operational QC flags",
         "Simulated cases reuse reference events; replicates are not independent heatwaves",
         "Station-level bootstrap cannot remove geographic dependence",
         "Missing values break events; no interpolation",
         "Study needs stronger novelty check before preprint submission"]}
    (out/"run_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    print(f"{args.mode.upper()}: {len(keep)} stations, {len(events)} reference heatwaves, {len(runs)} replicate policy evaluations")
    print(f"Results: {out}")

if __name__=="__main__":main()

#!/usr/bin/env python3
"""Run v2 controlled review-prioritization benchmark.

No NOAA operational QC labels are available. Downloaded public USCRN Daily01
is used only as a provider-screened reference. Synthetic errors/flag masks,
plus oracle reviewer adjudication, make this a controlled sensitivity study.
"""
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
from heatqc.noaa import make_demo, select_stations, load_real
from heatqc.core import fit_p90
from heatqc.review_v2 import run_review_benchmark, paired_effects, REGIMES, BUDGETS

def prepare(args,out):
    if args.mode=="demo":
        raw=make_demo(n_stations=min(args.stations,4))
    else:
        candidate_count=args.stations+max(3,args.stations//2)
        cache=HERE/"data"/"raw"
        names=select_stations(cache,candidate_count,2010,2025)
        raw,inventory=load_real(names,2010,2025,cache)
        inventory.to_csv(out/"source_manifest.csv",index=False)
    prepared=[]
    for station,group in raw.groupby("station_id"):
        dates=pd.DataFrame({"date":pd.date_range("2010-01-01","2025-12-31",freq="D")})
        full=dates.merge(group,on="date",how="left",validate="one_to_one")
        full["station_id"]=station
        prepared.append(full)
    all_data=pd.concat(prepared,ignore_index=True)
    keep=[]; thresholds={}; audit=[]
    for station,group in all_data.groupby("station_id",sort=True):
        periods={
            "train":group.date.dt.year.between(2010,2020),
            "validation":group.date.dt.year.between(2021,2022),
            "test":group.date.dt.year.between(2023,2025)}
        warm=group.date.dt.month.isin([5,6,7,8,9])
        coverage={name:float(group.loc[mask&warm,"tmax_c"].notna().mean())
                  for name,mask in periods.items()}
        eligible=all(x>=0.95 for x in coverage.values())
        audit.append({"station_id":station,**{f"{x}_coverage":v for x,v in coverage.items()},"eligible":eligible})
        if eligible and len(keep)<args.stations:
            thresholds[station]=fit_p90(group[periods["train"]])
            keep.append(station)
    pd.DataFrame(audit).to_csv(out/"coverage_audit.csv",index=False)
    if len(keep)<2:
        raise ValueError(f"Only {len(keep)} stations have >=95% warm-season coverage in train/validation/test")
    test=all_data[(all_data.station_id.isin(keep))&all_data.date.dt.year.between(2023,2025)].copy()
    return test,thresholds,keep

def plot_results(effects:pd.DataFrame,out:Path,mode:str):
    metric="event_distortion_count"
    data=effects[(effects.metric==metric)&(effects.comparison=="event_impact vs random")]
    fig,ax=plt.subplots(figsize=(9,5))
    for (regime,min_len),g in data.groupby(["regime","min_length"]):
        g=g.sort_values("review_budget")
        ax.errorbar(g.review_budget,g.paired_gain,
                    yerr=np.vstack((np.maximum(0,g.paired_gain-g.ci95_low),
                                    np.maximum(0,g.ci95_high-g.paired_gain))),
                    marker="o",capsize=3,label=f"{regime}, min days {min_len}")
    ax.axhline(0,linewidth=1,linestyle="--")
    ax.set(xlabel="Fraction of flagged observations reviewed",
           ylabel="Paired reduction in event distortion vs random\n(positive = better; station-year scale)",
           title=("SYNTHETIC-ONLY DEMO — NOT SCIENTIFIC RESULTS" if mode=="demo"
                  else "NOAA QC-SCREENED REFERENCE + SYNTHETIC FLAGS / ORACLE REVIEW"))
    ax.legend()
    fig.tight_layout()
    fig.savefig(out/"v2_gain_vs_random.png",dpi=160)
    plt.close(fig)
    for min_len in sorted(effects.min_length.unique()):
        ss=effects[(effects.metric==metric)&(effects.min_length==min_len)]
        fig,ax=plt.subplots(figsize=(9,5))
        for (regime,comparison),g in ss.groupby(["regime","comparison"]):
            ax.plot(g.review_budget,g.paired_gain,marker="o",label=f"{regime}: {comparison}")
        ax.axhline(0,linewidth=1,linestyle="--")
        ax.set(xlabel="Review budget",ylabel="Reduction in event distortion vs random",
               title=f"Minimum {min_len} consecutive hot days; controlled scenarios")
        ax.legend(fontsize=8)
        fig.tight_layout();fig.savefig(out/f"v2_comparisons_min{min_len}.png",dpi=160);plt.close(fig)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--mode",choices=["demo","real"],default="demo")
    p.add_argument("--stations",type=int,default=12)
    p.add_argument("--reps",type=int,default=12)
    p.add_argument("--output",type=str,default=None)
    args=p.parse_args()
    if args.reps<=0 or args.stations<2:raise ValueError("reps>=1 and stations>=2 required")
    out=Path(args.output) if args.output else HERE/"outputs"/("V2_DEMO_SYNTHETIC" if args.mode=="demo" else "V2_NOAA_CONTROLLED")
    out.mkdir(parents=True,exist_ok=True)
    test,thresholds,stations=prepare(args,out)
    results=run_review_benchmark(test,thresholds,
                                 regimes=tuple(REGIMES),
                                 budgets=BUDGETS,
                                 min_lengths=(3,6),reps=args.reps)
    if results.empty:raise ValueError("No V2 trials; check thresholds and data coverage")
    results.to_csv(out/"v2_all_trials.csv",index=False)
    effects=paired_effects(results,n_boot=350)
    effects.to_csv(out/"v2_paired_effects.csv",index=False)
    grouped=results.groupby(["regime","min_length","review_budget","strategy"],as_index=False).agg(
        mean_event_distortion=("event_distortion_count","mean"),
        mean_disappeared_events=("disappeared_events","mean"),
        mean_false_events=("unmatched_candidate_events","mean"),
        mean_fragmented_events=("fragmented_events","mean"),
        mean_reviewed=("n_reviewed","mean"),
        n_trials=("replicate","count"))
    grouped.to_csv(out/"v2_descriptive_summary.csv",index=False)
    metadata={
      "mode":args.mode,"stations":stations,"n_stations":len(stations),
      "n_trial_strategy_budget_rows":len(results),"n_replicates_per_station_year_regime":args.reps,
      "regimes":REGIMES,"budgets":BUDGETS,"min_consecutive_hot_days":[3,6],
      "reference":"NOAA USCRN Daily01 QC-screened (NOT validated ground truth)",
      "train":"2010-2020","validation":"2021-2022 (held out; not used for tuning)",
      "test":"2023-2025","season":"May-September", "p90_window":"calendar day +/- 7, training only",
      "random_seed":20261126,
      "counterfactual_reviewer":"perfect ORACLE substitution with NOAA reference value, not realistic human reviewer",
      "flags":"synthetic probabilistic detection conditional on injected error labels; actual error labels never provided to strategies",
      "goal":"equal-budget paired comparison of random/anomaly/event-impact review prioritization",
      "unit_of_uncertainty":"station cluster; repeated trials are dependent",
      "event_distortion_count":"missed reference events + unmatched candidate events + fragmented reference events (equal weight)",
      "caveats":["No NOAA operational QC actions or errors are observed",
                 "No study-level claim about QC practice or institution",
                 "Shared error/flag masks across prioritizers for paired design",
                 "Oracle adjudication is a favorable upper-bound assumption",
                 "Event scoring from contaminated data can be fooled by errors",
                 "Effects may be sensitive to heatwave definition and artificial error distribution",
                 "Event matching uses any overlapping day (diagnostic simplification)",
                 "Novelties and generalizability unconfirmed"]
    }
    (out/"v2_metadata.json").write_text(json.dumps(metadata,indent=2),encoding="utf8")
    plot_results(effects,out,args.mode)
    print(f"V2 {args.mode.upper()}: {len(stations)} stations, {len(results)} paired policy/strategy evaluation rows")
    print("Regimes:",list(REGIMES),"minimum event lengths:",[3,6],
          "budgets:",list(BUDGETS),"strategies: random, anomaly, event_impact")
    print("Outputs:",out)
    p2=effects[(effects.metric=="event_distortion_count")&
               (effects.comparison=="event_impact vs random")]
    print("Exploratory paired effect summary (positive=better vs random):")
    print(p2[["regime","min_length","review_budget","paired_gain","ci95_low","ci95_high"]].to_string(index=False))
    print("These are results of synthetic interventions and ORACLE review, not observed NOAA QC behavior.")

if __name__=="__main__":
    main()

#!/usr/bin/env python3
"""Pilot v2.1 full workflow, independent of the v1 and v2 entry points."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE/"src"))
from run_v2 import prepare
from heatqc.review_v21 import (
    run_v21, paired_effects_v21, STRATEGIES, FALSE_FLAG_PATTERNS,
    REVIEW_RELIABILITIES, REVIEW_BUDGETS, MIN_LENGTHS, IOU_THRESHOLDS,
    METRICS, COMPARISONS
)

def main():
    ap=argparse.ArgumentParser(description="Pilot v2.1 controlled review-priority research experiment")
    ap.add_argument("--mode",choices=("demo","real"),default="demo")
    ap.add_argument("--stations",type=int,default=12)
    ap.add_argument("--reps",type=int,default=6)
    ap.add_argument("--bootstrap",type=int,default=300)
    ap.add_argument("--output")
    args=ap.parse_args()
    if args.stations < 2 or args.reps<1 or args.bootstrap<20:
        raise ValueError("stations >=2, reps >=1 and bootstrap >=20 required")
    out=(Path(args.output) if args.output else HERE/"outputs"/
         ("V21_DEMO_SYNTHETIC" if args.mode=="demo" else "V21_NOAA_CONTROLLED"))
    out.mkdir(parents=True,exist_ok=True)

    test,thresholds,stations=prepare(args,out)
    trials=run_v21(test,thresholds,reps=args.reps)
    if trials.empty: raise ValueError("No review trials generated")
    trials.to_csv(out/"v21_trials.csv",index=False)
    pairs=paired_effects_v21(trials,n_boot=args.bootstrap)
    if pairs.empty:raise ValueError("No paired comparisons generated")
    pairs.to_csv(out/"v21_paired_effects.csv",index=False)

    grp=["detector_regime","fp_placement","min_length","review_budget",
         "review_reliability","iou_threshold","strategy"]
    summary=trials.groupby(grp,as_index=False).agg(
        n_trials=("replicate","size"),
        mean_event_distortion=("event_distortion_count","mean"),
        mean_missed_events=("missed_events","mean"),
        mean_unmatched_events=("unmatched_events","mean"),
        mean_fragmented_events=("fragmented_events","mean"),
        mean_missed_hot_days=("missed_reference_hot_days","mean"),
        mean_extra_hot_days=("extra_candidate_hot_days","mean"),
        mean_reviewed_errors=("n_reviewed_errors","mean"),
        mean_corrected_errors=("n_corrected_errors","mean"),
        mean_n_reviewed=("n_reviewed","mean"),
        mean_n_hot_false_flags=("n_hot_false_flags","mean"))
    summary.to_csv(out/"v21_descriptive_summary.csv",index=False)

    # Paired effects + station/bootstrap CI: plot comparisons for the
    # designated primary v2.1 analysis (not prospectively preregistered) (3-day heatwave, IoU>=0.5, 25% review).
    comp=pairs[
        (pairs.sample_subset=="all") &
        (pairs.metric=="event_distortion_count") &
        (pairs.min_length==3) &
        (pairs.iou_threshold==0.50) &
        (pairs.review_budget==0.25) &
        (pairs.comparison.isin(("event_impact vs anomaly",
                               "event_impact vs hot_run",
                               "event_impact vs threshold_proximity")))]
    fig,axes=plt.subplots(1,2,figsize=(13,5),sharey=True)
    for ax,(placement,sub) in zip(axes,comp.groupby("fp_placement",sort=True)):
        for compname,g in sub.groupby("comparison",sort=True):
            for det,part in g.groupby("detector_regime",sort=True):
                part=part.sort_values("review_reliability")
                label=f"{compname.replace('event_impact vs ','vs ')} ({det})"
                ax.plot(part.review_reliability,part.paired_gain,marker="o",label=label)
        ax.axhline(0,linestyle="--",linewidth=1)
        ax.set_xlabel("Simulated reviewer reliability")
        ax.set_title(f"False-flag placement: {placement}")
    axes[0].set_ylabel("Paired gain: avoided event distortions per station-year\n(positive favors event-impact)")
    axes[1].legend(fontsize=7,loc="best")
    fig.suptitle("SYNTHETIC QC FLAGS + REVIEW; NOT OBSERVED NOAA QC PERFORMANCE")
    fig.tight_layout()
    fig.savefig(out/"v21_eventimpact_gain_robustness.png",dpi=170)
    plt.close(fig)

    fig,ax=plt.subplots(figsize=(10,5))
    primary=summary[
        (summary.detector_regime=="balanced") &
        (summary.min_length==3) &
        (summary.iou_threshold==0.50) &
        (summary.review_budget==0.25) &
        (summary.review_reliability==0.90)]
    table=primary.pivot(index="strategy",columns="fp_placement",values="mean_event_distortion")
    table=table.reindex(STRATEGIES)
    table.plot(kind="bar",rot=12,ax=ax)
    ax.set_ylabel("Mean event distortion count per trial")
    ax.set_title("NOAA reference + synthetic flags/errors (balanced, reviewer 90%, IoU 0.50)")
    fig.tight_layout()
    fig.savefig(out/"v21_strategy_comparison.png",dpi=170)
    plt.close(fig)

    meta={
        "version":"2.1","mode":args.mode,"warning":"EXPERIMENTAL, NOT NOAA OBSERVED QC DATA",
        "stations":stations,"n_stations":len(stations),"n_rows":len(trials),
        "n_reps":args.reps,"bootstrap_samples":args.bootstrap,
        "training":"2010-2020","validation":"2021-2022 reserved (NOT used for tuning)",
        "evaluation_period":"2023-2025 (exploratory; reused during v1-v2.1 method development)","variable":"NOAA USCRN Daily01 Tmax QC-screened proxy",
        "synthetic_detector_regimes":["balanced","noisy"],
        "synthetic_fp_placements":list(FALSE_FLAG_PATTERNS),
        "reviewer_success_rates":list(REVIEW_RELIABILITIES),
        "review_budgets":list(REVIEW_BUDGETS),
        "event_min_lengths":list(MIN_LENGTHS),
        "event_iou_thresholds":list(IOU_THRESHOLDS),
        "review_strategies":list(STRATEGIES),
        "metric_primary":"missed ref events + unmatched candidate events + fragmented ref events",
        "comparison_sign":"baseline mean minus proposed method mean; positive indicates proposed method fewer distortions; corrected-error counts have opposite preference",
        "event_matching":"Hungarian maximum-weight 1-to-1 on day IoU, thresholded",
        "review_failures":"failed reviewed flags remain missing; successful reviews restore reference value exactly (ideal oracle on success)",
        "label_blinding":"selection strategies see only corrupted Tmax, simulated flags, and train-only thresholds",
        "same_false_positive_count_across_placements":True,
        "same_true_positive_flags_across_placements":True,
        "random_seed":20261126,
        "limitations":[
            "All QC flags, sensor errors and review success decisions are simulated; not observations of NOAA operations",
            "Public NOAA Daily01 is already QC-screened and may itself contain errors",
            "Injected-error prevalence is deliberately high relative to unverified real operations",
            "A success event means perfect reference restoration, an optimistic idealization",
            "Proposed strategy uses heatwave topology; primary metric also focuses on heatwave topology",
            "12 geographically related stations do not provide independent universal generalization",
            "Station-cluster bootstrap is exploratory; repeated trials are dependent",
            "At least 2025-2026 novelty overlap, alternative baselines, and explicit publication approvals remain"
        ]
    }
    (out/"v21_metadata.json").write_text(json.dumps(meta,indent=2),encoding="utf-8")
    pick=pairs[(pairs.metric=="event_distortion_count") &
         (pairs.sample_subset=="all") & (pairs.comparison=="event_impact vs anomaly") &
         (pairs.min_length==3)&(pairs.iou_threshold==0.5)&(pairs.review_budget==0.25)]
    print(f"V2.1 {args.mode.upper()}: {len(stations)} stations; {len(trials)} strategy/evaluation rows")
    print("Output:",out)
    print("Core paired gains: event-impact vs anomaly, min3, IoU0.5, 25% review")
    print(pick[["detector_regime","fp_placement","review_reliability",
        "paired_gain","ci95_low","ci95_high","n_stations"]].to_string(index=False))
    print("WARNING: all errors, flags and reviewer actions are simulated.")

if __name__=="__main__":
    main()

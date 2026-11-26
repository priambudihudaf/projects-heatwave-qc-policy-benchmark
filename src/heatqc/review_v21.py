"""Pilot v2.1: stress tests for event-impact-aware QC review prioritization.

DATA BOUNDARY: NOAA USCRN Daily01 is a public, provider-QC-screened reference
proxy, not validated ground truth. Errors, candidate QC flags, and reviewer
outcomes are entirely SYNTHETIC. Review prioritizers do not see injected-error
labels or reference values; an imperfect oracle uses those labels only after
a review decision is made.

This is exploratory research software, NOT operational meteorological QC.
"""
from __future__ import annotations
import math
from typing import Iterable
import numpy as np
import pandas as pd
from scipy.optimize import linear_sum_assignment
from .core import attach_threshold, find_events
from .review_v2 import stable_seed, simulate_trial, REGIMES, score_candidates, _neighbor_median_deviation

STRATEGIES = ("random", "anomaly", "threshold_proximity", "hot_run", "event_impact")
FALSE_FLAG_PATTERNS = ("uniform", "hot_enriched")
REVIEW_RELIABILITIES = (0.70, 0.90, 1.00)
REVIEW_BUDGETS = (0.10, 0.25, 0.50)
MIN_LENGTHS = (3, 6)
IOU_THRESHOLDS = (0.25, 0.50)

def synthetic_flags(contaminated: pd.DataFrame, error_mask: np.ndarray,
                    regime: str, placement: str, tp_random: np.ndarray,
                    rng_fp: np.random.Generator) -> np.ndarray:
    """Controlled FP count and identical TP flags across FP-placement regimes.

    Uniform: false flags sampled uniformly among warm-season error-free dates.
    Hot enriched: SAME number of false flags, sampled with 6x higher weight
    on *observed hot* dates. Thus FP concentration, not FP count, changes.
    """
    if placement not in FALSE_FLAG_PATTERNS: raise ValueError(placement)
    if regime not in REGIMES: raise ValueError(regime)
    p=REGIMES[regime]
    obs=contaminated.tmax_c.to_numpy(dtype=float)
    valid=(contaminated.date.dt.month.isin((5,6,7,8,9)).to_numpy() & np.isfinite(obs))
    error_mask=np.asarray(error_mask,dtype=bool)
    if len(tp_random)!=len(obs): raise ValueError("TP random array length mismatch")
    true_positive = valid & error_mask & (tp_random < p["true_positive_rate"])
    candidates=np.flatnonzero(valid & ~error_mask)
    k=min(len(candidates), int(round(p["false_positive_rate"]*len(candidates))))
    flags=true_positive.copy()
    if k:
        weights=np.ones(len(candidates),dtype=float)
        if placement=="hot_enriched":
            hot=obs[candidates]>contaminated.heat_threshold_c.to_numpy(dtype=float)[candidates]
            weights[hot]=6.0
        weights=weights/weights.sum()
        chosen=rng_fp.choice(candidates,size=k,replace=False,p=weights)
        flags[chosen]=True
    return flags

def strong_baseline_scores(contaminated:pd.DataFrame,flags:np.ndarray,
                           min_length:int)->dict[str,np.ndarray]:
    """Rank scores depend on observed temperatures and training-set thresholds only.

    No access to clean reference temperatures, reference heatwave events,
    synthetic errors, or reviewer outcome draws.
    """
    indices=np.flatnonzero(np.asarray(flags,dtype=bool))
    out={"threshold_proximity":np.zeros(len(indices)),
         "hot_run":np.zeros(len(indices))}
    if not len(indices):return out
    obs=contaminated.tmax_c.to_numpy(dtype=float)
    threshold=contaminated.heat_threshold_c.to_numpy(dtype=float)
    valid=(np.isfinite(obs)&np.isfinite(threshold)&
           contaminated.date.dt.month.isin((5,6,7,8,9)).to_numpy())
    above=valid&(obs>threshold)
    left=np.zeros(len(obs),dtype=int)
    right=np.zeros(len(obs),dtype=int)
    dates=pd.DatetimeIndex(contaminated.date)
    for i in range(len(obs)):
        if above[i]:
            left[i]=1+(left[i-1] if i>0 and (dates[i]-dates[i-1]).days==1 else 0)
    for i in range(len(obs)-1,-1,-1):
        if above[i]:
            right[i]=1+(right[i+1] if i+1<len(obs) and (dates[i+1]-dates[i]).days==1 else 0)
    for k,i in enumerate(indices):
        if valid[i]:
            delta=abs(obs[i]-threshold[i])
            out["threshold_proximity"][k]=1.0/(1.0+delta)
            # Continuous, observed hot-run length; for non-hot dates use zero.
            out["hot_run"][k] = float(left[i]+right[i]-1) if above[i] else 0.0
    return out

def rank_strategies(contaminated:pd.DataFrame,flags:np.ndarray,min_length:int,
                    rng:np.random.Generator)->dict[str,np.ndarray]:
    candidates=np.flatnonzero(np.asarray(flags,dtype=bool))
    if not len(candidates):return {x:candidates.copy() for x in STRATEGIES}
    # Reuse exactly the v2 event-impact score: comparison with v2 is traceable.
    original=score_candidates(contaminated,flags,min_length=min_length)
    stronger=strong_baseline_scores(contaminated,flags,min_length)
    scores={**original,**stronger}
    tie=rng.random(len(candidates))
    ranked={"random":rng.permutation(candidates)}
    for strategy in STRATEGIES[1:]:
        vals=np.asarray(scores[strategy],dtype=float)
        ranked[strategy]=candidates[np.lexsort((tie,-vals))]
    return ranked

def reviewed_series(reference:pd.DataFrame,contaminated:pd.DataFrame,
                    flags:np.ndarray,reviewed:np.ndarray,
                    reviewer_success:np.ndarray) -> pd.DataFrame:
    """Failed review leaves the value missing, rather than inventing a correction.

    A successful simulated review restores provider-screened REFERENCE exactly.
    This is still an ideal oracle-on-success assumption, NOT an empirical model
    of expert observers. Nonflagged injected errors remain untouched.
    """
    if not len(reference)==len(contaminated)==len(flags)==len(reviewer_success):
        raise ValueError("Mismatched series length")
    flagged=np.asarray(flags,dtype=bool)
    reviewed=np.asarray(reviewed,dtype=int)
    if reviewed.size and (reviewed.min()<0 or reviewed.max()>=len(flagged) or
                          not flagged[reviewed].all()):
        raise ValueError("Can review only flagged indices")
    d=contaminated.copy()
    d.loc[flagged,"tmax_c"]=np.nan
    successful=reviewed[np.asarray(reviewer_success,dtype=bool)[reviewed]]
    if len(successful):
        d.loc[successful,"tmax_c"]=reference.iloc[successful].tmax_c.to_numpy(dtype=float)
    return d

def iou_event_metrics(ref_events:list,obs_events:list,iou_min:float)->dict:
    """Maximum-weight ONE-TO-ONE event matching using day-set intersection/union.

    Matching score is intersection over union (IoU), thresholded at iou_min.
    Splits (1 ref -> >=2 overlapping output runs) and merges are separately
    diagnosed using ANY day overlap, independent of strict matching.
    """
    if not 0 < iou_min <= 1:raise ValueError("IoU threshold must be in (0,1]")
    nr,no=len(ref_events),len(obs_events)
    ref=[set(x.days) for x in ref_events]
    ob=[set(x.days) for x in obs_events]
    iou=np.zeros((nr,no),dtype=float)
    overlap=np.zeros((nr,no),dtype=int)
    for a,r in enumerate(ref):
        for b,o in enumerate(ob):
            intersection=len(r&o)
            overlap[a,b]=intersection
            if intersection:
                iou[a,b]=intersection/len(r|o)
    pairs=[]
    if nr and no:
        # Global optimal assignment, not greedy chronological matching.
        row,col=linear_sum_assignment(-np.where(iou>=iou_min,iou,0.0))
        pairs=[(int(a),int(b)) for a,b in zip(row,col) if iou[a,b]>=iou_min]
    missed=nr-len(pairs)
    unmatched=no-len(pairs)
    split=int(sum(np.count_nonzero(overlap[a,:])>1 for a in range(nr)))
    merged=int(sum(np.count_nonzero(overlap[:,b])>1 for b in range(no)))
    refdays=set().union(*ref) if nr else set()
    obdays=set().union(*ob) if no else set()
    duration=[abs(ref_events[a].duration-obs_events[b].duration) for a,b in pairs]
    peak=[abs(ref_events[a].peak_c-obs_events[b].peak_c) for a,b in pairs]
    return {
        "reference_events":nr,"candidate_events":no,"matched_events":len(pairs),
        "missed_events":missed,"unmatched_events":unmatched,
        "fragmented_events":split,"merged_events":merged,
        "missed_reference_hot_days":len(refdays-obdays),
        "extra_candidate_hot_days":len(obdays-refdays),
        "mean_abs_duration_error":float(np.mean(duration)) if duration else np.nan,
        "mean_abs_peak_error_c":float(np.mean(peak)) if peak else np.nan,
        "event_distortion_count":int(missed+unmatched+split)
    }

def run_v21(test:pd.DataFrame,thresholds:dict,reps:int=6,seed:int=20261126,
            regimes:Iterable[str]=tuple(REGIMES),
            placements=FALSE_FLAG_PATTERNS,
            reliabilities=REVIEW_RELIABILITIES,
            budgets=REVIEW_BUDGETS,
            lengths=MIN_LENGTHS,
            ious=IOU_THRESHOLDS)->pd.DataFrame:
    """Within each scenario, scores share corrupted data/flags and review outcomes.

    For each injection, both FP-placement regimes use identical injected errors,
    TP flags, FP count and reviewer draw arrays. Each algorithm has identical
    flags and budget, and each reliability shares monotone reviewer draws.
    """
    rows=[]
    for (station,year),sub in test.groupby(["station_id",test.date.dt.year],sort=True):
        d=attach_threshold(sub.sort_values("date").reset_index(drop=True),thresholds[station])
        for rep in range(reps):
            for regime in regimes:
                rng=np.random.default_rng(stable_seed(station,year,rep,regime,"errors",seed=seed))
                trial=simulate_trial(d,rng,regime)
                if trial is None:continue
                contaminated,_,error_mask=trial
                tp_random=np.random.default_rng(stable_seed(station,year,rep,regime,"tp",seed=seed)).random(len(d))
                reviewer_random=np.random.default_rng(stable_seed(station,year,rep,regime,"review",seed=seed)).random(len(d))
                for placement in placements:
                    flags=synthetic_flags(
                        contaminated,error_mask,regime,placement,tp_random,
                        np.random.default_rng(stable_seed(station,year,rep,regime,placement,"fp",seed=seed)))
                    nflag=int(flags.sum())
                    if nflag<2:continue
                    for min_length in lengths:
                        reference_events=find_events(d,min_length=min_length)
                        ranks=rank_strategies(contaminated,flags,min_length,
                            np.random.default_rng(stable_seed(station,year,rep,regime,placement,min_length,"rank",seed=seed)))
                        for budget in budgets:
                            n_review=min(nflag,int(math.ceil(nflag*budget)))
                            for reliability in reliabilities:
                                reviewer_success=reviewer_random<float(reliability)
                                for strategy,order in ranks.items():
                                    reviewed=order[:n_review]
                                    repaired=reviewed_series(d,contaminated,flags,reviewed,reviewer_success)
                                    observed_events=find_events(repaired,min_length=min_length)
                                    for iou in ious:
                                        metric=iou_event_metrics(reference_events,observed_events,float(iou))
                                        rows.append({
                                            "station_id":station,"year":int(year),
                                            "replicate":rep,"detector_regime":regime,
                                            "fp_placement":placement,
                                            "min_length":int(min_length),
                                            "review_budget":float(budget),
                                            "review_reliability":float(reliability),
                                            "iou_threshold":float(iou),
                                            "strategy":strategy,
                                            "n_flagged":nflag,"n_reviewed":n_review,
                                            "n_injected_errors":int(error_mask.sum()),
                                            "n_true_positive_flags":int((flags&error_mask).sum()),
                                            "n_false_positive_flags":int((flags&~error_mask).sum()),
                                            "n_false_negative_errors":int((error_mask&~flags).sum()),
                                            "n_hot_false_flags":int(((flags&~error_mask)&
                                                (contaminated.tmax_c.to_numpy(dtype=float)>
                                                 d.heat_threshold_c.to_numpy(dtype=float))).sum()),
                                            "n_reviewed_errors":int(error_mask[reviewed].sum()),
                                            "n_review_successes":int(reviewer_success[reviewed].sum()),
                                            "n_corrected_errors":int((reviewer_success[reviewed]&error_mask[reviewed]).sum()),
                                            **metric
                                        })
    return pd.DataFrame(rows)

METRICS=("event_distortion_count","missed_events","unmatched_events",
         "fragmented_events","missed_reference_hot_days","extra_candidate_hot_days",
         "n_corrected_errors")
COMPARISONS=(("random","event_impact"),("anomaly","event_impact"),
             ("hot_run","event_impact"),("threshold_proximity","event_impact"),
             ("random","anomaly"))

def paired_effects_v21(runs:pd.DataFrame,n_boot:int=300,seed:int=1504)->pd.DataFrame:
    """Paired gain = mean(baseline metric - comparator metric) by station-year.

    For quality-loss metrics positive favors comparator. For n_corrected_errors
    positive instead means comparator corrected FEWER errors; interpret carefully.
    Values use equal station-year weighting; bootstrap clusters by station.
    Two sample subsets: all station-years, and those with >=1 reference event.
    """
    if runs.empty:raise ValueError("No v2.1 rows")
    unit=["station_id","year","replicate","detector_regime","fp_placement",
          "min_length","review_budget","review_reliability","iou_threshold"]
    pivot=runs.pivot(index=unit,columns="strategy",values=list(METRICS)+["reference_events"])
    rows=[]
    for baseline,comp in COMPARISONS:
        for metric in METRICS:
            if (metric,baseline) not in pivot or (metric,comp) not in pivot:continue
            paired=pd.DataFrame({
                "delta":pivot[(metric,baseline)]-pivot[(metric,comp)],
                "ref_events":pivot[("reference_events",baseline)]
            }).reset_index()
            for subset in ("all","reference_event_present"):
                part=paired if subset=="all" else paired[paired.ref_events>0]
                for keys,g in part.groupby(["detector_regime","fp_placement","min_length",
                                            "review_budget","review_reliability","iou_threshold"],sort=True):
                    per_stationyear=g.groupby(["station_id","year"],as_index=False).delta.mean()
                    per_stationyear=per_stationyear[np.isfinite(per_stationyear.delta)]
                    if per_stationyear.empty:continue
                    point=float(per_stationyear.delta.mean())
                    station_means=per_stationyear.groupby("station_id").delta.mean().to_numpy(dtype=float)
                    if len(station_means)>=2:
                        rg=np.random.default_rng(stable_seed(*keys,baseline,comp,metric,subset,seed=seed))
                        samples=rg.integers(0,len(station_means),size=(n_boot,len(station_means)))
                        boot=station_means[samples].mean(axis=1)
                        lo,hi=np.quantile(boot,[.025,.975])
                    else:lo,hi=np.nan,np.nan
                    regime,placement,min_len,budget,reliability,iou=keys
                    rows.append({
                        "detector_regime":regime,"fp_placement":placement,
                        "min_length":int(min_len),"review_budget":float(budget),
                        "review_reliability":float(reliability),"iou_threshold":float(iou),
                        "sample_subset":subset,"metric":metric,"comparison":f"{comp} vs {baseline}",
                        "paired_gain":point,"ci95_low":float(lo),"ci95_high":float(hi),
                        "n_stations":len(station_means),
                        "n_station_years":len(per_stationyear)
                    })
    return pd.DataFrame(rows)

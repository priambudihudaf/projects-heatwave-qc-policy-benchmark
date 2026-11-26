"""Pilot v2: simulated triage of QC-flagged observations for heatwave integrity.

No historical NOAA flags, no verified observation truth and no operational
review process are claimed. Scores use only the corrupted observed series,
simulated flags and thresholds fit on training years. A simulated reviewed item
is adjudicated by an *oracle* (the original reference value); this is a
deliberately optimistic diagnostic of review-priority choices.
"""
from __future__ import annotations
import hashlib
import math
import numpy as np
import pandas as pd
from .core import find_events, event_metrics

REGIMES = {
    "balanced": {"true_positive_rate": 0.85, "false_positive_rate": 0.04, "hot_false_positive_extra": 0.06},
    "noisy": {"true_positive_rate": 0.65, "false_positive_rate": 0.09, "hot_false_positive_extra": 0.09},
}
STRATEGIES = ("random", "anomaly", "event_impact")
BUDGETS = (0.10, 0.25, 0.50)

def stable_seed(*parts, seed: int = 20261126) -> int:
    val = "|".join(map(str, (seed, *parts))).encode("utf8")
    return int.from_bytes(hashlib.sha256(val).digest()[:8], "little") % (2**32)

def _events(df: pd.DataFrame, min_length: int):
    return find_events(df, min_length=min_length)

def simulate_trial(reference: pd.DataFrame, rng: np.random.Generator, regime: str):
    """Controlled, mixed-sign errors and *synthetic* candidate flags.

    Error injection targets ordinary and hot days using observed TRAIN-based
    P90 (not future reference events). A simulated-flag generator uses labels
    to set target TPR/FPR, but prioritizers do not receive those labels.
    """
    if regime not in REGIMES:
        raise ValueError(f"Unknown regime {regime}")
    d = reference.sort_values("date").reset_index(drop=True).copy()
    obs = d.tmax_c.to_numpy(dtype=float).copy()
    valid = d.date.dt.month.isin((5, 6, 7, 8, 9)).to_numpy() & np.isfinite(obs)
    hot = valid & (obs > d.heat_threshold_c.to_numpy(dtype=float))
    hot_idx = np.flatnonzero(hot)
    other_idx = np.flatnonzero(valid & ~hot)
    if len(other_idx) < 8 or len(hot_idx) < 3:
        return None

    # Errors occur both within/outside hot days; use positive and negative
    # spikes, plus a short persistent offset where contiguous valid days exist.
    picked_hot = rng.choice(hot_idx, size=min(3, len(hot_idx)), replace=False)
    picked_other = rng.choice(other_idx, size=min(4, len(other_idx)), replace=False)
    seeds = [int(x) for x in np.concatenate([picked_hot, picked_other])]
    rng.shuffle(seeds)
    error_mask = np.zeros(len(d), dtype=bool)
    for k, ix in enumerate(seeds):
        magnitude = float(rng.choice((4.0, 6.0, 9.0)))
        sign = 1.0 if k % 2 == 0 else -1.0
        # Several multi-day offsets, no leap over missing dates or seasons.
        affected = [ix]
        if k in (1, 4):
            for j in (ix + 1, ix + 2):
                if j < len(d) and valid[j] and (d.date.iloc[j] - d.date.iloc[ix]).days == j - ix:
                    affected.append(j)
        for j in affected:
            obs[j] = reference.tmax_c.iloc[j] + sign*magnitude
            error_mask[j] = True
    contaminated = d.copy()
    contaminated["tmax_c"] = obs

    p = REGIMES[regime]
    draws = rng.random(len(d))
    # The flag generator is a controlled probabilistic detector model, not a
    # deployable detector. Hot extra FP probability is based on OBSERVED Tmax.
    observed_hot = valid & (obs > d.heat_threshold_c.to_numpy(dtype=float))
    prob = np.where(error_mask, p["true_positive_rate"],
        p["false_positive_rate"] + p["hot_false_positive_extra"]*observed_hot)
    flags = valid & (draws < prob)
    # Require enough items for fair budget comparisons.
    if int(flags.sum()) < 3: return None
    return contaminated, flags, error_mask

def _neighbor_median_deviation(obs: np.ndarray, ix: int) -> float:
    j0, j1 = max(0, ix-3), min(len(obs), ix+4)
    neighbors = np.concatenate((obs[j0:ix], obs[ix+1:j1]))
    neighbors = neighbors[np.isfinite(neighbors)]
    if len(neighbors) < 2: return 0.0
    return float(abs(obs[ix] - np.median(neighbors)))

def score_candidates(contaminated: pd.DataFrame, flags: np.ndarray,
                     min_length: int = 3) -> dict[str, np.ndarray]:
    """Scores do not accept reference events, error mask, or true values."""
    flag = np.asarray(flags, dtype=bool)
    if len(flag) != len(contaminated): raise ValueError("QC flag length mismatch")
    candidates = np.flatnonzero(flag)
    n = len(candidates)
    anomaly = np.zeros(n,dtype=float)
    event_impact = np.zeros(n,dtype=float)
    if not n: return {"anomaly": anomaly,"event_impact":event_impact}

    obs = contaminated.tmax_c.to_numpy(dtype=float)
    raw_events = _events(contaminated, min_length=min_length)

    def descriptors(events):
        return (len(events),
                sum(x.duration for x in events),
                max((x.duration for x in events), default=0))
    n0, days0, longest0 = descriptors(raw_events)

    for k,ix in enumerate(candidates):
        anomaly[k] = _neighbor_median_deviation(obs, int(ix))
        altered = contaminated.copy()
        altered.loc[ix, "tmax_c"] = np.nan
        e = _events(altered, min_length=min_length)
        ne, days, longest = descriptors(e)
        # A one-day removal's counterfactual effect is estimable using only
        # already-observed values; this is not oracle heatwave truth.
        event_impact[k] = (3*abs(n0-ne) + abs(days0-days) +
                           0.5*abs(longest0-longest))
        # Local hot-day context distinguishes near-ties; tiny anomaly tie-break.
        threshold = contaminated.heat_threshold_c.to_numpy(dtype=float)
        hot = np.isfinite(obs) & (obs > threshold)
        neighbors = sum(bool(hot[j]) for j in (ix-1,ix+1)
                        if 0<=j<len(obs) and abs((contaminated.date.iloc[j]-contaminated.date.iloc[ix]).days)==1)
        event_impact[k] += 0.02*neighbors + 1.e-5*anomaly[k]
    return {"anomaly":anomaly,"event_impact":event_impact}

def ranked_indices(flags: np.ndarray, scores: dict[str,np.ndarray],
                   rng: np.random.Generator) -> dict[str,np.ndarray]:
    candidates = np.flatnonzero(np.asarray(flags,dtype=bool))
    # Ties random but deterministic for each replicate, independent of labels.
    tie = rng.random(len(candidates))
    return {
        "random":rng.permutation(candidates),
        "anomaly":candidates[np.lexsort((tie,-scores["anomaly"]))],
        "event_impact":candidates[np.lexsort((tie,-scores["event_impact"]))]
    }

def apply_review(reference: pd.DataFrame, contaminated: pd.DataFrame,
                 flags:np.ndarray, reviewed_indices:np.ndarray) -> pd.DataFrame:
    """Simulated oracle adjudication: unreviewed flags omitted; reviewed
    items restored to their original QC-screened reference value. False-negative
    corrupted items not flagged remain corrupted.
    """
    flagged=np.asarray(flags,dtype=bool)
    if len(flagged)!=len(contaminated) or len(reference)!=len(contaminated):
        raise ValueError("Length mismatch")
    reviewed = np.asarray(reviewed_indices,dtype=int)
    if reviewed.size and (reviewed.min()<0 or reviewed.max()>=len(flagged) or
                          not flagged[reviewed].all()):
        raise ValueError("Reviewed items must all be flagged")
    o=contaminated.copy()
    o.loc[flagged,"tmax_c"]=np.nan
    if len(reviewed):
        o.loc[reviewed,"tmax_c"] = reference.iloc[reviewed].tmax_c.to_numpy(dtype=float)
    return o

def event_loss(reference_events, candidate_events, candidate_series) -> dict:
    m=event_metrics(reference_events,candidate_events,candidate_series)
    # Equal-weight count distortion is an evaluation choice, NOT a universal
    # scientific impact utility. Report component counts alongside it.
    m["event_distortion_count"] = (m["disappeared_events"] +
                                  m["unmatched_candidate_events"] +
                                  m["fragmented_events"])
    return m

def run_review_benchmark(test: pd.DataFrame, thresholds:dict,
                         regimes=tuple(REGIMES), budgets=BUDGETS,
                         min_lengths=(3,6), reps:int=12,seed:int=20261126):
    """All ranking strategies share exactly the same trial, flags, budget,
    reviewer, corruption and reference events within a comparison block.
    """
    rows=[]
    for (station,year),sub in test.groupby(["station_id",test.date.dt.year],sort=True):
        from .core import attach_threshold
        d=attach_threshold(sub.sort_values("date").reset_index(drop=True),
                           thresholds[station])
        for rep in range(reps):
            for regime in regimes:
                rng=np.random.default_rng(stable_seed(station,year,rep,regime,seed=seed))
                trial=simulate_trial(d,rng,regime)
                if trial is None: continue
                contaminated, flags,err=trial
                nflag=int(flags.sum())
                for min_length in min_lengths:
                    ref_events=_events(d,min_length=min_length)
                    scores=score_candidates(contaminated,flags,min_length)
                    order=ranked_indices(flags,scores,
                        np.random.default_rng(stable_seed(station,year,rep,regime,min_length,"rank",seed=seed)))
                    for budget in budgets:
                        nreview=int(math.ceil(float(budget)*nflag))
                        nreview=min(nflag,nreview)
                        for strategy in STRATEGIES:
                            selected=order[strategy][:nreview]
                            repaired=apply_review(d,contaminated,flags,selected)
                            cand=_events(repaired,min_length)
                            metrics=event_loss(ref_events,cand,repaired)
                            rows.append({
                                "station_id":station,"year":int(year),"replicate":int(rep),
                                "regime":regime,"min_length":int(min_length),
                                "review_budget":float(budget),"strategy":strategy,
                                "n_injected":int(err.sum()),
                                "n_flagged":nflag,"n_true_positive_flags":int((flags&err).sum()),
                                "n_false_positive_flags":int((flags&~err).sum()),
                                "n_false_negative_errors":int((err&~flags).sum()),
                                "n_reviewed":nreview,
                                "n_reviewed_injected":int(err[selected].sum()),
                                **metrics
                            })
    return pd.DataFrame(rows)

def paired_effects(runs:pd.DataFrame,n_boot:int=500,seed:int=2401)->pd.DataFrame:
    """Effect = baseline minus comparator (positive means comparator improves).

    First average repeated interventions per station-year, then average
    station-year differences equally; bootstrap station clusters for CIs.
    Units: station-year, NOT individual simulation rows or event days.
    """
    keys=["station_id","year","regime","min_length","review_budget","replicate"]
    metrics=["event_distortion_count","disappeared_events",
             "unmatched_candidate_events","fragmented_events",
             "mean_lost_reference_days"]
    if runs.empty:raise ValueError("No benchmark rows")
    grouped=runs.pivot(index=keys,columns="strategy",values=metrics)
    rows=[]
    for metric in metrics:
        for baseline,comp in (("random","anomaly"),("random","event_impact"),
                              ("anomaly","event_impact")):
            if (metric,baseline) not in grouped or (metric,comp) not in grouped:continue
            delta=(grouped[(metric,baseline)]-grouped[(metric,comp)]).rename("paired_gain").reset_index()
            for (regime,min_length,budget),sub in delta.groupby(["regime","min_length","review_budget"]):
                units=sub.groupby(["station_id","year"],as_index=False)["paired_gain"].mean()
                units=units[np.isfinite(units.paired_gain)]
                if units.empty: continue
                avg=float(units.paired_gain.mean())
                # Two-stage estimator: station-year means -> station means for
                # bootstrap, while retaining station-year mean point estimate.
                by_station=units.groupby("station_id")["paired_gain"].mean().to_numpy()
                if len(by_station)>=2:
                    rng=np.random.default_rng(stable_seed(metric,baseline,comp,regime,min_length,budget,seed=seed))
                    boot=np.array([rng.choice(by_station,size=len(by_station),replace=True).mean() for _ in range(n_boot)])
                    lo,hi=np.percentile(boot,[2.5,97.5])
                else:lo,hi=np.nan,np.nan
                rows.append({"regime":regime,"min_length":int(min_length),
                             "review_budget":float(budget),"metric":metric,
                             "comparison":f"{comp} vs {baseline}",
                             "paired_gain":avg,"ci95_low":float(lo),
                             "ci95_high":float(hi),
                             "n_station_years":int(len(units)),
                             "n_stations":int(units.station_id.nunique())})
    return pd.DataFrame(rows)

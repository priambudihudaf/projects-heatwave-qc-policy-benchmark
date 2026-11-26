"""Offline checks for v2 strategy fairness, oracle isolation and event logic."""
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from heatqc.noaa import make_demo
from heatqc.core import fit_p90,attach_threshold
from heatqc.review_v2 import (
    simulate_trial, score_candidates, ranked_indices, apply_review,
    run_review_benchmark,paired_effects,stable_seed,STRATEGIES,BUDGETS
)

class ReviewV2Tests(unittest.TestCase):
    def prepared(self):
        data=make_demo(2,seed=14)
        thresholds={}
        for sid,sub in data.groupby("station_id"):
            thresholds[sid]=fit_p90(sub[sub.date.dt.year.between(2010,2020)])
        return data,thresholds

    def test_trial_and_balanced_flags(self):
        data,thresholds=self.prepared()
        d=data[(data.station_id=="DEMO_01")&(data.date.dt.year==2024)].copy().reset_index(drop=True)
        d=attach_threshold(d,thresholds["DEMO_01"])
        trial=simulate_trial(d,np.random.default_rng(1),"balanced")
        self.assertIsNotNone(trial)
        obs,flags,errors=trial
        self.assertGreater(errors.sum(),0)
        self.assertGreater(flags.sum(),0)
        self.assertTrue(np.allclose(obs.tmax_c[~errors].to_numpy(),
                                           d.tmax_c[~errors].to_numpy(),equal_nan=True))

    def test_reviewer_can_only_review_flagged(self):
        dates=pd.date_range("2025-07-01",periods=7)
        ref=pd.DataFrame({"date":dates,"tmax_c":[34.0]*7,
                          "heat_threshold_c":[30.0]*7})
        obs=ref.copy()
        obs.loc[2,"tmax_c"]=39.0
        flags=np.array([False,True,True,False,False,False,False])
        out=apply_review(ref,obs,flags,np.array([1]))
        self.assertEqual(out.tmax_c.iloc[1],34.0)
        self.assertTrue(pd.isna(out.tmax_c.iloc[2]))
        with self.assertRaises(ValueError):
            apply_review(ref,obs,flags,np.array([3]))
        out=apply_review(ref,obs,flags,np.array([1,2]))
        self.assertEqual(out.tmax_c.iloc[2],34.0)

    def test_scores_are_label_blind_and_budget_equal(self):
        data,thresholds=self.prepared()
        d=data[(data.station_id=="DEMO_01")&(data.date.dt.year==2024)].copy().reset_index(drop=True)
        d=attach_threshold(d,thresholds["DEMO_01"])
        obs,flags,errors=simulate_trial(d,np.random.default_rng(123),"balanced")
        scores=score_candidates(obs,flags,3)
        order=ranked_indices(flags,scores,np.random.default_rng(42))
        candidates=set(np.flatnonzero(flags))
        self.assertEqual(set(order),set(STRATEGIES))
        for arr in order.values():
            self.assertEqual(set(arr),candidates)
        n=int(np.ceil(0.25*len(candidates)))
        self.assertEqual(len(set(order["anomaly"][:n])),n)
        self.assertEqual(len(set(order["event_impact"][:n])),n)

    def test_benchmark_and_paired_effects(self):
        data,thresholds=self.prepared()
        test=data[data.date.dt.year==2024].copy()
        out=run_review_benchmark(test,thresholds,reps=2)
        self.assertGreater(len(out),0)
        self.assertTrue(set(out.strategy)==set(STRATEGIES))
        keys=["station_id","year","regime","min_length","review_budget","replicate"]
        self.assertTrue((out.groupby(keys).n_reviewed.nunique()==1).all())
        self.assertTrue((out.groupby(keys).n_flagged.nunique()==1).all())
        # All three interventions evaluated on the same simulated flag mask.
        self.assertTrue((out.groupby(keys).n_true_positive_flags.nunique()==1).all())
        p=paired_effects(out,n_boot=12)
        self.assertFalse(p.empty)
        self.assertTrue(set(p.comparison)=={"anomaly vs random","event_impact vs random"})
        # CI is based on number of distinct stations, not replicate rows.
        self.assertTrue((p.n_stations<=2).all())

    def test_reproducible_seed(self):
        self.assertEqual(stable_seed("station",2024,3),stable_seed("station",2024,3))
        self.assertNotEqual(stable_seed("station",2024,3),stable_seed("station",2024,4))

if __name__=="__main__":
    unittest.main()

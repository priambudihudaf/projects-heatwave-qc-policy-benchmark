"""Unit and integration tests for Pilot v2.1, entirely offline."""
from __future__ import annotations
import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from heatqc.core import Event,fit_p90,attach_threshold
from heatqc.noaa import make_demo
from heatqc.review_v2 import simulate_trial, stable_seed
from heatqc.review_v21 import (
    STRATEGIES,synthetic_flags,strong_baseline_scores,rank_strategies,
    reviewed_series,iou_event_metrics,run_v21,paired_effects_v21
)

class TestPilotV21(unittest.TestCase):
    @staticmethod
    def demo_one():
        data=make_demo(2,seed=14)
        thresholds={sid:fit_p90(g[g.date.dt.year.between(2010,2020)])
                    for sid,g in data.groupby("station_id")}
        year=(data.station_id=="DEMO_01")&(data.date.dt.year==2024)
        d=attach_threshold(data[year].sort_values("date").reset_index(drop=True),
                           thresholds["DEMO_01"])
        return d,thresholds,data

    def test_matched_false_positive_counts_between_distributions(self):
        d,_,_=self.demo_one()
        contaminated,_,errors=simulate_trial(d,np.random.default_rng(12),"balanced")
        tp=np.random.default_rng(99).random(len(d))
        a=synthetic_flags(contaminated,errors,"balanced","uniform",tp,np.random.default_rng(6))
        b=synthetic_flags(contaminated,errors,"balanced","hot_enriched",tp,np.random.default_rng(6))
        self.assertEqual(int((a&~errors).sum()),int((b&~errors).sum()))
        self.assertTrue(np.array_equal(a&errors,b&errors))
        self.assertGreater((a&errors).sum(),0)

    def test_reviewer_failure_is_not_magic_correction(self):
        dates=pd.date_range("2025-07-01",periods=5)
        d=pd.DataFrame({"date":dates,"tmax_c":[32.,33.,34.,35.,36.],
                        "heat_threshold_c":[30.]*5})
        c=d.copy();c.loc[2,"tmax_c"]=43.
        flags=np.array([False,True,True,False,False])
        success=np.array([True,False,True,True,True])
        out=reviewed_series(d,c,flags,np.array([1,2]),success)
        self.assertTrue(pd.isna(out.tmax_c.iloc[1])) # failed review
        self.assertEqual(out.tmax_c.iloc[2],34.)
        with self.assertRaises(ValueError):
            reviewed_series(d,c,flags,np.array([0]),success)

    def test_reviewer_success_nested_seventy_ninety_hundred(self):
        x=np.random.default_rng(7).random(1000)
        self.assertTrue(np.all((x<.7)<=(x<.9)))
        self.assertTrue(np.all((x<.9)<=(x<1.0)))

    def test_iou_threshold_changes_matching(self):
        def ev(start,n):
            ds=tuple(pd.date_range(start,periods=n))
            return Event(ds[0],ds[-1],ds,42.0)
        a=ev("2025-07-01",4)
        b=ev("2025-07-01",3)
        low=iou_event_metrics([a],[b],0.50)
        high=iou_event_metrics([a],[b],0.80)
        self.assertEqual(low["matched_events"],1)
        self.assertEqual(high["matched_events"],0)
        self.assertEqual(high["missed_events"],1)
        self.assertEqual(high["unmatched_events"],1)
        self.assertEqual(low["missed_reference_hot_days"],1)

    def test_split_and_merge_are_diagnosed(self):
        def ev(start,n):
            ds=tuple(pd.date_range(start,periods=n))
            return Event(ds[0],ds[-1],ds,40.0)
        reference=[ev("2025-07-01",7)]
        predicted=[ev("2025-07-01",3),ev("2025-07-05",3)]
        result=iou_event_metrics(reference,predicted,0.25)
        self.assertEqual(result["fragmented_events"],1)
        self.assertEqual(result["matched_events"],1)
        self.assertEqual(result["unmatched_events"],1)

    def test_ranks_label_blind(self):
        d,_,_=self.demo_one()
        obs,_,errors=simulate_trial(d,np.random.default_rng(12),"balanced")
        p=np.random.default_rng(99).random(len(d))
        flags=synthetic_flags(obs,errors,"balanced","uniform",p,np.random.default_rng(11))
        scores=strong_baseline_scores(obs,flags,3)
        self.assertEqual(set(scores),{"hot_run","threshold_proximity"})
        ranked=rank_strategies(obs,flags,3,np.random.default_rng(4))
        self.assertEqual(set(ranked),set(STRATEGIES))
        for name,ranking in ranked.items():
            self.assertEqual(set(ranking),set(np.flatnonzero(flags)),name)

    def test_same_budget_and_reproducibility(self):
        d,thresholds,data=self.demo_one()
        test=data[(data.station_id.isin(["DEMO_01","DEMO_02"])) &
                  (data.date.dt.year==2024)].copy()
        opts={"reps":1,"regimes":("balanced",),
              "placements":("uniform","hot_enriched"),
              "reliabilities":(0.7,1.0),
              "budgets":(0.25,), "lengths":(3,), "ious":(0.5,)}
        out=run_v21(test,thresholds,**opts)
        self.assertGreater(len(out),0)
        groups=["station_id","year","replicate","detector_regime","fp_placement",
                "review_reliability","min_length","iou_threshold","review_budget"]
        self.assertTrue((out.groupby(groups).n_reviewed.nunique()==1).all())
        self.assertTrue((out.groupby(groups).n_true_positive_flags.nunique()==1).all())
        self.assertTrue((out.groupby(groups).n_false_positive_flags.nunique()==1).all())
        self.assertEqual(out.strategy.nunique(),5)
        # Placement changes must not change the number of erroneous input days
        # or detected true positives given same station/year/rep/regime.
        p=out.groupby(["station_id","year","replicate","detector_regime","fp_placement"]
                       )[["n_true_positive_flags","n_false_positive_flags"]].first()
        q=p.unstack("fp_placement")
        self.assertTrue((q[("n_true_positive_flags","uniform")] ==
                         q[("n_true_positive_flags","hot_enriched")]).all())
        self.assertTrue((q[("n_false_positive_flags","uniform")] ==
                         q[("n_false_positive_flags","hot_enriched")]).all())
        rerun=run_v21(test,thresholds,**opts)
        pd.testing.assert_frame_equal(out,rerun)
        effects=paired_effects_v21(out,n_boot=25)
        self.assertGreater(len(effects),0)
        self.assertIn("event_impact vs hot_run",effects.comparison.unique())
        self.assertTrue((effects.n_stations<=2).all())

if __name__=="__main__":
    unittest.main()

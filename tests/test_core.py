import sys
from pathlib import Path
import unittest
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from heatqc.noaa import parse_daily,make_demo
from heatqc.core import fit_p90,attach_threshold,find_events,apply_policy,event_metrics,calendar_day
from heatqc.experiment import make_scenario,run_experiments

class CoreTests(unittest.TestCase):
    def test_noaa_parser(self):
        sample="12345 20250101 2.1.1 -105.0 40.0 12.3 0 0 0 0 0 0 0\n"
        d=parse_daily(sample,"CO_Test","test://fixture")
        self.assertEqual(d.tmax_c.iloc[0],12.3)
        self.assertEqual(str(d.date.iloc[0].date()),"2025-01-01")
    def test_calendar_leap(self):
        days=calendar_day(pd.to_datetime(["2023-03-01","2024-03-01","2024-02-29"]))
        self.assertEqual(days.tolist(),[60,60,59])
    def test_fragment_and_disappearance(self):
        dates=pd.date_range("2025-07-01",periods=9)
        base=pd.DataFrame({"date":dates,"tmax_c":[29,35,35,35,35,35,35,35,29],
                           "heat_threshold_c":30})
        reference=find_events(base)
        self.assertEqual(reference[0].duration,7)
        flags=np.zeros(len(base),dtype=bool)
        flags[4]=True
        removed=apply_policy(base,flags,"remove",cap_c=40)
        candidate=find_events(removed)
        score=event_metrics(reference,candidate,removed)
        self.assertEqual(score["fragmented_events"],1)
        self.assertEqual(score["disappeared_events"],0)
        # a four-day event becomes two pieces too short to be a heatwave
        short=base.iloc[0:6].copy()
        short.loc[:,"tmax_c"]=[29,35,35,35,35,29]
        ref=find_events(short)
        fl=np.zeros(len(short),dtype=bool);fl[2]=True
        after=apply_policy(short,fl,"remove",40)
        met=event_metrics(ref,find_events(after),after)
        self.assertEqual(met["disappeared_events"],1)
    def test_identical_flags_policies(self):
        dates=pd.date_range("2025-07-01",periods=4)
        base=pd.DataFrame({"date":dates,"tmax_c":[35.,42.,36.,30.],
                           "heat_threshold_c":[31.]*4})
        f=np.array([False,True,False,False])
        a=apply_policy(base,f,"preserve",40)
        b=apply_policy(base,f,"remove",40)
        c=apply_policy(base,f,"cap",40)
        self.assertEqual(a.tmax_c.iloc[1],42)
        self.assertTrue(np.isnan(b.tmax_c.iloc[1]))
        self.assertEqual(c.tmax_c.iloc[1],40)
        self.assertEqual(a.qc_flag_simulated.tolist(),b.qc_flag_simulated.tolist())
    def test_synthetic_repeatable(self):
        self.assertTrue(make_demo(2,seed=7).tmax_c.equals(make_demo(2,seed=7).tmax_c))
    def test_pipeline_small(self):
        frame=make_demo(2,seed=2)
        thresholds={};caps={}
        for sid,sub in frame.groupby("station_id"):
            thresholds[sid]=fit_p90(sub[sub.date.dt.year.between(2010,2020)])
            caps[sid]=float(np.nanpercentile(sub[sub.date.dt.year.between(2010,2020)].tmax_c,99.5))
        test=frame[frame.date.dt.year==2024]
        r=run_experiments(test,thresholds,caps,reps=2)
        self.assertGreater(len(r),0)
        self.assertTrue(set(["preserve","remove","cap"]).issubset(set(r.policy)))
        counts=r.groupby(["station_id","year","scenario","replicate"])["n_flags"].nunique()
        self.assertTrue((counts==1).all())

if __name__=="__main__":unittest.main()

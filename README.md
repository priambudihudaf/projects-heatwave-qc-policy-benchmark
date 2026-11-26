# Heatwave-Aware QC Review Prioritization — Research v2.1

**Current research manuscript title:** *Retrospective Heatwave-Aware Prioritization of Quality-Control Reviews: A Controlled Sensitivity Study Using Public Temperature Observations*

**Current implementation on `main`:** v2.1, `run_v21.py` + `src/heatqc/review_v21.py` (which reuses helpers in `review_v2.py`).  
**Status (26 November 2026):** completed exploratory controlled pilot and methodological audit; **GO for qualified manuscript drafting; NOT ready for submission or operational deployment**.

> **Scientific boundary:** NOAA USCRN Daily01 daily maximum temperature is public but **already quality-screened**. All experimental sensor errors, candidate QC flags, and reviewer outcomes are **synthetic**. No NOAA/BMKG operational QC decisions or real sensor-error rates are inferred. A successful simulated reviewer restores the QC-screened reference **exactly** (an optimistic oracle-on-success assumption). This is an **offline/retrospective** study, not real-time QC.

## Research question

Given the **same simulated candidate flags** and a **fixed review budget**, does a label-blind, heatwave-event-impact priority score better preserve heatwave events than simpler prioritization heuristics? Where does it trade event preservation for fewer individually corrected injected errors?

The v2.1 experiment compares five strategies: **random, anomaly, threshold proximity, hot-run length, event impact**. Priority scores use contaminated observed Tmax, simulated flags, and training-only heatwave thresholds; **they do not receive true synthetic error labels or clean references**.

## Latest reproducible study (v2.1)

| Design element | v2.1 configuration |
| --- | --- |
| Public temperature product | NOAA USCRN Daily01, `T_DAILY_MAX`, station-local standard date |
| Sampling | 18 candidate stations audited; 16 eligible; 12 selected with >=95% warm-season coverage in training, reserved validation, and evaluation |
| Years | Train 2010–2020; reserved validation 2021–2022 (not tuned); **exploratory evaluation** 2023–2025 |
| Event definition | Station-specific calendar-day training P90 (+/-7-day window), Tmax > P90, consecutive May–September hot days |
| Sensitivity | At least 3 or 6 consecutive days; 1:1 IoU matching thresholds 0.25 or 0.50 |
| Simulated flag regimes | Balanced / noisy; matched true-positive flags and false-positive counts across placement conditions |
| FP placement | Uniform versus hot-enriched (6x relative sampling weight on observed hot days) |
| Review workload | 10%, 25%, 50% of candidate flags (rounded up), identical within comparisons |
| Reviewer success | 70%, 90%, 100%; success restores reference exactly, failure leaves missing |
| Estimation | Paired trial comparisons, average by station-year; station-cluster bootstrap (300 resamples) |
| Main outcome | Missed reference events + unmatched candidate events + fragmented reference events (equal-weight, task-specific composite) |

**Evaluation 2023–2025 was reused during development from v1 to v2.1. It is not an untouched independent confirmatory test.** Sensitivity analyses are exploratory, and 155,520 downstream evaluation rows are highly dependent.

### Reproducibility

Use Python 3.11+. For the research implementation:

```bash
git clone https://github.com/priambudihudaf/projects-heatwave-qc-policy-benchmark.git
cd projects-heatwave-qc-policy-benchmark
# main contains the current v2.1 implementation
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_v21.py --mode demo --stations 3 --reps 1 --bootstrap 50
python run_v21.py --mode real --stations 12 --reps 6 --bootstrap 300
```

The demo is **entirely synthetic and NOT scientific evidence**. The real-mode experiment uses public NOAA observations as a QC-screened **reference proxy**, then imposes simulated errors, flags and review decisions.

**Colab:** [Run v2.1 notebook](https://colab.research.google.com/github/priambudihudaf/projects-heatwave-qc-policy-benchmark/blob/main/notebooks/Run_Heatwave_QC_V21_from_GitHub.ipynb).

Real-mode output directory: `outputs/V21_NOAA_CONTROLLED/`.

| Output file | Purpose |
| --- | --- |
| `v21_trials.csv` | Full paired synthetic trials, strategy outcomes and metadata |
| `v21_paired_effects.csv` | Paired effects / 95% exploratory station-bootstrap intervals |
| `v21_descriptive_summary.csv` | Distortion components, corrections, budgets and scenario summaries |
| `v21_metadata.json` | Experimental settings, data scope, caveats |
| `coverage_audit.csv` | Candidate station completeness, exclusions |
| `source_manifest.csv` | NOAA URLs, download states, source SHA256 |
| `v21_eventimpact_gain_robustness.png`, `v21_strategy_comparison.png` | Exploratory figures |

**Verified previous full run:** [NOAA v2.1 GitHub Actions](https://github.com/priambudihudaf/projects-heatwave-qc-policy-benchmark/actions/runs/45758900953), artifact `v21-noaa-robustness-results`; see [final audit](docs/FINAL_AUDIT_2026-11-26.md) for checks of the separately supplied Colab result ZIP. Source artifacts are subject to GitHub retention.

## What the audited pilot found

- 288 NOAA source-manifest entries downloaded; 12 stations, 36 station-years.
- **85** reference events lasting at least 3 days; **23** lasting at least 6 days.
- **432** simulated corrupted station-year/regime/repetition series, **864** flag-mask trial groups, and **155,520** dependent strategy/evaluation rows; **not 155,520 independent observations**.
- For balanced/uniform flags, 25% review budget, reviewer success 90%, 3-day events and IoU >=0.50: mean event-distortion counts per simulated trial were **0.838 anomaly**, **0.556 hot-run**, **0.426 event-impact**.
- Paired event-impact gain over anomaly under that setting was **+0.412 simulated composite distortions per station-year**, exploratory 95% station-cluster bootstrap CI **[0.248, 0.639]**.
- The anomaly prioritizer **corrected more injected individual errors** (3.546 vs 3.204 per trial in that setting). Event-impact's mean matched-event peak-temperature error did **not** demonstrably improve in the pilot.
- Strongest methodological limitation: the score is **structurally aligned** with the event-level loss. Results do not establish universal algorithm superiority, real-world QC performance, or a new event-level counterfactual principle.

Read the **[final audit and publication gates](docs/FINAL_AUDIT_2026-11-26.md)** before quoting any result.

## Full manuscript (v2.1)

The complete [exploratory manuscript draft](manuscript/Manuscript_v2.1_Draft.md), [figure gallery](manuscript/README.md), source-linked Results tables and carefully qualified Discussion are now available. Submission remains pending author declarations, permanent output archiving and scientific review.

## Manuscript preparation and publication status

1. [Current v2.1 manuscript outline and evidence map](docs/MANUSCRIPT_OUTLINE.md)
2. [v2.1 controlled-sensitivity protocol](docs/PILOT_V21_PROTOCOL.md)
3. [Final methodological and novelty audit](docs/FINAL_AUDIT_2026-11-26.md)
4. [2025–2026 targeted novelty comparators](docs/LITERATURE_2025_2026.md)
5. [Version history and legacy documentation](docs/VERSION_HISTORY.md)

**Draft now, submit later:** use data-supported findings and report component outcomes separately, verify bibliography and figures, consider an additional independent-station/period replication and lower synthetic-error prevalence, and satisfy author/affiliation permissions and journal requirements before submission. Such checks do **not** require a v3 redesign.

## Version history (legacy code retained intentionally)

| Version | Entry point | Scope | Status |
| --- | --- | --- | --- |
| v1 | `run.py` | Same flags, different handling: preserve / remove / cap | **Historical pilot**, not manuscript v2.1 |
| v2 | `run_v2.py` | Random / anomaly / event-impact review prioritization, ideal reviewer | **Historical pilot** |
| **v2.1** | **`run_v21.py`** | Five rankers, matched FP placements, imperfect oracle review, 1:1 IoU matching, paired uncertainty | **Active manuscript evidence** |

Legacy components are kept for reproducibility; **do not run `run.py` or use the old v1 outline when reporting v2.1**. The default `main` branch now includes v2.1; the historical research branch `research/event-impact-aware-qc-v2-1` retains a reproducible pre-merge snapshot; the historical source migration is in [docs/MIGRATION.md](docs/MIGRATION.md).

## Public sources and ethical scope

- [NOAA USCRN products](https://www.ncei.noaa.gov/access/crn/products.html)
- [NOAA Daily01 directory](https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01/)
- [NOAA Daily01 product format](https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01/readme.txt)
- No restricted BMKG data, hidden NOAA QC flags, or actual reviewer labels are included.

**Research software and exploratory simulations; not a production QC recommendation or evidence of an institution's actual actions.**

# Manuscript v2.1 — writing plan and evidence map

**Working title:** *Retrospective Heatwave-Aware Prioritization of Quality-Control Reviews: A Controlled Sensitivity Study Using Public Temperature Observations*

**Status:** READY FOR CAUTIOUS MANUSCRIPT DRAFTING; **NOT** submission-ready. This outline replaces the **v1 preserve/remove/cap** manuscript outline. The numerical results below are from the [2026-11-26 audit](FINAL_AUDIT_2026-11-26.md), NOT from any claimed independent reanalysis in this document.

## Claim and contribution boundaries

We assess **offline, event-sensitive priority ordering** of *already simulated QC-flagged* Tmax observations under a fixed review budget, against **random, local anomaly, training-P90 proximity, and observed hot-run** heuristics. Compare heatwave event integrity **and** the number of corrected injected point errors. The finding is an **exploratory conditional trade-off**, not a validated operational QC advance, new real-world detector, new counterfactual-ranking principle, or proof of broad novelty.

All NOAA USCRN Daily01 reference temperatures were **already provider-QC-screened**. Sensor errors, QC flags and review outcomes are simulated; success implies exact, optimistic oracle restoration; rankings are label-blind. The same 2023–2025 period helped develop v1→v2.1 and is **not an untouched holdout**.

## Draft abstract — fill/verify against archived output CSV

- **Background:** QC review capacity may be constrained, and prioritizing anomalous individual readings need not preserve extreme event topology.
- **Methods:** 12 USCRN stations (2010–2025), training-based calendar-day P90, 2023–2025 exploratory evaluation, 3-/6-day events, simulated QC flags/errors/reviewers, five budget-matched ranking heuristics, 1:1 IoU matching, station-cluster bootstrap.
- **Primary result:** balanced/uniform scenario, 3-day minimum, IoU >=0.50, reviewer success 90%, budget 25%: anomaly 0.838, hot-run 0.556, event-impact 0.426 mean composite distortions per simulated trial. Event-impact versus anomaly paired gain +0.412 per station-year (95% exploratory bootstrap CI [0.2476,0.6394]).
- **Trade-off:** anomaly 3.546 versus event-impact 3.204 corrected injected point errors per trial; more correction did not correspond to less heatwave event distortion.
- **Conclusion boundary:** modeled retrospective prioritization can change simulated event-level QC outcomes; effects cannot be interpreted as real NOAA operational gains.

## 1. Introduction

1. Importance of preserving scientifically credible temperature extremes during downstream QC decisions.
2. Distinguish **candidate flagging**, **review priority allocation**, **oracle-on-success correction**, and downstream **event reconstruction**.
3. Integrate directly relevant 2025–2026 temperature/QC work; compare with ocean active learning and **2026 event-level counterfactual anomaly methods** (details in [literature matrix](LITERATURE_2025_2026.md)).
4. Specific gap: constrained, **matched-budget retrospective review ranking** focused on heatwave event continuity, including separate point-error correction trade-offs.
5. Research questions: (i) under matched synthetic flags/budget, how do rankers differ in event distortion; (ii) robustness to placement, reviewer success, budget, event definition; (iii) trade-off with error corrections; (iv) limitations of objective-aligned scoring.

## 2. Data and methods

### 2.1 Observations and selection
NOAA USCRN Daily01 Tmax, **local-standard-time dates**, missing sentinel, provider quality screening; 18 candidate stations, 16 pass completeness checks, 12 selected with >=95% warm-season coverage; 288 source-manifest entries downloaded. Describe station selection and data retrieval date/hash from `source_manifest.csv`.

### 2.2 Partition, reference and heatwave threshold
Training 2010–2020 only; 2021–2022 reserved **without model tuning**; evaluation 2023–2025 **exploratory, reused during iterative development**. Calendar-day training P90 within +/-7 days; hot when Tmax > threshold; May–September consecutive 3/6-day reference events; missing days break events.

### 2.3 Controlled simulated perturbations
State exactly how mixed-sign spikes and offsets are injected, per-regime nominal TPR/FPR, uniform vs sixfold hot-enriched FP sampling with **matched total FP counts and matched TP masks**. Approximate injected-error prevalence **~7% of 153 warm-season days per trial** is a *deliberate stress-test property*, not a real NOAA rate.

### 2.4 Fixed-budget review and five label-blind strategies
Review 10/25/50% of flags; simulated success 70/90/100% (successful reviews restore original reference exactly; otherwise flagged observations remain missing). Methods: random, neighbor-median anomaly, P90 threshold proximity, observed hot-run length, event-impact counterfactual deletion. Event-impact has **full-series/future context**, so is **retrospective only**. Counterfactual score is aligned with target event topology; note this explicitly.

### 2.5 Evaluation and inference
Optimal one-to-one Hungarian matching on reference/candidate event-day IoU, minimum 0.25/0.50. Main descriptive loss = **missed reference events + unmatched candidate events + fragmented reference events**, equal-weight composite. Report **each component** and missing/extra hot days, corrected errors, conditional matched-event peak error. Paired comparison = baseline minus event-impact for loss metrics; **a positive difference in corrected-error counts instead means event-impact corrected fewer errors**. Average trials at station-year level, then bootstrap by station (300 draws; 12 clusters; exploratory intervals). Multiple sensitivity cells and replicas are dependent.

### 2.6 Declared primary slice (within v2.1, not prospectively preregistered)
Min duration 3 days; IoU >=0.50; 25% review budget; simulated reviewer success 90%; compare both flag placements and detector regimes. Describe 2023–2025 reuse transparently.

## 3. Results — populated only from verified v2.1 outputs

- **Table 1:** stations, completeness, exclusion counts, years, events (85 min3; 23 min6), 36 station-years, source-file manifest.
- **Figure 1:** controlled design schematic: public QC-screened reference → synthetic error injection → matched flags → five rankings → simulated review → event matching. Label every synthetic component.
- **Table 2:** main slice strategy means, paired effect sizes and station-bootstrap intervals. Balanced/uniform: anomaly 0.838, hot-run 0.556, event-impact 0.426; event-impact vs anomaly +0.4120 [0.2476,0.6394], vs hot-run +0.1296 [0.0741,0.1852].
- **Figure 2:** `v21_eventimpact_gain_robustness.png` or revised publication-quality figure: paired event-impact gains across two placements / reviewer reliability / regimes. Mark exploratory intervals, not independent experiments.
- **Figure 3:** contrast individual injected-error corrections and separate component event losses. Anomaly 3.546 vs event-impact 3.204 corrected injected errors in balanced/uniform main slice.
- **Table 3 / supplement:** noisy/uniform +0.5139 [0.3472,0.7017] event-impact vs anomaly; +0.0972 [0.0115,0.1620] vs hot-run. For hot-enriched/noisy vs hot-run, CI [-0.0002,0.2269] overlaps zero. Show 6-day, IoU=0.25 and review-budget sensitivities without searching for the best-performing slice after the fact.
- **Figure 4 (optional):** distribution by station and outcome component, avoiding pseudo-independent error bars from 155,520 rows.

## 4. Discussion

Explain competing objectives: event-continuity focus versus correcting more individual injected anomalies. Discuss score–loss alignment, 2026 event-level counterfactual prior art, simplified flag generator, unusually high injected-error prevalence, oracle-on-success reviewer, missing flagged values, threshold/season definitions, within-continent sample, only 12 station clusters, unblind reuse of evaluation outcomes, and noncausal transfer to real network operations. Matched-event peak errors are conditional on successful event matching (selection bias).

## 5. Conclusions

Conclude **only** that the examined retrospective scoring rule changes event-level outcomes under specified controlled simulation assumptions, potentially with fewer individual error corrections. No deployment or universal performance claims.

## Declarations and submission checklist

- **Code availability:** repository, v2.1 branch and exact immutable commit SHA used for final figures.
- **Data availability:** NOAA USCRN Daily01 public product; original source URLs/hashes `source_manifest.csv`; simulated intervention outputs and archived run artifact.
- **Reproducibility:** cite exact `v21_metadata.json`, `v21_trials.csv`, `v21_paired_effects.csv`, `v21_descriptive_summary.csv`. Keep all units and metric-sign conventions correct.
- **References:** verify primary sources and bibliographic details (avoid claiming global first).
- **Authors / affiliation / permissions / AI disclosure:** complete truthfully against current publisher policy. Verify figures, references, and suitable supplementary tables before submission.
- **Optional strengthening:** low injected-error prevalence (1%/3%) and additional independent-station/period replication without further tuning. Not prerequisite to writing a manuscript draft; important for stronger generalization.

**Do not use v1 `run.py` results or v1 preserve/remove/cap figures for this paper.**

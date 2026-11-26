# Pilot v2.1 — Robustness protocol

**Status:** reproducible controlled sensitivity experiment; NOT evidence of observed NOAA QC behavior and NOT submission-ready research.

## Why v2.1?
The v2 result suggested event-aware review might protect reference heatwaves better than local anomaly-based review at equal review budgets, but its synthetic QC flags disproportionately targeted hot days, all reviews were assumed perfect, and event matching used any day overlap. This iteration challenges those assumptions explicitly.

## Precommitted comparisons
Same underlying observed, provider-QC-screened NOAA USCRN Daily01 Tmax as v1/v2, and the same train 2010–2020, reserved validation 2021–2022 and test 2023–2025 temporal split. At most 12 stations with >=95% warm-season coverage.

**Five review priority strategies**, each receiving identical flagged observations and budget:
- Random: shuffled flagged candidates.
- Local anomaly: |Tmax - median of nearby observed values|.
- Threshold proximity: 1/(1+|Tmax - train-only calendar P90|).
- Hot-run length: consecutive observed hot-day streak containing the candidate.
- Event-impact: change in detected heatwave topology if the candidate value were excluded from an otherwise unchanged observed series (v2 score).

**Two synthetic QC generator regimes** (balanced and noisy) are inherited from v2 for error injection, with fixed TPR values (.85/.65) and FP fractions (.04/.09), applied to the **same injected errors** across location patterns.

**Matched false-positive counts** for two placement patterns:
- Uniform random false-flag locations among clean May–September days.
- Hot-enriched: weighted sampling, sixfold selection weight on observed hot days.

The TRUE-POSITIVE flag mask is also kept identical when contrasting uniform vs hot-enriched placement. This isolates effects of false-flag *placement*, not count. Exact hot enrichment is a probabilistic weight, not a guaranteed count.

**Reviewer success probabilities:** 70%, 90%, 100%; use a fixed per-day draw within each trial so successes are nested across reviewer scenarios. On review success, an optimistic simulated oracle restores the NOAA reference value; on review failure, flagged value remains missing. This DOES NOT simulate a real expert reconstructing sensor truth.

**Review budgets:** 10%, 25%, 50% of flagged observations, rounded up; all strategies review exactly the same number in each trial.

**Heatwave sensitivity:** temperature > station-specific calendar P90 (training only), during May–September for 3 or 6 consecutive days. Missing days break events.

**Stricter event matching:** solve optimal one-to-one assignment between original and post-review event day sets using Hungarian maximum-weight intersection-over-union (IoU), at minimum IoU of .25 or .50. Report missed reference events, unmatched candidate events, split and merged episodes, missing reference hot days, and extra candidate hot days. One-day-overlap is no longer sufficient for the primary definition.

## Primary analysis
Use **minimum three consecutive hot days, IoU>=0.50, review budget 25%, reviewer success 90%**. Report both uniform and hot-enriched flag placements, balanced and noisy detector regimes, and compare the event-impact strategy with anomaly, hot-run and threshold-proximity baselines.

**Primary outcome:** missed reference event count + unmatched candidate event count + fragmented event count, equally weighted. This metric is task-specific, not a universal QC standard. Co-report three separate components (a composite might hide false positives), corrected error counts and missed/extra hot days.

**Estimation:** repeated interventions share station-year observations. First compute within-trial paired differences, then average by station-year, then bootstrap stations (not individual trial rows). Intervals from only 12 station clusters are provisional, and multiple testing across settings should not be treated as confirmatory statistical evidence.

**Data leakage protections:** error truth and clean reference are available ONLY to synthetic flag generator, simulated reviewer on successful inspection, and outcome evaluator. Priority scores receive contaminated observations, the candidate QC mask and train-only thresholds.

## Explicit limitations and extensions
- Synthetic injection rate and high perfect-on-success correction cannot be generalized to actual NOAA instrument faults or human reviews.
- NOAA Daily01 has already undergone provider QC; no official NOAA QC flags were retrieved.
- The event-impact score is closely aligned with event-level evaluation; strong baselines reduce but do not entirely remove objective-alignment advantage.
- Two IoU thresholds do not exhaust reasonable event definitions.
- If results depend entirely on biased false-flag placement or perfect reviews, report failure of robustness.
- The 2025–2026 novelty search remains a separate obligation before EGUsphere submission.
- No private BMKG files or screenshots enter this repository.

## How to execute
See \`run_v21.py\` and \`notebooks/Run_Heatwave_QC_V21_from_GitHub.ipynb\`.
Use \`python run_v21.py --mode real --stations 12 --reps 6\` to run the public NOAA experiment; the output includes station coverage, source manifest/hashes, complete trial results, paired cluster-bootstrap effects, summaries and figures.

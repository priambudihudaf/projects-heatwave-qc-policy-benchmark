> **HISTORICAL v2 ONLY — NOT THE CURRENT v2.1 MANUSCRIPT PROTOCOL.** This document is preserved for reproducibility; mentions of `main` in the original v2 text describe repository state **at that time**, before v2.1 was merged to `main`. For current code/methods see [v2.1 protocol](PILOT_V21_PROTOCOL.md) and [version history](VERSION_HISTORY.md).

# Pilot v2 — event-impact-aware QC review prioritization
**Status: IMPLEMENTATION / EXPLORATORY METHODS. NOT A PUBLISHED RESULT.**

The entire v1 pipeline remains on main and is not overwritten. This branch adds
an independent controlled evaluation of three strategies for selecting *which
already-flagged* temperature observations to investigate, given a fixed review budget.

## Scientific question
At the same review workload and under identical flagged observations, can a
risk-to-heatwave-event score help prioritize review, compared to random review
or large instantaneous temperature anomalies?

This is a **candidate contribution**, not verified novelty. It does not demonstrate
what NOAA or any other organization actually does during QC.

## Inputs / split
- NOAA USCRN Daily01 provider-QC-screened daily Tmax, public.
- Synthetic demo available for self-tests, excluded from scientific findings.
- Training 2010–20, reserved validation 2021–22, test 2023–25.
- Only warm-season dates May–Sep scored, with train-only calendar P90 +/-7 days.
- Select up to 12 stations with >=95% coverage in each period.
- A sensitivity analysis evaluates minimum runs of **3 and 6** consecutive hot days.

## Generative design
For each station-year/replicate:
1. Copy QC-screened NOAA reference temperature series.
2. Inject **both positive and negative** synthetic error spikes and short
   persistent offsets in hot and non-hot days (magnitudes 4, 6 or 9 C).
3. Generate *synthetic* candidate QC flags using label-conditional detection
   parameters. Under "balanced": nominal TPR .85, FPR .04 + .06 on observed
   hot days. Under "noisy": nominal TPR .65, FPR .09 + .09 on observed hot days.
   These are simulation settings, not NOAA detection statistics.
4. A **simulated oracle reviewer** may inspect 10%, 25%, or 50% of flagged
   observations. All other flagged observations are excluded (missing) from
   event detection. The reviewer perfectly restores the original reference
   for reviewed items (including correction of injected errors); false-negative
   errors remain uncorrected.

The oracle model offers an **upper-bound theoretical test** of prioritization,
not actual human verification, sensor restoration or automated validation.

## Priority scores: MUST NOT use ground-truth information
- Random: deterministic shuffled ordering.
- Anomaly: absolute deviation of observed Tmax from a local median of up
  to six neighboring available values (excluding the candidate).
- Event impact: event topology disruption when *that flagged observation*
  is suppressed versus kept in the contaminated series, plus a small
  local hot-day context tie-break. It uses ONLY the observed values, QC flags,
  and train-only heatwave threshold. It never observes actual synthetic
  error labels or reference events.

All three strategies receive exactly the same candidates and budget in a trial.
Scores are computed **before** oracle review. Ranking works on contaminated
data and can be deceived by erroneous temperature values.

## Evaluation
- Compare candidate heatwave events to NOAA-reference events using overlap
  of at least one day: report missed reference events, spurious events with
  no reference overlap, fragmented events, missing reference hot days.
- Primary *event distortion count* is a transparent exploratory equal-weight
  sum: missed + spurious + fragmented reference events.
- Positive **paired gain** means the comparator produces less distortion than
  the named baseline on the SAME trial and SAME budget. Report both
  **event_impact vs anomaly** (primary) and comparisons to random (secondary).
- Report the separate components (a composite can obscure trade-offs).
- Average repeated interventions within each station-year, then use a
  station-cluster bootstrap. Repeated trials and neighboring heatwaves
  are not independent replicates.

## Failure modes that matter
- Perfect oracle review is not available in normal operations.
- Synthetic flag generation is informed by injected-error labels; priority
  strategies are *not*, but the evaluation is not an out-of-sample QC detector.
- Sensitivity depends on event definition, season, error magnitude and
  selection of stations; *some heatwaves may not satisfy the 6-day definition*.
- Event matching by any overlap day is a pragmatic pilot diagnostic; a robust
  one-to-one matching / intersection-over-union analysis remains to be added.
- The threshold proximity and synthetic intervention placement may dominate
  seemingly strong effects. Large effects alone do not establish novelty.
- NOAA Daily01 has itself been through QA/QC; cannot establish actual bias
  of operational NOAA or other networks.
- No assertion that "event-aware" will outperform anomaly. An equally valid
  outcome is no improvement or even worse performance.

## Outputs
\`v2_all_trials.csv\`: full paired interventions per station/year/replicate.
\`v2_paired_effects.csv\`: station-level bootstrap CIs of comparison to random.
\`v2_descriptive_summary.csv\`: separate event-loss mechanisms.
\`v2_gain_vs_random.png\`, \`v2_comparisons_min3.png\`,
\`v2_comparisons_min6.png\`: visual diagnostics.
\`v2_metadata.json\`, \`source_manifest.csv\`, \`coverage_audit.csv\`:
reproducibility information.

## Publication gate
Before preprint, improve matching, run additional robustness and comparisons
including review with imperfect correction, evaluate held-out-station
transferability if tuning introduced, run 2025–26 literature overlap review,
and obtain all applicable institutional / publication permissions.

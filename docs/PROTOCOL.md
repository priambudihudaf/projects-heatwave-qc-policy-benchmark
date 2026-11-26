# Protocol — controlled event-level QC policy sensitivity

**Status:** Research plan, not evidence of novelty or results (2026-11-26).

## Question and conceptual contribution

When QC flags are *identical*, can downstream handling policies lead to
substantially different heatwave event statistics? Quantify **which event
durations, positions, and error contexts** cause changes. Avoid presenting
the trivial mathematical property that deletion breaks consecutive runs as
a novel scientific finding.

## Data and design

NOAA USCRN Daily01 QC-screened Tmax (LST_DATE), contiguous USA, 2010–2025.
Reference proxy is Daily01, never the unknown pre-QC original.
Select 12 stations from reproducible public directory intersections, screen
warm-season coverage >=95% on train/validation/test.
Time: train 2010–2020 / reserved validation 2021–2022 / independent test 2023–25.
Dates are LOCAL STANDARD TIME; do not join UTC daily products without alignment.
Missing sentinel -9999.0 -> NaN. No interpolation.

## Define reference events

Compute station-specific P90 thresholds using training observations within
+/-7 calendar days across 2010–2020 (exclude Feb 29 in threshold fitting).
Hot-day condition is strictly Tmax > P90; a heatwave needs >=3 consecutive
May–Sep hot days. A missing day stops a run. May-Sep chosen for a pilot;
the limitation for other climates is explicit.

## Controlled scenarios

Eight types, repeated 30 times by default:
- clean_start / clean_middle / clean_end: one *false QC flag* on an
  accepted-reference heatwave without modifying its temperature
- spike_inside / spike_outside: inject a one-day +5/+10C perturbation
  with an oracle true-positive QC flag
- offset_inside / offset_outside: inject +3/+5C on up to three adjacent days
  with oracle QC flags
- mixed: one flagged injected error inside an event plus another false flag

These are *controlled stress tests*. The flags are never claimed to be produced
by the NOAA QC system or an operational anomaly detection model. The event
targeting and error labels can require knowledge unavailable in actual QC.

## Analysis policies (same flag mask)

1. preserve: retain observed/contaminated value AND flag.
2. remove: set flagged values to missing, never fill in.
3. cap: minimum of flagged value and training station P99.5 threshold.
These policies apply to analysis copy, NOT to original or official observations.

## Evaluation

Recompute events with fixed thresholds. Match reference and candidate events
by overlapping days. Report event recall, fragmentation, disappearance,
unmatched new events, lost reference heatwave days, and matched-event peak error.
An event overlapping several episodes is not interpreted as one-to-one matching;
disappearance and fragmentation are separate outcomes.

Analyze by scenario, station, year; bootstrap at station level. Repeated masks
on the same heatwave do not represent independent heatwave events.

## Limits and safeguards

- Reference is QC-screened, not independently reobserved ground truth.
- Synthetic false flags and corrupted data provide *causal intervention* about
  policies within this artificial design, not evidence of real NOAA/BMKG operations.
- Capping a value is not a scientifically endorsed correction.
- A single missing day cannot universally be classified as a broken heatwave
  without a missing-data convention.
- Source snapshot can change after retrieval; retain per-file hashes.
- Comparing policy outcomes at different simulated flag masks is invalid.
- A cap threshold P99.5 usually leaves P90–P99.5 temperatures unchanged;
  this is an intentional result, not a bug.
- Study may not be novel enough for journal publication without empirically
  meaningful patterns and an updated systematic literature review.

## Future additions (not claims of current implementation)

- Optional event-matching one-to-one / IoU thresholds.
- Paired policy effect confidence intervals, station holdout.
- 3 vs 6-day heatwave sensitivity and alternate summer definition.
- Severe corruption mixtures, real documented error labels if available.

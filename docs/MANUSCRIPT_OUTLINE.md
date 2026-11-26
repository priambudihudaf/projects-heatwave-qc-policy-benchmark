# EGUsphere manuscript outline (NO RESULTS YET)

**Working title:** Flag, Remove, or Cap? An Event-Level Assessment of
Quality-Control Decisions on Heatwave Statistics

## Abstract
[Write only after independent NOAA experiments; no invented findings.]

## 1 Introduction
- Difference between QC flagging and handling policy.
- Prior studies in 2025–2026: extreme heat preservation, meteorological autoencoder QC,
  urban air temperature QC, and downstream QC sensitivity.
- Candidate gap: holding flags constant while measuring heatwave event topology
  and physically relevant outcome distortion.

## 2 Data
- NOAA USCRN Daily01, version and retrieval date.
- LST date; QC-screened reference, not raw unaltered sensor data.
- Station-selection rule and completeness thresholds.
- Predefined 2010–20 / 2021–22 / 2023–25 partition.

## 3 Methods
3.1 Training-based seasonally varying P90 threshold.
3.2 Event definition, event overlap criteria, missing-day policy.
3.3 Controlled clean false flags, spikes, persistent offsets.
3.4 Three policies on *identical* flag masks.
3.5 Event recall, fragmentation, disappearance, lost days, peak errors.
3.6 Cluster uncertainty, seed, leakage safeguards.
3.7 Sensitivity / alternative event definitions.

## 4 Results
[Populate only after analysis of real downloaded NOAA data.]
- Table 1: data coverage and reference event counts.
- Figure 1: scenario design and a representative *labeled* case study.
- Figure 2: event recall/disappearance versus handling policy.
- Figure 3: fragmentation versus flag position / event duration.
- Figure 4: trade-offs by error type and station.
- Table 2: paired policy effect sizes and uncertainty.

## 5 Discussion
- What is an empirical effect beyond mathematical inevitability?
- Can findings transfer to other climatic regimes / variables?
- Reference and simulated error limitations.
- Distinguish QA research from criticism of NOAA QC operations.

## 6 Conclusions
[Answer the actual supported research question.]

## Code and data availability
Code publicly accessible; data publicly retrievable from NOAA; source manifest
records retrieval URLs and SHA256. Include precise commit SHA after final run.

## Author contributions / competing interests / AI statement
Complete according to final publisher and institutional policies.

## References
Only verified 2025–2026 novelty references for the initial focused review;
official NOAA docs may be older and are cited as dataset documentation.

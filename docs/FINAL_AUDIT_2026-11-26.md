# Final Methodological and Novelty Audit — Pilot v2.1

**Audit date:** 2026-11-26  
**Status:** **GO for carefully qualified manuscript drafting; NO-GO for submission-ready causal/general performance claims**.  
**Source of experimental counts:** user-provided Colab ZIP \`heatwave_QC_V21_NOAA_RESULTS.zip\` (local audit: \`v21_trials.csv\`, \`v21_paired_effects.csv\`, \`coverage_audit.csv\`, \`source_manifest.csv\`, \`v21_metadata.json\`).  
**Source of implementation:** branch \`research/event-impact-aware-qc-v2-1\`, \`src/heatqc/review_v21.py\`, \`src/heatqc/review_v2.py\`, \`run_v21.py\`.  
**Novelty window:** peer-reviewed or published research dated **2025–2026**, plus current official NOAA / EGUsphere documentation for non-novelty requirements.

## 1. Reproducibility / data integrity

| Check | Verified result |
| --- | --- |
| NOAA source-manifest download entries | **288**, all \`downloaded\` |
| Candidate stations in coverage audit | **18**, **16 eligible**, **12 selected** |
| Selected stations meeting >=95% warm-season coverage in all three periods | **12/12** |
| Data period used for reporting | training 2010–2020; reserved validation 2021–2022; test 2023–2025 |
| Number of station-years | **36** (12 stations x 3 test years) |
| Reference heatwave events | **85** with >=3 consecutive days; **23** with >=6 days |
| Independent corrupted series generated | **432** station-year x replicate x detector-regime draws |
| Alternative FP locations per corrupted series | **2**, giving 864 flag-mask trial groups |
| Downstream strategy/evaluation rows | **155,520**, **NOT independent samples** |
| Duplicate row identifiers | **0** |
| Composite \`event_distortion_count\` == missed + unmatched + fragmented | **all rows** |
| Review budgets within the same scenario | **identical across five strategies** |
| Errors and false-positive flag counts in the two placement conditions | **matched** |
| Source hashes and URLs | included in \`source_manifest.csv\` |

**Crucial scope:** NOAA USCRN Daily01 is **already quality-screened**. Neither the QC flags nor the inserted sensor errors nor the reviewer adjudications in the experiment are observed NOAA operational actions.

## 2. Prespecified primary scenario within v2.1 (but NOT prospectively preregistered)

Minimum 3-day heatwaves, IoU >= 0.50, review budget 25% of flagged records, simulated review success probability 90%, the **uniform** false-positive location scenario.

| Detector regime | Event-impact vs anomaly, positive = fewer distorted events | 95% station bootstrap CI | Event-impact vs hot-run | 95% station bootstrap CI |
| --- | ---: | ---: | ---: | ---: |
| Balanced | **+0.4120** per station-year | [0.2476, 0.6394] | **+0.1296** | [0.0741, 0.1852] |
| Noisy | **+0.5139** | [0.3472, 0.7017] | **+0.0972** | [0.0115, 0.1620] |

These are paired estimates from **12 station clusters**, not real-world forecast/QA operational performance estimates. The CI estimation uses 300 cluster bootstrap resamples and is exploratory. The hot-enriched/noisy hot-run result has 95% CI of **[-0.0002, 0.2269]**; therefore improvement against hot-run is less robust than that against anomaly.

With balanced/uniform flags, 90% reviewer, 25% budget and min 3 days, the three strategies' average composite event distortion counts per simulated trial were:
- Anomaly **0.838**; Hot-run **0.556**; Event-impact **0.426**.
- Anomaly corrected **3.546** synthetic error observations per trial; Event-impact **3.204**. More error corrections do **not** necessarily mean better event-level preservation.
- Event-impact reduced missing reference hot days relative to anomaly, but its mean *absolute peak-temperature error* in matched events did **not** demonstrably improve in this simple secondary check. Peak-error averages are conditional on event matching and thus susceptible to selection bias.

**Do NOT say** 0.412 distorted events were avoided in real NOAA production workflows; say **0.412 fewer simulated composite distortions per station-year under the stated controlled intervention**.

## 3. Correctness findings and methodological limitations

| Check | Level | Finding / requirement |
| --- | --- | --- |
| Basic pipeline execution / paired budget fairness | PASS | All core data-audit checks passed. |
| Direct ground-truth leakage into *priority ranking* | PASS (bounded) | Scores use contaminated observations, known simulated flag mask, train-fitted thresholds; no injected error labels or clean reference. |
| Outcome-data reuse across pilot versions | **HIGH** | Years 2023–2025 have informed the move from v1 -> v2 -> v2.1. They are **not** an untouched independent evaluation anymore. Treat results as exploratory/hypothesis-generating; do not use the word "confirmatory" or claim a fully independent test. |
| Synthetic error prevalence | **HIGH** | Trial-level mean is ~10.7 injected-error days per station-year, roughly **7%** of the 153 warm-season days. This is a stress-test prevalence, **not** a supported estimate of genuine NOAA sensor failures. |
| Simulated QC flag mechanism | MODERATE-HIGH | True-positive flags are generated conditioned on injected truth; FP count and placements are controlled. A probabilistic scenario is **not** a validated operational QC detector. |
| Reviewer semantics | **HIGH** | A reviewer who "succeeds" restores the reference value exactly. A failed review leaves it missing; no mistaken accepted correction is modeled. "70%" and "90%" are purely hypothetical success probabilities, not measured human accuracy. |
| Event-aware score and loss alignment | **HIGH** | Score uses hypothetical change to heatwave topology after removing a candidate; composite outcome counts missed/spurious/fragmented heatwaves. This structural alignment favors event-aware scoring, so method novelty must be framed as empirical *trade-offs and robustness*, not universal superiority. |
| Comparator strength | PARTIAL PASS | Hot-run, threshold proximity, anomaly and random provide stronger baselines; **hot-run is the most serious comparator**. |
| Event matching | PARTIAL PASS | Optimal 1:1 day IoU 0.25/0.50 is better than any overlap, but split-event counting can overlap conceptually with unmatched event penalties; equal-weight composite is ad hoc. Report components individually. |
| Noncausal vs real-time | **HIGH if operational claims** | Event-impact scoring inspects a full series including future days. It is an **offline/retrospective triage** strategy and must NOT be described as real-time QC. |
| Uncertainty and multiple testing | MODERATE | Station-cluster bootstrap uses only 12 stations, and many sensitivity configurations reuse the same data. Do not interpret the 144+ setting counts as independent replications. |
| Incomplete validation usage | MODERATE | 2021–2022 is reserved but unused for calibrating the presented method. This is permissible but does not remove the test-set reuse concern. |
| Heatwave definition / climate representativeness | MODERATE | May–September daily Tmax > station-specific training P90, 3 or 6 consecutive days is ONE definition. Only **16/36 station-years** contain a >=6-day reference heatwave. Generalization beyond this US sample is unknown. |
| Objective direction for correction metric | MODERATE | For \`n_corrected_errors\`, the paired code uses *baseline minus comparator*. **Positive** here means the comparator corrected **fewer** synthetic errors, opposite to the event-distortion metric's quality orientation. |
| Publication approval | MUST CHECK | Use appropriate research/affiliation permissions before public preprint. A public GitHub code repository does not establish approval to publish under an institution's affiliation. |

## 4. Literature novelty matrix — only 2025–2026 studies

These comparators make several broad novelty claims **unavailable**:

| Paper | Year | What it covers / overlap | Difference, if any |
| --- | --- | --- | --- |
| [Leveraging Crowdsourced Data for Extreme Heat Monitoring](https://doi.org/10.1002/joc.70050) | 2025 | Extreme-heat-aware QC and minimizing loss of valid heatwave information. | Does not establish the *same* constrained, label-blind, post-flag review ranking design. Heatwave preservation itself **is not novel**. |
| [Leveraging active learning for ocean data quality assessment: reducing labeling workload and addressing severe data imbalance challenges](https://doi.org/10.1007/s41060-025-00751-w) | 2025 | Uses operator/labeling workload as QC constraint for ocean observations. | Cost-constrained human-in-the-loop QC **is not novel**. Different domain/target. |
| [A Practical Framework for Event-Level Evaluation and Verifiable Counterfactual Explanation in Multivariate Time-Series Anomaly Detection](https://doi.org/10.3390/app16115450) | 2026 | **Closest methodological threat:** event-level metrics, counterfactual repair-based ranking, matched random/heuristic baselines. | Heatwave event-continuity application and constrained review budget differ, but **counterfactual priority based on repairing events is not novel in general**. Cite and explicitly position. |
| [Proximity-based explainable anomaly detection for time-series data with calibration, leakage safety](https://www.sciencedirect.com/science/article/pii/S2542660526000508) | 2026 | Fixed-budget top-k anomaly triage, calibration, leakage-safe time-series evaluation. | Budgeted triage **is not novel**; study not specifically about heatwave event distortion. |
| [Comprehensive compilation and quality assessment of street-level urban air temperature measurements](https://doi.org/10.1038/s41597-026-06804-4) | 2026 | Temperature QC, retains raw values / flags and considers credible extreme heat; reports expert validation. | Our review-allocation benchmark differs, but preserving original flagged temperatures **is not novel**. |
| [A machine learning approach using autoencoders to perform quality control on meteorological data](https://doi.org/10.1017/eds.2026.10030) | 2026 | Detection of suspicious temperature observations using ML and expert QC. | Our downstream objective is event integrity rather than individual anomaly detection; do not claim a novel QC detector. |
| [A Benchmark Dataset of Agricultural Weather Stations over the Contiguous United States for Evapotranspiration Applications](https://doi.org/10.1038/s41597-026-07819-7) | 2026 | Quantifies scientific downstream changes from QA/QC corrections (evapotranspiration). | Quantifying **downstream QC consequences is not novel**, though application to event-level review differs. |

**Candidate incremental novelty, NOT globally proven first:** Controlled comparison of *event-impact* versus simpler *hot-run* and anomaly ranking for constrained retrospective review of daily Tmax candidate flags, measuring both heatwave event continuity and individual synthetic-error corrections under a matched flag mask and review budget.

**Do not claim** the first impact-aware QC system, the first event-preserving QC, the first counterfactual-ranking method, or the first budget-aware operator-review scheme.

## 5. What is truly needed before manuscript submission? No v3 needed.

**Minimal in-place checks**, not a new major algorithm:
1. **Undisclosed holdout / additional independent replication:** try 2021–2022 or the four unused eligible stations, without tuning scores after reviewing their outcomes. Call this an *additional replication/sensitivity check* rather than a prospectively preregistered confirmatory test.
2. **Error-prevalence stress test** with lower injected-error rates (e.g., 1% and 3%, explicitly hypothetical). A conclusion that only appears at ~7% injected errors must be described as high-error stress-test-specific.
3. **Outcome audit from existing CSV (no rerun):** show separate missed events, false new events, fragmentation, lost/extra hot days, and error corrections; report "mean peak temperature error" only conditional on matching. Provide matched-pair station-bootstrap CIs.
4. **Manuscript positioning:** use *retrospective, controlled, simulated post-flag QC review triage*, not operational real-time QC. Explain that reviewer "success" means perfect oracle restoration. Declare model-development history/test reuse and avoid suggesting that 2023–2025 was an untouched blind test.
5. **Novelty + permissions:** cite the 2026 event-level counterfactual study and 2025 ocean active-learning QC study, as well as relevant heatwave QC; verify submission/affiliation permissions.

## 6. Go / no-go decision

- **GO** to draft Introduction, Data, Methods, Results and Discussion as a **transparent exploratory simulation-based methodological preprint**, with strong limitations and comparison to 2025–2026 recent studies.
- **NO-GO** to claim deployed QC superiority, real NOAA error rates, proven cross-network generalizability, a truly untouched independent test, or a novel counterfactual-ranking algorithm.
- **NO-GO for immediate EGUsphere submission** pending at least the manuscript-quality controls and relevant approvals. EGUsphere standalone preprints are moderated for basic scientific quality.

Suggested cautious title:

**Retrospective Heatwave-Aware Prioritization of Quality-Control Reviews: A Controlled Sensitivity Study Using Public Temperature Observations**

Suggested cautious contribution sentence:

> We evaluate whether a heatwave-event-sensitive ranking of flagged temperature observations can reduce simulated event-level distortion relative to point-anomaly and hot-run heuristics under matched review budgets, while documenting trade-offs in correction of injected point errors.

## 7. Official documentation / submission constraints

- NOAA USCRN data products: https://www.ncei.noaa.gov/access/crn/products.html
- EGUsphere screening: https://www.egusphere.net/preprints/preprint_screening.html
- EGUsphere submission: https://www.egusphere.net/preprints/preprint_submission.html
- EGUsphere general terms / institutional approvals: https://www.egusphere.net/about/general_terms.html

**Scientific verdict:** v2.1 is a credible **pilot benchmark**, not yet a claim of new real-world QC technology. Write the manuscript from the existing honest evidence, optionally adding the two small holdout/prevalence checks to strengthen it before submission.
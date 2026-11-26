# Heatwave QC Policy Benchmark (independent research project)

**Working title:** *Flag, Remove, or Cap? An Event-Level Assessment of Quality-Control Decisions on Heatwave Statistics*

> **Research software / preregistered pilot, NOT a published result.**
> No BMKG, Kalsel, or restricted institutional observations are used. The experiment
> uses NOAA's already-QC-screened Daily01 Tmax as a **reference proxy**, with
> explicitly **synthetic** flags/errors. Do not interpret results as evidence of
> actual NOAA QC policies, nor as validated ground-truth sensor errors.

This is the **standalone research repository**. Migrated from `priambudihudaf/kemayoran-rainfall-gapfill/projects/heatwave-qc-policy-benchmark/` on 2026-11-26. No BMKG or private station data are included.

## What this project asks

With an *identical* QC-flag mask, how do three downstream choices — retain
value with flag, remove value, and cap high flagged value — change **heatwave
event recall, fragmentation, disappearance, duration loss, and peak temperature**?

**The research gap remains a candidate**, not a verified novelty claim. 2025–2026
studies already examine extreme-heat preservation and QC effects. This project
isolates *post-flag handling* for controlled event-level sensitivity testing.

## Run (Python 3.11+)

From this project directory:

```bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run.py --mode demo --stations 4 --reps 3
```

**DEMO uses entirely synthetic data and is not a scientific result.**
Outputs: `outputs/SYNTHETIC_DEMO_NOT_RESULTS`.

Real NOAA data (requires internet; hundreds of small downloads, cached locally; the program oversamples candidate stations and retains up to the requested number after completeness checks):

```bash
python run.py --mode real --stations 12 --reps 30
```

Outputs: `outputs/NOAA_PILOT/`. All input source file URLs + SHA256 checksums
are recorded in `source_manifest.csv`. Data are cached in `data/raw/` and
are not committed.

## Open directly in Google Colab

[Run the dedicated notebook](https://colab.research.google.com/github/priambudihudaf/projects-heatwave-qc-policy-benchmark/blob/main/notebooks/Run_Heatwave_QC_from_GitHub.ipynb) — setup, tests, demo, NOAA real-data pilot and zipped results. No credentials or BMKG files needed.

## Reproducibility and validity

- Data: NOAA USCRN **Daily01** (not raw weather station observations);
  `T_DAILY_MAX` is field 6, temperature in °C; `LST_DATE` is the station's
  local-standard-time day. Data missing sentinel `-9999.0` becomes NaN.
- Timeline: train 2010–2020; validation 2021–2022 (reserved); test 2023–2025.
- Heatwave: Tmax > station-wise P90 for calendar day (+/-7-day baseline
  window), for at least 3 consecutive May–September days.
- P90 and P99.5 clipping threshold use **training data only**.
- Real-data station selection is deterministic from stations appearing in both
  start and end year directory listings, with geographically distributed state
  ordering, and requires >=95% warm-season coverage in all three periods.
- Reference events are computed **before** introducing synthetic errors.
- Flags are identical across the three policies within a trial. Some scenarios
  deliberately use oracle knowledge of heatwave location / synthetic error
  location. They are *stress tests*, **not deployable QC detectors**.
- Capping is **counterfactual** and not recommended as a production practice.
  Raw values and flags should be preserved in an audit trail.
- Missing days break runs; no interpolating over missing periods.
- Simulated repetitions resample a finite pool of heatwaves. They are not new
  independent events; summary uses station-level cluster bootstrap.
- USCRN quality-screened data can still contain errors: reference proxy is
  not perfect ground truth. Synthetic errors do not replicate all real failures.
- Manuscript publication, factual novelty, and acceptance are NOT implied.

## Directory

- `run.py`: full CLI analysis from data download to figures
- `src/heatqc/noaa.py`: NOAA download, parser, demo generator, cache + source URLs
- `src/heatqc/core.py`: P90 thresholds, event runs, policies, metrics
- `src/heatqc/experiment.py`: randomized controlled scenarios + station bootstrap
- `tests/`: offline unit tests and smoke test
- `docs/PROTOCOL.md`: comprehensive experiment decisions / caveats
- `docs/MANUSCRIPT_OUTLINE.md`: EGUsphere skeleton without invented Results
- `docs/LITERATURE_2025_2026.md`: current relevant reading list
- `.github/workflows/heatwave-qc.yml`: CI unit tests and synthetic smoke test

## Official data documentation
- [NOAA Daily01 directory](https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01/)
- [NOAA Daily01 readme](https://www.ncei.noaa.gov/pub/data/uscrn/products/daily01/readme.txt)
- [USCRN products](https://www.ncei.noaa.gov/access/crn/products.html)

## Next checkpoints before EGUsphere

1. Confirm 12 station availability and inspect date/missingness coverage on real NOAA.
2. Audit whether the chosen P90 heatwave definition aligns with targeted literature.
3. Add sensitivity analysis for 3 vs 6-day definitions, upper thresholds, and
   strict independent-station evaluation.
4. Verify 2025–2026 literature overlap, especially event-level post-QC studies.
5. Inspect all results critically; no fabricated numeric findings in manuscript.
6. Follow publication permissions/affiliation rules when submitting.

## Reproduced NOAA pilot results

Prior successful full 12-station test (before migration): [GitHub Actions run](https://github.com/priambudihudaf/kemayoran-rainfall-gapfill/actions/runs/45747326581) produced **12 stations**, **85 reference events**, **23,040 simulated policy evaluations**. These figures are process/output counts, **not evidence of scientific novelty or observed NOAA QC behavior**. The new repository has independent workflows that regenerate a fresh output ZIP from public NOAA data; download it from the `heatwave-qc-noaa-12station-results` artifact on the full NOAA Actions run.


## Pilot v2 — event-impact-aware review triage (research branch)

V1 is preserved on \`main\`. The opt-in \`research/event-impact-aware-qc-v2\` branch
adds a simulated, equal-budget comparison of random, anomaly-based and
**event-impact-aware review prioritization**, using NOAA QC-screened public Tmax
with **synthetic errors, synthetic QC flags and an idealized oracle reviewer**.
This is a research *stress test*, not a model of NOAA operational QC actions.

\`\`\`bash
python -m unittest discover -s tests -v
python run_v2.py --mode demo --stations 3 --reps 2
python run_v2.py --mode real --stations 12 --reps 12
\`\`\`

Read [Pilot v2 research protocol](docs/PILOT_V2_PROTOCOL.md),
[execution guide](docs/PILOT_V2_RUN_GUIDE.md) and
[Colab v2](notebooks/Run_Heatwave_QC_V2_from_GitHub.ipynb) for limitations.
No results should be reported as scientific novelty until reproducibility,
sensitivity checks, and 2025–2026 literature review are complete.

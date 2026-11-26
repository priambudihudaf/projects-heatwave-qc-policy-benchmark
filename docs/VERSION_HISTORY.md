# Research version history and migration notes

This repository intentionally keeps prior experiments to preserve reproducibility. **v2.1 is now on default `main` and is the active manuscript study**. Prior runner scripts remain available.

| Version | Runner | Experiment | Status |
| --- | --- | --- | --- |
| v1 | `run.py` | Preserving vs removing vs capping identically flagged public temperature data; event-level consequences | Historical standalone pilot |
| v2 | `run_v2.py` | Fixed-budget prioritization: random, anomaly, event impact; idealized reviewer, preliminary event matching | Intermediate exploratory pilot |
| **v2.1** | **`run_v21.py`** | Five prioritizers, matched FP scenarios, imperfect oracle review, stricter IoU matching, paired uncertainty and sensitivity | **Latest active evidence for manuscript** |

## What remains valid

- `src/heatqc/core.py`, `src/heatqc/noaa.py` and `run_v2.py` helpers underpin the newer workflow; do **not** delete them.
- `src/heatqc/review_v2.py` contains shared simulation and event-impact scoring used by `review_v21.py`; the name is historical, not a stale version of the current score.
- `run.py`, `src/heatqc/experiment.py`, `tests/test_core.py` and the older notebooks remain for legacy reproduction.
- The v1 `docs/PROTOCOL.md`, v2 `docs/PILOT_V2_PROTOCOL.md` and `docs/PILOT_V2_RUN_GUIDE.md` are preserved as explicitly **historical**, not current paper protocols.
- Current: `docs/PILOT_V21_PROTOCOL.md`, `docs/FINAL_AUDIT_2026-11-26.md` and `docs/MANUSCRIPT_OUTLINE.md`.

## GitHub workflow / output separation

- v1: `outputs/NOAA_PILOT`.
- v2: `outputs/V2_NOAA_CONTROLLED`.
- v2.1: `outputs/V21_NOAA_CONTROLLED`; verified workflow [45758900953](https://github.com/priambudihudaf/projects-heatwave-qc-policy-benchmark/actions/runs/45758900953) (artifact `v21-noaa-robustness-results`).
- Historical v1 migration from Kemayoran repository is described in [MIGRATION.md](MIGRATION.md).

## Scientific evolution

The 2023–2025 evaluation period **influenced method iterations across versions**; avoid calling it a prospectively untouched test set. v2.1 supports **exploratory simulation-based claims**, not causal claims about NOAA operations or confirmed new detector performance. Do not mix published units, figures, or terminology across versions.

Use [README](../README.md) and the [v2.1 manuscript outline](MANUSCRIPT_OUTLINE.md) for all current writing.

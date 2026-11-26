# Repository migration

Migrated on 2026-11-26 from https://github.com/priambudihudaf/kemayoran-rainfall-gapfill/tree/main/projects/heatwave-qc-policy-benchmark to https://github.com/priambudihudaf/projects-heatwave-qc-policy-benchmark.

All tracked code, docs, notebook, tests, and three Actions workflows were moved to repository root (no separate subproject folder). The source research folder is retired after verification. **GitHub Actions artifacts do not transfer across repositories**: the original full 12-station results remain accessible in the historic run https://github.com/priambudihudaf/kemayoran-rainfall-gapfill/actions/runs/45747326581 subject to GitHub retention. Run `.github/workflows/heatwave-qc-full-noaa.yml` on the new repository to produce a new dataset-backed artifact.

NOAA data and synthetic-QC limitations documented in README and PROTOCOL remain unchanged.

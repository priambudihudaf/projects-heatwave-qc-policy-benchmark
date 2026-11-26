# Pilot v2 — execution

Branch: \`research/event-impact-aware-qc-v2\` (v1 on \`main\` remains unchanged).

## Quick start (Python 3.11+)

\`\`\`bash
python -m pip install -r requirements.txt
python -m unittest discover -s tests -v
python run_v2.py --mode demo --stations 3 --reps 2
\`\`\`

Demo outputs: \`outputs/V2_DEMO_SYNTHETIC/\`; not publishable.

## Public NOAA experiment

\`\`\`bash
python run_v2.py --mode real --stations 12 --reps 12
\`\`\`

Real USCRN Daily01 is already QC-screened; **all injected errors, simulated
flags and perfect review decisions are synthetic**. Never report these as
observed NOAA errors or actions.

Outputs in \`outputs/V2_NOAA_CONTROLLED/\`, excluded by .gitignore.
Use \`v2_paired_effects.csv\` for uncertainty-aware comparisons and
\`v2_all_trials.csv\` to independently verify that review budgets, candidate
counts, flags and errors are identical across methods within a trial.

## Colab

Open [Pilot v2 Colab](../notebooks/Run_Heatwave_QC_V2_from_GitHub.ipynb)
on this branch and run all cells. Downloads a ZIP at the end.

## What would be a meaningful contribution?

Not a trivial "remove breaks run" result. A defensible contribution would
show with paired, uncertainty-aware validation whether a **label-blind**,
event-impact-aware review priority produces fewer *missed and false-created*
heatwaves than simple anomaly review at a **fixed review budget**, across
error types, heatwave definitions and stations.

The current setup uses **oracle review**, so any positive effect reflects
conditional value of prioritization under a perfect verifier, not a
deployable system.

Always report negative results and novelty limitations.

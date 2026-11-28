# EGUsphere stand-alone preprint — submission readiness plan (2026-11-28)

**Project:** *Retrospective Heatwave-Aware Prioritization of Quality-Control Reviews: A Controlled Sensitivity Study Using Public Temperature Observations*.

**Route chosen:** **EGUsphere — Preprints not (immediately) targeting journal publication** (stand-alone preprint). **Do not register as an EGU journal submission** unless the authors explicitly choose that different route. Posting is subject to EGUsphere moderator screening for basic scientific quality, language, and technical compliance; a posted preprint **is not peer-reviewed journal publication**.

Official guidance: [submission requirements](https://www.egusphere.net/preprints/preprint_submission.html), [screening rules](https://www.egusphere.net/preprints/preprint_screening.html), [topics](https://www.egusphere.net/about/egusphere_topics.html), [Copernicus AI policy](https://publications.copernicus.org/for_authors/ai_policy.html), [terms](https://www.egusphere.net/about/general_terms.html).

## Study-specific readiness

- [x] Controlled research experiment v2.1 exists on `main`; archived prior successful GitHub Actions run and audited output CSVs exist.
- [x] Manuscript **working draft** is present at `manuscript/Manuscript_v2.1_Draft.md` (not submission-approved).
- [x] Key limitations are disclosed: NOAA reference already QC screened; all errors, flags and reviewer outcomes are simulated; simulated successful reviews restore reference perfectly; 2023–2025 was used during iterative method development; only 12 station clusters; event-aware score partly aligns with the event-level objective.
- [ ] **Human authors write and validate the final scientific narrative and interpretations.** The current draft was substantially generated with ChatGPT and **must not be submitted as-is** under current Copernicus AI policy (which permits assistive language editing but prohibits AI-generated manuscript text and interpretations). Do not assume an AI-use declaration alone grants permission; contact the publisher for clarification if necessary. Record the actual use accurately.
- [ ] Confirm actual authors, full first names, genuine affiliations and corresponding email; obtain coauthor agreement and any required institutional permissions. Never infer affiliation approval from the public GitHub repository.
- [ ] Audit the paper line-by-line against `v21_trials.csv`, `v21_paired_effects.csv`, `v21_descriptive_summary.csv`, source manifest and v2.1 methods. Report separate outcome components alongside the equal-weight composite.
- [ ] Confirm all reference metadata and claims in original sources (especially 2025–2026 comparators), complete the scientific context and citations.
- [ ] Supply reproducible, permanently accessible code/results snapshot (immutable Git revision, a durable research archive with DOI if possible, source manifests and checksums). GitHub Actions artifacts expire.
- [ ] Complete accurate author contributions, funding, competing interests, code/data availability, acknowledgements and any compliant AI-use statements.
- [ ] Convert the human-authored final manuscript to **official Copernicus Word or LaTeX template**, export a fully readable PDF, and verify **page and line numbers** and full author first names on the title page.
- [ ] Ensure readable figures/tables, accessible figure colors, embedded/standard fonts and proper reproduction rights/credits; submit supplement as PDF or ZIP where appropriate.
- [ ] Prepare abstract for pasting into the submission system, choose at least one official EGUsphere topic, and run the author's final quality and plagiarism/similarity check.
- [ ] Confirm this research is **not simultaneously posted as a preprint on another server**; GitHub source code/manuscript draft alone is not an EGU preprint posting.
- [ ] The corresponding author registers the stand-alone preprint and submits via [EGUsphere's official submission page](https://www.egusphere.net/preprints/preprint_submission.html). Acceptance/posting is decided by moderators, not guaranteed.

## Recommended topic classification

- **Atmospheric sciences → Measurement techniques** or **Meteorology**, for the temperature QC / heatwave use case.
- **Earth & space science informatics → Data, software, and computing infrastructures across earth and space sciences**, for a data quality review framework.

Choose the most applicable one(s) in the actual registration form; moderators can assess fit.

## Scientific framing / claim discipline

This study compares **retrospective** review-prioritization heuristics at matched simulated flags and review budgets, focusing on event-continuity outcomes and the trade-off with corrections of injected point errors. It does not validate a new operational QC detector, real NOAA/BMKG error rates, real expert accuracy, real-time forecasting, or universal superiority. Report exploratory station-cluster bootstrap intervals rather than confirmatory p-value claims. Additional independent-station or lower-error-prevalence checks may strengthen the paper, **but no v3 experiment is required merely to prepare a stand-alone preprint**.

## Submission vs later journal publication

Stand-alone EGUsphere preprints are moderated for basic scientific/technical standards and, once posted, receive a DOI and public discussion; they are **not themselves journal peer review**. Any later EGU journal submission has a separate editor eligibility/review process. Do not double-post the same preprint on another server. Consult current rules at the time of submission.

# Tim’s ExquAIro sandbox

This repository is **Tim Takkenkamp’s fork** of the ExquAIro / Lifelines bootcamp project:

- Playground: https://github.com/timtakkenkamp/exquairo-apex-lifelines
- Upstream (reference only): `kyliekeijzer/exquairo-apex-lifelines`

Work here is for product exploration and later ML on this fork. It must not change colleagues’ modeling on the upstream repo.

## Coordinator role

A Cursor cloud agent acts as **sandbox coordinator** for Tim on this fork only.

Hard rules:

- Push and open PRs **only** against `timtakkenkamp/exquairo-apex-lifelines`.
- Never push to `kyliekeijzer/exquairo-apex-lifelines` and never open PRs against Kylie’s repo.
- Treat upstream as read-only reference (ideas, data conventions, preprocessing stubs).
- Do **not** train models or change clinical claims unless Tim asks in a follow-up.
- Team data-cleaning decisions stay separate. This sandbox may copy ideas; it must not block colleagues.

## Product-first, model-later

Near-term focus is presentation + product: an **electronic buddy** for patients.

Intended patient experience (mock first, now runnable):

1. Two pictures: **korte-termijn** and **lange-termijn risico op diabetes** (mock proxy: HbA1c > 6.5%).
2. Top **patient-specific** risk factors (local importance, not a global list).
3. Linked lifestyle intervention cards with theme colours.
4. Weight / BMI what-if that moves the mock percentages and BMI/waist bars.

Run the demo: `uv run streamlit run product/buddy/app.py`

Later, an ML/DL model can feed the same buddy UI through a **stable JSON contract**. The UI should not need a redesign when the mock is swapped for a model API.

See `product/buddy/` for the vision, example payload, and demo personas.

## Repo snapshot (coordinator notes)

Inspected on bootstrap. Do not treat this as a license to rewrite shared modeling files.

| Area | What is here |
| --- | --- |
| Setup | `uv sync` + `.venv` kernel; Python `>=3.12` (`README.md`, `pyproject.toml`) |
| Raw data | `data/raw/exquairo_ai_bootcamp_synth_dataset.csv` — 17 960 × 100, separator `;` |
| Team filtered set | `data/processed/df_filtered.xlsx` — team cleaning artifact; copy ideas only |
| Preprocessing stub | `Scripts and Notebooks/preprocessing.py` — commented `load_and_clean` / `split_data` / `scale_data` / `get_data` |
| Notebooks | `Scripts and Notebooks/discovery.ipynb` — NSES parse/impute discovery (Martijn) |
| Diabetes-relevant columns (raw) | `HBAC_*`, `HB1C_*`, `GLU_*`, `BMI_*`, `SMOKING`, `SPORTS_T1`, family T2DM flags, diet/activity fields |

HbA1c-style fields in the synth table include `HBAC_T1` / `HBAC_T2` / `HBAC_T3` (percent-like values such as 5.5) and `HB1C_*` (mmol/mol-like). Patient-facing titles are short- and long-term diabetes risk; the locked mock proxy underneath is still **HbA1c > 6.5%** — not a validated clinical claim.

## What this sandbox will not do by default

- Train or evaluate models.
- Rewrite `preprocessing.py` or the team filtered workbook as a shared source of truth.
- State that a score is a real medical diagnosis or prognosis.

## Asking the coordinator for next work

Typical follow-ups Tim can request on this fork:

- Polish the Streamlit buddy (`product/buddy/app.py`) for a live audience.
- Tighten schema `0.2.0` once the colleagues’ model feature list is frozen.
- Later: a model API that emits the same contract (still fork-only).

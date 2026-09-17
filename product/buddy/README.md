# Electronic buddy (product scaffold)

Working proposal for this fork: a patient-facing **electronic buddy** that presents personal diabetes / unfavorable-HbA1c risk, the top patient-specific drivers, and a few linked lifestyle interventions.

This folder is **product-first**. The first usable artifact is a mock UI plus a stable JSON contract. A model comes later and must fit the contract, not the other way around.

Nothing here is a clinical claim. Demo numbers and copy are placeholders.

## Intended experience

The buddy shows three things on one screen:

1. **Risk** — chance of unfavorable HbA1c (working proxy: e.g. ≥6.5%) as a percentage plus a short label (`low` / `moderate` / `high`).
2. **Why you** — top local (patient-specific) factors, not only a global feature-importance list.
3. **What you can try** — intervention cards tied to those factors (activity, diet pattern, smoking, sleep, etc.).

Later, an ML/DL model can populate the same three panels. The UI should keep working if `source` flips from `mock` to `model`.

## Phased plan

### Phase 1 — Mock UI

- Read `contract.example.json` (and later persona-specific fixtures).
- Render risk %, label, factor list, and intervention cards.
- Suggested first implementation: Streamlit app under this folder (not started yet).
- Personas in `personas.md` drive the demo, not real patients.

### Phase 2 — JSON contract

- Keep a versioned payload (`schema_version`) with at least:
  - `risk_score` (0–1 probability)
  - `risk_label`
  - `top_factors[]` (id, label, direction, local importance, optional patient value)
  - `interventions[]` (id, title, summary, linked factor ids)
- UI consumes only this shape.
- Mock writer and future model API share the same example as the source of truth.

### Phase 3 — Model API

- Predict the unfavorable-HbA1c (or agreed diabetes-proxy) target on Tim’s sandbox data only.
- Return local explanations (e.g. per-patient attributions) mapped into `top_factors`.
- Map factor ids to intervention cards; do not invent new clinical claims in the UI.
- Swap the mock loader for an HTTP/local function that returns the same JSON.

## Out of scope for this scaffold

- Training or evaluating models.
- Changing team preprocessing or the filtered workbook used by colleagues.
- Pushing any of this to the upstream (`kyliekeijzer`) repo.

## Files

| File | Role |
| --- | --- |
| `contract.example.json` | Example buddy payload |
| `personas.md` | Demo patients for mock UI |
| `README.md` | This vision + plan |

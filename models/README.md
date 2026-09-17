# Models (from upstream Kylie)

Copied from `kyliekeijzer/exquairo-apex-lifelines` (`first models`, ~2026-09-17).

| File | Role |
|------|------|
| `model_a_best_logreg_elasticnet.joblib` | Model A — short horizon (T1→T2), best elastic-net logistic regression pipeline |
| `model_b_best_logreg_elasticnet.joblib` | Model B — long horizon (T1→T3), same family |

These are sklearn pipelines (include preprocessing / SMOTE via `imblearn`). To load locally:

```bash
uv add scikit-learn imbalanced-learn joblib
uv run python -c "import joblib; print(joblib.load('models/model_a_best_logreg_elasticnet.joblib'))"
```

**Step 1 only:** artefacts on Tim’s fork for Boris buddy integration. Wiring into the UI = later step.

## Step 2 — adapter

- `product/buddy/model_adapter.py` — load A/B joblibs, build 23 features (+ missing flags), `predict_diabetes_risks(row)`.
- `product/buddy/smoke_models.py` — smoke on 3 rows from `data/processed/df_filtered.xlsx`.

```bash
cd product/buddy && uv run python smoke_models.py
```

Not wired into Streamlit yet (step 3). Note: elastic-net may shrink some coefficients (e.g. BMI) near zero on model A — what-if on that feature can look flat for T1→T2 while T1→T3 still moves.

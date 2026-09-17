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

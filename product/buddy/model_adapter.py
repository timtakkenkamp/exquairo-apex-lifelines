"""Adapter: Kylie A/B joblib models → Boris buddy risk payload (step 2)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[2]
MODELS_DIR = REPO_ROOT / "models"

# Exact feature order expected by both elastic-net pipelines
FEATURE_COLS: list[str] = [
    "AGE_T1",
    "BMI_T1",
    "HIP_T1",
    "WAIST_T1",
    "EDUCATION_LOWER_T1",
    "HBF_T1",
    "MAP_T1",
    "HTN_MED_T1",
    "BKR_T1",
    "CHO_T1",
    "HBAC_T1",
    "HDC_T1",
    "LDC_T1",
    "TGL_T1",
    "RESPIRATORY_DISEASE_T1",
    "SPORTS_T1",
    "DEPRESSION_T1",
    "EDUCATION_LOWER_T1_MISSING",
    "HBF_T1_MISSING",
    "MAP_T1_MISSING",
    "HTN_MED_T1_MISSING",
    "RESPIRATORY_DISEASE_T1_MISSING",
    "SPORTS_T1_MISSING",
]

# Core columns that may be missing in raw rows → companion *_MISSING flags
_CORE_WITH_MISSING_FLAG = [
    "EDUCATION_LOWER_T1",
    "HBF_T1",
    "MAP_T1",
    "HTN_MED_T1",
    "RESPIRATORY_DISEASE_T1",
    "SPORTS_T1",
]

_FRIENDLY = {
    "AGE_T1": ("Leeftijd", "jaar"),
    "BMI_T1": ("BMI", "kg/m²"),
    "HIP_T1": ("Heupomtrek", "cm"),
    "WAIST_T1": ("Taille", "cm"),
    "EDUCATION_LOWER_T1": ("Lagere opleiding", ""),
    "HBF_T1": ("Vetpercentage", "%"),
    "MAP_T1": ("Bloeddruk (MAP)", "mmHg"),
    "HTN_MED_T1": ("Bloeddrukmedicatie", ""),
    "BKR_T1": ("Kreatinine", ""),
    "CHO_T1": ("Cholesterol", "mmol/L"),
    "HBAC_T1": ("HbA1c", "%"),
    "HDC_T1": ("HDL", "mmol/L"),
    "LDC_T1": ("LDL", "mmol/L"),
    "TGL_T1": ("Triglyceriden", "mmol/L"),
    "RESPIRATORY_DISEASE_T1": ("Luchtwegziekte", ""),
    "SPORTS_T1": ("Sport", ""),
    "DEPRESSION_T1": ("Depressie", ""),
}


@lru_cache(maxsize=1)
def load_models(
    models_dir: str | None = None,
) -> tuple[Any, Any]:
    root = Path(models_dir) if models_dir else MODELS_DIR
    model_a = joblib.load(root / "model_a_best_logreg_elasticnet.joblib")
    model_b = joblib.load(root / "model_b_best_logreg_elasticnet.joblib")
    return model_a, model_b


def prepare_features(row: pd.Series | dict[str, Any]) -> pd.DataFrame:
    """Build a 1×23 frame with missing flags; fill remaining NaNs with 0 after flags."""
    s = pd.Series(row) if not isinstance(row, pd.Series) else row
    data: dict[str, float] = {}
    for col in FEATURE_COLS:
        if col.endswith("_MISSING"):
            continue
        if col in s.index:
            val = s[col]
            data[col] = float(val) if pd.notna(val) else np.nan
        else:
            data[col] = np.nan

    for core in _CORE_WITH_MISSING_FLAG:
        flag = f"{core}_MISSING"
        if flag in s.index and pd.notna(s[flag]):
            data[flag] = float(s[flag])
        else:
            data[flag] = 1.0 if pd.isna(data.get(core, np.nan)) else 0.0
        if pd.isna(data.get(core, np.nan)):
            data[core] = 0.0

    # Any other NaNs (labs etc.) → 0 for v1 smoke; flags only for the six above
    for col in FEATURE_COLS:
        if col not in data or pd.isna(data[col]):
            data[col] = 0.0

    return pd.DataFrame([[data[c] for c in FEATURE_COLS]], columns=FEATURE_COLS)


def _local_factor_contributions(model: Any, X: pd.DataFrame, top_k: int = 5) -> list[dict[str, Any]]:
    """Approximate local contributions: coef × scaled feature value (logreg)."""
    clf = model.named_steps["clf"]
    pre = model.named_steps["preprocessor"]
    Xs = pre.transform(X)
    if hasattr(Xs, "toarray"):
        Xs = Xs.toarray()
    coefs = np.asarray(clf.coef_).ravel()
    x = np.asarray(Xs).ravel()
    contrib = coefs * x
    # map back to feature names in ColumnTransformer order
    try:
        names = list(pre.get_feature_names_out())
        # names like num__AGE_T1
        names = [n.split("__", 1)[-1] for n in names]
    except Exception:
        names = FEATURE_COLS[: len(coefs)]

    items = []
    for name, c, raw in zip(names, contrib, X.iloc[0]):
        if name.endswith("_MISSING"):
            continue
        label, unit = _FRIENDLY.get(name, (name, ""))
        items.append(
            {
                "id": name,
                "label": label,
                "unit": unit,
                "patient_value": float(raw),
                "contribution": float(c),
                "direction": "increases_risk" if c > 0 else "decreases_risk",
            }
        )
    items.sort(key=lambda d: abs(d["contribution"]), reverse=True)
    top = items[:top_k]
    total = sum(abs(d["contribution"]) for d in top) or 1.0
    for d in top:
        d["share"] = abs(d["contribution"]) / total
    return top


def predict_diabetes_risks(
    row: pd.Series | dict[str, Any],
    *,
    models_dir: str | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """
    Returns a buddy-oriented payload fragment:
      risk_t1_t2, risk_t1_t3, top_factors (from model A contributions), feature_frame used
    """
    model_a, model_b = load_models(models_dir)
    X = prepare_features(row)
    p_a = float(model_a.predict_proba(X)[0, 1])
    p_b = float(model_b.predict_proba(X)[0, 1])
    factors = _local_factor_contributions(model_a, X, top_k=top_k)
    return {
        "schema_version": "0.3.0-live",
        "source": "kylie_logreg_elasticnet_ab",
        "risk_t1_t2": p_a,
        "risk_t1_t3": p_b,
        "risks": [
            {
                "id": "t1_t2",
                "label": "Korte termijn",
                "risk_score": p_a,
                "risk_label": _band(p_a),
            },
            {
                "id": "t1_t3",
                "label": "Lange termijn",
                "risk_score": p_b,
                "risk_label": _band(p_b),
            },
        ],
        "top_factors": factors,
        "features_used": FEATURE_COLS,
    }


def _band(p: float) -> str:
    if p < 0.1:
        return "low"
    if p < 0.25:
        return "medium"
    return "high"

"""Smoke-test Kylie models via model_adapter (step 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from model_adapter import FEATURE_COLS, predict_diabetes_risks, prepare_features

ROOT = Path(__file__).resolve().parents[2]
FILTERED = ROOT / "data" / "processed" / "df_filtered.xlsx"


def main() -> None:
    df = pd.read_excel(FILTERED)
    # three diverse rows by BMI tertiles among complete-ish HBAC
    ok = df["HBAC_T1"].notna() & df["BMI_T1"].notna()
    sub = df.loc[ok].copy()
    sub["bmi_q"] = pd.qcut(sub["BMI_T1"], 3, labels=["low_bmi", "mid_bmi", "high_bmi"])
    rows = []
    for label in ["low_bmi", "mid_bmi", "high_bmi"]:
        part = sub.loc[sub["bmi_q"] == label]
        rows.append(part.iloc[len(part) // 2])

    print("Smoke predict (3 rows from df_filtered.xlsx)\n")
    results = []
    for i, row in enumerate(rows, 1):
        out = predict_diabetes_risks(row, top_k=5)
        print(f"[{i}] BMI={row['BMI_T1']:.1f}  HBAC={row['HBAC_T1']:.2f}")
        print(f"    T1→T2 (kort)={out['risk_t1_t2']:.4f}  T1→T3 (lang)={out['risk_t1_t3']:.4f}")
        print(f"    top factors: " + ", ".join(f"{f['label']} ({f['direction'][:3]})" for f in out["top_factors"][:3]))
        results.append(
            {
                "bmi": float(row["BMI_T1"]),
                "hbac": float(row["HBAC_T1"]),
                "risk_t1_t2": out["risk_t1_t2"],
                "risk_t1_t3": out["risk_t1_t3"],
                "top": [f["id"] for f in out["top_factors"]],
            }
        )
        # what-if: +5 kg approx via BMI bump if height known — use WAIST/BMI only
        bumped = row.copy()
        bumped["BMI_T1"] = float(row["BMI_T1"]) + 2.0
        out2 = predict_diabetes_risks(bumped, top_k=3)
        print(f"    what-if BMI+2 → kort={out2['risk_t1_t2']:.4f} lang={out2['risk_t1_t3']:.4f}")
        assert 0.0 <= out["risk_t1_t2"] <= 1.0
        assert 0.0 <= out["risk_t1_t3"] <= 1.0
        assert out2["risk_t1_t2"] >= out["risk_t1_t2"] - 1e-9  # usually rises

    # feature matrix shape check
    X = prepare_features(rows[0])
    assert list(X.columns) == FEATURE_COLS
    assert X.shape == (1, 23)
    print("\nOK — adapter smoke passed.")
    out_path = ROOT / "product" / "buddy" / "smoke_models_last.json"
    out_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()

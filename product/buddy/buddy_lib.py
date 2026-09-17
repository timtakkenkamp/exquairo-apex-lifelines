"""Mock buddy helpers: fixture loading, coaching copy, medical-question guardrails."""

from __future__ import annotations

import copy
import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = ROOT / "fixtures"
EXAMPLE_CONTRACT = ROOT / "contract.example.json"

RISK_ORDER = {"low": 0, "medium": 1, "high": 2}

THEME_META = {
    "sport": {"label": "Beweging", "token": "sport"},
    "food": {"label": "Voeding", "token": "food"},
    "sleep": {"label": "Slaap", "token": "sleep"},
    "smoking": {"label": "Rookvrij", "token": "smoking"},
    "alcohol": {"label": "Alcohol", "token": "alcohol"},
}

FACTOR_DIRECTION_NL = {
    "increases_risk": "verhoogt je risico op diabetes",
    "decreases_risk": "verlaagt je risico op diabetes",
}

RISK_BAND_NL = {
    "low": "laag",
    "medium": "middel",
    "high": "hoog",
}

FACTOR_LABEL_NL = {
    "bmi": "BMI",
    "weight": "Gewicht",
    "waist": "Tailleomvang",
    "sports": "Sport / beweging",
    "family_t2dm": "Familiegeschiedenis type 2 diabetes",
    "sleep": "Slaap",
    "smoking": "Roken",
    "alcohol": "Alcoholpatroon",
    "cycle_commute": "Fietsen naar werk",
    "kcal": "Energie-inname",
}

# Patient-facing titles. Internal ids stay t1_t2 / t1_t3 (HbA1c > 6.5% mock proxy).
PATIENT_RISK_COPY = {
    "t1_t2": {
        "title": "Korte-termijn risico op diabetes",
        "subtitle": "Demo-proxy: kans dat HbA1c boven 6,5% uitkomt. Geen diagnose.",
    },
    "t1_t3": {
        "title": "Lange-termijn risico op diabetes",
        "subtitle": "Demo-proxy: kans dat HbA1c boven 6,5% uitkomt. Geen diagnose.",
    },
}

# What-if heuristic (transparent mock — not a trained model):
#   BMI = weight_kg / (height_m ** 2)
#   short_term = clip(base_short + 0.025 * (BMI - BMI0), 0.02, 0.95)
#   long_term  = clip(base_long  + 0.035 * (BMI - BMI0), 0.03, 0.97)
# Long-term moves a bit more so the two cards stay distinct in the demo.
# BMI factor: importance = clip(base + 0.045 * (BMI - BMI0), 0.04, 0.70);
#   direction flips at BMI 25 (below → lowers, at/above → raises).
# Waist (if present): cm' = cm0 + 0.7 * (kg - kg0);
#   importance = clip(base + 0.012 * (cm' - cm0), 0.04, 0.50).
SHORT_TERM_BMI_COEF = 0.025
LONG_TERM_BMI_COEF = 0.035
BMI_FACTOR_COEF = 0.045
WAIST_CM_PER_KG = 0.7
WAIST_FACTOR_COEF = 0.012
BMI_DIRECTION_PIVOT = 25.0
WEIGHT_LINKED_FACTORS = {"bmi", "waist", "weight"}

# Lifestyle coaching only. Medical / diagnosis / medication / triage → deflect.
_MEDICAL_RE = re.compile(
    r"\b("
    r"medicin\w*|medication\w*|meds|pill\w*|tablet\w*|drug\w*|dosage|dose|"
    r"prescrib\w*|prescription|pharmacy|"
    r"metformin|insulin|ozempic|wegovy|semaglutide|statin\w*|glp-?1|"
    r"diagnos\w*|diabetic|do i have|am i sick|"
    r"triage|emergenc\w*|chest pain|ambulance|a&e|er visit|hospital|"
    r"blood test result|lab result|treat my|cure|symptom\w*"
    r")\b",
    re.IGNORECASE,
)

DEFLECT_MESSAGE = (
    "I am a lifestyle buddy, not a clinician. I cannot diagnose, prescribe, "
    "or triage. Please take questions about medications, test results, or "
    "symptoms to your care provider. I can still help with everyday movement, "
    "meals, sleep, smoking, and alcohol habits."
)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_personas() -> list[dict[str, Any]]:
    paths = sorted(FIXTURES_DIR.glob("persona-*.json"))
    if not paths:
        return [load_payload(EXAMPLE_CONTRACT)]
    return [load_payload(p) for p in paths]


def validate_payload(data: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    patient = data.get("patient") or {}
    if not patient.get("persona_id"):
        errors.append("missing patient.persona_id")
    target = data.get("target") or {}
    if target.get("threshold") != ">6.5%":
        errors.append("target.threshold must be >6.5%")
    risks = data.get("risks") or []
    ids = {r.get("id") for r in risks}
    if ids != {"t1_t2", "t1_t3"}:
        errors.append("risks must include t1_t2 and t1_t3 only")
    for risk in risks:
        score = risk.get("risk_score")
        label = risk.get("risk_label")
        if not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            errors.append(f"invalid risk_score on {risk.get('id')}")
        if label not in RISK_ORDER:
            errors.append(f"risk_label must be low/medium/high on {risk.get('id')}")
    factors = data.get("top_factors") or []
    if not 3 <= len(factors) <= 5:
        errors.append("top_factors must have 3–5 items")
    for factor in factors:
        if factor.get("direction") not in {"increases_risk", "decreases_risk"}:
            errors.append(f"bad direction on {factor.get('id')}")
        imp = factor.get("importance")
        if not isinstance(imp, (int, float)) or not 0 <= float(imp) <= 1:
            errors.append(f"invalid importance on {factor.get('id')}")
    if not data.get("interventions"):
        errors.append("missing interventions")
    return errors


def is_medical_or_triage(text: str) -> bool:
    return bool(_MEDICAL_RE.search(text or ""))


def pct(score: float) -> str:
    return f"{round(float(score) * 100)}%"


def factor_display_label(factor: dict[str, Any]) -> str:
    return FACTOR_LABEL_NL.get(factor.get("id"), factor.get("label") or factor.get("id") or "")


def factor_direction_nl(direction: str) -> str:
    return FACTOR_DIRECTION_NL.get(direction, FACTOR_DIRECTION_NL["increases_risk"])


def risk_band_nl(label: str) -> str:
    return RISK_BAND_NL.get(label, label)


def factor_share(factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize local importances so bars are comparable within this persona."""
    total = sum(float(f.get("importance") or 0) for f in factors) or 1.0
    out = []
    for factor in factors:
        item = dict(factor)
        item["share"] = float(factor.get("importance") or 0) / total
        out.append(item)
    out.sort(key=lambda f: f["share"], reverse=True)
    return out


def clip(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def risk_band(score: float) -> str:
    if score < 0.20:
        return "low"
    if score < 0.55:
        return "medium"
    return "high"


def _as_float(value: Any, default: float | None = None) -> float | None:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def persona_body(payload: dict[str, Any]) -> dict[str, float]:
    """Baseline height / weight / BMI / waist for the what-if control."""
    patient = payload.get("patient") or {}
    snap = patient.get("snapshot") or {}
    height_cm = _as_float(patient.get("height_cm"), 170.0) or 170.0
    bmi = _as_float(patient.get("bmi")) or _as_float(snap.get("bmi"), 25.0) or 25.0
    weight_kg = _as_float(patient.get("weight_kg"))
    if weight_kg is None:
        weight_kg = bmi * (height_cm / 100.0) ** 2
    waist_cm = None
    for factor in payload.get("top_factors") or []:
        if factor.get("id") == "waist":
            waist_cm = _as_float(factor.get("patient_value"))
            break
    if waist_cm is None:
        waist_cm = _as_float(snap.get("waist"))
    return {
        "height_cm": height_cm,
        "weight_kg": weight_kg,
        "bmi": bmi,
        "waist_cm": float(waist_cm) if waist_cm is not None else float("nan"),
    }


def apply_weight_whatif(
    payload: dict[str, Any],
    *,
    weight_kg: float | None = None,
    bmi: float | None = None,
) -> dict[str, Any]:
    """Return a copy of the persona with mock risks and weight-linked factors updated.

    Formula (documented for the demo; not a clinical model):
        BMI = kg / m^2
        short = clip(base_short + 0.025 * dBMI, 0.02, 0.95)
        long  = clip(base_long  + 0.035 * dBMI, 0.03, 0.97)
        BMI bar grows/shrinks by 0.045 * dBMI; waist tracks 0.7 cm per kg.
    """
    updated = copy.deepcopy(payload)
    body = persona_body(payload)
    height_m = body["height_cm"] / 100.0
    if height_m <= 0:
        height_m = 1.7
    if bmi is not None and weight_kg is None:
        new_bmi = float(bmi)
        new_weight = new_bmi * height_m**2
    else:
        new_weight = float(weight_kg if weight_kg is not None else body["weight_kg"])
        new_bmi = new_weight / height_m**2
    new_weight = clip(new_weight, 35.0, 180.0)
    new_bmi = clip(new_bmi, 15.0, 55.0)
    delta_bmi = new_bmi - body["bmi"]
    delta_kg = new_weight - body["weight_kg"]

    for risk in updated.get("risks") or []:
        base = float(risk["risk_score"])
        coef = SHORT_TERM_BMI_COEF if risk.get("id") == "t1_t2" else LONG_TERM_BMI_COEF
        lo, hi = (0.02, 0.95) if risk.get("id") == "t1_t2" else (0.03, 0.97)
        score = clip(base + coef * delta_bmi, lo, hi)
        copy_bits = PATIENT_RISK_COPY.get(risk.get("id"), {})
        risk["risk_score"] = round(score, 4)
        risk["risk_label"] = risk_band(score)
        risk["horizon"] = copy_bits.get("title", risk.get("horizon"))
        risk["label"] = copy_bits.get("subtitle", risk.get("label"))

    new_waist = None
    if body["waist_cm"] == body["waist_cm"]:  # not NaN
        new_waist = clip(body["waist_cm"] + WAIST_CM_PER_KG * delta_kg, 50.0, 180.0)

    for factor in updated.get("top_factors") or []:
        fid = factor.get("id")
        if fid not in WEIGHT_LINKED_FACTORS:
            continue
        base_imp = float(factor.get("importance") or 0)
        if fid in {"bmi", "weight"}:
            factor["importance"] = round(clip(base_imp + BMI_FACTOR_COEF * delta_bmi, 0.04, 0.70), 4)
            factor["direction"] = (
                "increases_risk" if new_bmi >= BMI_DIRECTION_PIVOT else "decreases_risk"
            )
            if fid == "bmi":
                factor["patient_value"] = f"{new_bmi:.1f}"
                factor["unit"] = "kg/m²"
            else:
                factor["patient_value"] = f"{new_weight:.1f}"
                factor["unit"] = "kg"
            factor["note"] = "Mock what-if contribution — not a trained attribution."
        elif fid == "waist" and new_waist is not None:
            d_waist = new_waist - body["waist_cm"]
            factor["importance"] = round(clip(base_imp + WAIST_FACTOR_COEF * d_waist, 0.04, 0.50), 4)
            factor["direction"] = "increases_risk" if new_waist >= 88 else "decreases_risk"
            factor["patient_value"] = f"{new_waist:.0f}"
            factor["unit"] = "cm"
            factor["note"] = "Waist tracks weight in this mock (0.7 cm per kg)."

    patient = updated.setdefault("patient", {})
    snap = patient.setdefault("snapshot", {})
    snap["bmi"] = f"{new_bmi:.1f}"
    snap["weight"] = f"{new_weight:.1f} kg"
    if new_waist is not None:
        snap["waist"] = f"{new_waist:.0f} cm"
    patient["weight_kg"] = round(new_weight, 1)
    patient["bmi"] = round(new_bmi, 1)
    updated["whatif"] = {
        "weight_kg": round(new_weight, 1),
        "bmi": round(new_bmi, 1),
        "height_cm": body["height_cm"],
        "delta_kg": round(delta_kg, 1),
        "delta_bmi": round(delta_bmi, 2),
        "active": abs(delta_kg) >= 0.25,
    }
    return updated


def template_reply(question: str, payload: dict[str, Any]) -> str:
    q = (question or "").lower()
    interventions = payload.get("interventions") or []
    theme_hits = {
        "sport": ("walk", "sport", "move", "activ", "cycl", "bike", "exercise"),
        "food": ("eat", "food", "meal", "drink", "sugar", "diet", "plate"),
        "sleep": ("sleep", "bed", "wind-down", "insomnia"),
        "smoking": ("smok", "cigarette", "vape"),
        "alcohol": ("alcohol", "drink", "beer", "wine"),
    }
    for intervention in interventions:
        theme = intervention.get("theme")
        needles = theme_hits.get(theme, ())
        if any(n in q for n in needles):
            return (
                f"{intervention['title']}: {intervention['summary']} "
                "Dit is leefstijlcoaching, geen medisch advies."
            )
    coaching = (payload.get("coaching") or {}).get("template")
    if coaching:
        return coaching
    return (
        "Let's keep this practical: pick one movement habit and one food habit "
        "you can repeat this week. Your care provider stays the place for medical questions."
    )


def optional_llm_reply(question: str, payload: dict[str, Any], fallback: str) -> tuple[str, str]:
    """Return (text, source). Uses OpenAI only when OPENAI_API_KEY is already set."""
    api_key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not api_key:
        return fallback, "template"

    name = (payload.get("patient") or {}).get("display_name", "there")
    system = (
        "You are a calm lifestyle coaching buddy in a demo app. "
        "Speak in 2–4 short sentences. Motivating, not over-the-top. "
        "Never diagnose, prescribe, dose, or triage. "
        "If the user asks about medication, symptoms, diagnosis, or emergencies, "
        "deflect to their care provider. Lifestyle only: movement, food, sleep, "
        f"smoking, alcohol. The patient's demo name is {name}."
    )
    body = json.dumps(
        {
            "model": "gpt-4o-mini",
            "temperature": 0.4,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": question},
            ],
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        text = data["choices"][0]["message"]["content"].strip()
        return text or fallback, "openai"
    except (urllib.error.URLError, TimeoutError, KeyError, IndexError, json.JSONDecodeError):
        return fallback, "template"


def answer_question(question: str, payload: dict[str, Any]) -> tuple[str, str]:
    text = (question or "").strip()
    if not text:
        return "Ask about a daily habit — walking, meals, sleep, smoking, or alcohol.", "empty"
    if is_medical_or_triage(text):
        return DEFLECT_MESSAGE, "guardrail"
    fallback = template_reply(text, payload)
    return optional_llm_reply(text, payload, fallback)

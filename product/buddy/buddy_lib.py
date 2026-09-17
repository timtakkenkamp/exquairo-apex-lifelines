"""Mock buddy helpers: fixture loading, coaching copy, medical-question guardrails."""

from __future__ import annotations

import copy
import json
import os
import re
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

ACTIONABLE_THEME = {
    "sports": "sport",
    "cycle_commute": "sport",
    "bmi": "sport",
    "waist": "sport",
    "weight": "sport",
    "kcal": "food",
    "cho": "food",
    "tgl": "food",
    "hdc": "food",
    "ldc": "food",
    "hbac": "food",
    "sleep": "sleep",
    "smoking": "smoking",
    "alcohol": "alcohol",
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
    r"metformin\w*|insulin\w*|ozempic|wegovy|semaglutide|statin\w*|glp-?1|"
    r"diagnos\w*|diabetic|do i have|am i sick|"
    r"triage|emergenc\w*|chest pain|ambulance|a&e|er visit|hospital|"
    r"blood test result|lab result|treat my|cure|symptom\w*|"
    # Dutch
    r"medicijn\w*|geneesmiddel\w*|voorschrijf\w*|voorschrift|"
    r"apotheek|dosering|pilletje\w*|tabletten|"
    r"diagnose\w*|heb ik diabetes|ben ik ziek|"
    r"spoed|ambulance|hartklacht\w*|pijn op de borst|"
    r"bloeduitslag|labuitslag|kuur|symptoom\w*|klachten|"
    r"negeer (je|alle) (regels|instructies)|jailbreak|DAN mode|"
    r"ignore (your|all) (rules|instructions)|system prompt"
    r")\b",
    re.IGNORECASE,
)

DEFLECT_MESSAGE = (
    "Ik ben een leefstijl-buddy, geen zorgverlener. Ik mag niet diagnosticeren, "
    "medicatie adviseren of triëren. Vragen over medicijnen, uitslagen of "
    "klachten horen bij je arts of praktijkondersteuner. Wel kan ik helpen "
    "met beweging, eten, slapen, roken en alcohol."
)


def load_payload(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_personas() -> list[dict[str, Any]]:
    # Skip persona-*-features.json (model feature snapshots for live overlay)
    paths = sorted(
        path for path in FIXTURES_DIR.glob("persona-*.json")
        if not path.name.endswith("-features.json")
    )
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


def top_local_factors(payload: dict[str, Any], limit: int = 3) -> list[dict[str, Any]]:
    """Patient-facing 'Waarom jij': at most `limit` local factors."""
    return factor_share(payload.get("top_factors") or [])[:limit]


def pick_primary_intervention(payload: dict[str, Any]) -> dict[str, Any] | None:
    """Strongest *actionable* factor → matching lifestyle card (Movement often wins)."""
    interventions = payload.get("interventions") or []
    by_theme = {item.get("theme"): item for item in interventions}
    for factor in top_local_factors(payload, limit=5):
        theme = ACTIONABLE_THEME.get(factor.get("id"))
        if theme and theme in by_theme:
            return by_theme[theme]
    return by_theme.get("sport") or (interventions[0] if interventions else None)


def secondary_interventions(payload: dict[str, Any], primary: dict[str, Any] | None, limit: int = 2) -> list[dict[str, Any]]:
    primary_id = (primary or {}).get("id")
    extras = [item for item in payload.get("interventions") or [] if item.get("id") != primary_id]
    return extras[:limit]


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
        "sport": (
            "walk",
            "wandel",
            "sport",
            "beweeg",
            "beweg",
            "fiets",
            "move",
            "activ",
            "cycl",
            "bike",
            "exercise",
        ),
        "food": (
            "eat",
            "eet",
            "eten",
            "voeding",
            "maaltijd",
            "suiker",
            "food",
            "meal",
            "sugar",
            "diet",
            "plate",
        ),
        "sleep": ("sleep", "slaap", "bed", "avondritueel", "wind-down", "insomnia"),
        "smoking": ("smok", "rook", "roken", "sigaret", "cigarette", "vape"),
        "alcohol": ("alcohol", "bier", "wijn", "beer", "wine"),
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
        "Houd het klein: kies deze week één bewegingsgewoonte en één eetgewoonte "
        "die je kunt herhalen. Voor medicijnen of klachten blijf je bij je zorgverlener."
    )


OPENAI_MODEL = "gpt-4o-mini"
OPENAI_AUTH_MESSAGE = (
    "Die OpenAI-sleutel wordt niet geaccepteerd. Plak een geldige key "
    "(begint meestal met sk-) in de sidebar of in .streamlit/secrets.toml."
)


def resolve_openai_api_key(*candidates: str | None) -> str:
    """First non-empty candidate, then OPENAI_API_KEY from the environment."""
    for raw in candidates:
        if raw and str(raw).strip():
            return str(raw).strip()
    return os.environ.get("OPENAI_API_KEY", "").strip()


def openai_key_configured(*candidates: str | None) -> bool:
    return bool(resolve_openai_api_key(*candidates))


def _coach_system_prompt(payload: dict[str, Any]) -> str:
    patient = payload.get("patient") or {}
    name = patient.get("display_name") or "daar"
    risks = {r.get("id"): r for r in payload.get("risks") or []}
    short = risks.get("t1_t2") or {}
    longr = risks.get("t1_t3") or {}
    factor_lines = []
    for factor in top_local_factors(payload, 3):
        factor_lines.append(
            f"- {factor_display_label(factor)}: {factor_direction_nl(factor.get('direction'))}"
        )
    primary = pick_primary_intervention(payload)
    step = (
        f"{primary['title']}: {primary.get('summary') or ''}"
        if primary
        else "Een kleine leefstijlstap die je kunt herhalen."
    )
    return (
        "Je bent Boris, een kalme leefstijl-buddy in een demo-app.\n"
        "Antwoord altijd in het Nederlands, in 2–4 korte zinnen. Warm, niet overdreven.\n"
        "Nooit diagnosticeren, medicatie adviseren, doseren of triëren.\n"
        "Bij medicijnen, uitslagen, symptomen of spoed: verwijs naar de arts "
        "of praktijkondersteuner en geef geen dosering.\n"
        "Alleen coaching over beweging, eten, slapen, roken en alcohol.\n"
        "Cijfers hier zijn een demo-proxy, geen diagnose.\n"
        f"Patiënt in deze demo: {name}.\n"
        f"Korte-termijn risico: {pct(short.get('risk_score') or 0)} "
        f"({risk_band_nl(short.get('risk_label') or 'medium')}).\n"
        f"Lange-termijn risico: {pct(longr.get('risk_score') or 0)} "
        f"({risk_band_nl(longr.get('risk_label') or 'medium')}).\n"
        "Waarom deze persoon:\n"
        + ("\n".join(factor_lines) or "- (geen lokale factoren)")
        + f"\nEerste stap die de app voorstelt: {step}\n"
    )


def optional_llm_reply(
    question: str,
    payload: dict[str, Any],
    fallback: str,
    *,
    api_key: str | None = None,
    history: list[tuple[str, str]] | None = None,
) -> tuple[str, str]:
    """Return (text, source). Uses the official OpenAI client when a key is present."""
    key = resolve_openai_api_key(api_key)
    if not key:
        return fallback, "template"

    try:
        from openai import OpenAI
    except ImportError:
        return fallback, "template"

    messages: list[dict[str, str]] = [{"role": "system", "content": _coach_system_prompt(payload)}]
    for prior_q, prior_a in (history or [])[-6:]:
        if prior_q:
            messages.append({"role": "user", "content": prior_q})
        if prior_a:
            messages.append({"role": "assistant", "content": prior_a})
    messages.append({"role": "user", "content": question})

    try:
        client = OpenAI(api_key=key, timeout=12.0)
        response = client.chat.completions.create(
            model=os.environ.get("OPENAI_MODEL", OPENAI_MODEL),
            temperature=0.4,
            messages=messages,
        )
        text = ((response.choices[0].message.content) or "").strip()
        return text or fallback, "openai"
    except Exception as exc:
        blob = f"{type(exc).__name__} {exc}".lower()
        if any(token in blob for token in ("auth", "401", "invalid_api_key", "incorrect api key")):
            return OPENAI_AUTH_MESSAGE, "openai-auth"
        return fallback, "openai-error"


_MEDICAL_ADVICE_OUT = re.compile(
    r"\b(take|start|stop|dose|mg\b|prescribe|diagnos|"
    r"neem\b|dosering|voorschrijf|diagnose|metformin\w*|insulin\w*)\b",
    re.IGNORECASE,
)


def _looks_like_medical_advice(text: str) -> bool:
    return bool(_MEDICAL_ADVICE_OUT.search(text or ""))


def answer_question(
    question: str,
    payload: dict[str, Any],
    *,
    api_key: str | None = None,
    history: list[tuple[str, str]] | None = None,
) -> tuple[str, str]:
    text = (question or "").strip()
    if not text:
        return "Stel een vraag over een dagelijkse gewoonte — wandelen, eten, slapen, roken of alcohol.", "empty"
    if is_medical_or_triage(text):
        return DEFLECT_MESSAGE, "guardrail"
    fallback = template_reply(text, payload)
    reply, source = optional_llm_reply(
        text, payload, fallback, api_key=api_key, history=history
    )
    if source == "openai" and _looks_like_medical_advice(reply):
        return DEFLECT_MESSAGE, "guardrail-post"
    return reply, source

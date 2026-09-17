"""Mock buddy helpers: fixture loading, coaching copy, medical-question guardrails."""

from __future__ import annotations

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
    "sport": {"label": "Movement", "token": "sport"},
    "food": {"label": "Food", "token": "food"},
    "sleep": {"label": "Sleep", "token": "sleep"},
    "smoking": {"label": "Smoke-free", "token": "smoking"},
    "alcohol": {"label": "Alcohol", "token": "alcohol"},
}

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


def factor_share(factors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Normalize local importances so bars are comparable within this persona."""
    total = sum(float(f.get("importance") or 0) for f in factors) or 1.0
    out = []
    for factor in factors:
        item = dict(factor)
        item["share"] = float(factor.get("importance") or 0) / total
        out.append(item)
    return out


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
                "This is lifestyle coaching, not medical advice."
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

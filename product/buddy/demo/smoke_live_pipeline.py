"""Automated smoke: live Kylie A/B overlay vs mock what-if (River / Sam / Noor)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from buddy_lib import apply_weight_whatif, load_personas  # noqa: E402
from live_model import models_available, overlay_live_predictions  # noqa: E402


PERSONA_IDS = ("persona-river", "persona-sam", "persona-noor")
WEIGHT_BUMP_KG = 7.0


def _risks(payload: dict) -> dict[str, float]:
    return {r["id"]: float(r["risk_score"]) for r in payload.get("risks") or []}


def check_persona(base: dict, *, bump_kg: float = WEIGHT_BUMP_KG) -> dict:
    pid = base["patient"]["persona_id"]
    weight = float(base["patient"]["weight_kg"])
    problems: list[str] = []

    live = overlay_live_predictions(base, weight_kg=weight)
    mock = apply_weight_whatif(base, weight_kg=weight)
    live_up = overlay_live_predictions(base, weight_kg=weight + bump_kg)

    live_r = _risks(live)
    mock_r = _risks(mock)
    up_r = _risks(live_up)

    if live.get("source") != "live_kylie_models":
        problems.append(f"source={live.get('source')!r} (expected live_kylie_models)")

    for hid in ("t1_t2", "t1_t3"):
        if hid not in live_r:
            problems.append(f"missing risk id {hid}")
            continue
        score = live_r[hid]
        if not 0.0 <= score <= 1.0:
            problems.append(f"{hid}={score} outside [0,1]")

    factors = live.get("top_factors") or []
    if not factors:
        problems.append("top_factors empty")

    if live_r.get("t1_t2") == mock_r.get("t1_t2") and live_r.get("t1_t3") == mock_r.get("t1_t3"):
        problems.append("live scores identical to mock what-if at same weight")

    moved = any(abs(live_r.get(k, 0) - up_r.get(k, 0)) > 1e-6 for k in ("t1_t2", "t1_t3"))
    if not moved:
        problems.append(f"weight +{bump_kg} kg did not change either live risk")

    return {
        "persona_id": pid,
        "display_name": base["patient"].get("display_name"),
        "weight_kg": weight,
        "weight_up_kg": weight + bump_kg,
        "live": {
            "source": live.get("source"),
            "t1_t2": live_r.get("t1_t2"),
            "t1_t3": live_r.get("t1_t3"),
            "top_factors": [
                {"id": f.get("id"), "label": f.get("label"), "importance": f.get("importance")}
                for f in factors[:5]
            ],
        },
        "mock": {"source": mock.get("source"), "t1_t2": mock_r.get("t1_t2"), "t1_t3": mock_r.get("t1_t3")},
        "live_weight_up": {"t1_t2": up_r.get("t1_t2"), "t1_t3": up_r.get("t1_t3")},
        "ok": not problems,
        "problems": problems,
    }


def main() -> int:
    report: dict = {
        "models_available": models_available(),
        "personas": [],
        "ok": False,
    }
    if not models_available():
        report["problems"] = ["joblib A/B models not found under models/"]
        print(json.dumps(report, indent=2))
        return 1

    by_id = {p["patient"]["persona_id"]: p for p in load_personas()}
    missing = [pid for pid in PERSONA_IDS if pid not in by_id]
    if missing:
        report["problems"] = [f"missing personas: {missing}"]
        print(json.dumps(report, indent=2))
        return 1

    rows = [check_persona(by_id[pid]) for pid in PERSONA_IDS]
    report["personas"] = rows
    report["ok"] = all(r["ok"] for r in rows)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

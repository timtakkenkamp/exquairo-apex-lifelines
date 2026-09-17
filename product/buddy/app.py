"""Boris buddy — simple 3-step Streamlit demo (fork-only, no trained model)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from buddy_lib import (
    OPENAI_MODEL,
    THEME_META,
    answer_question,
    apply_weight_whatif,
    factor_direction_nl,
    factor_display_label,
    load_personas,
    openai_key_configured,
    pct,
    persona_body,
    pick_primary_intervention,
    resolve_openai_api_key,
    risk_band_nl,
    secondary_interventions,
    top_local_factors,
    validate_payload,
)
from intervention_pages import get_intervention_page
from live_model import models_available, overlay_live_predictions

PERSONA_ORDER = ["persona-river", "persona-sam", "persona-noor"]
ASSETS = Path(__file__).resolve().parent / "assets"
MASCOT_FILE = ASSETS / "boris-mascot.png"

THEME_COLORS = {
    "sport": {"bar": "#6FBF4B", "soft": "#E4F6D8", "ink": "#2F7A28"},
    "food": {"bar": "#3D8BBF", "soft": "#DCEAF6", "ink": "#1A4A6E"},
    "sleep": {"bar": "#7BA3C9", "soft": "#E6F0F8", "ink": "#2A5270"},
    "smoking": {"bar": "#5B7C99", "soft": "#E4EBF1", "ink": "#2C4256"},
    "alcohol": {"bar": "#4AA3C7", "soft": "#D9F0F7", "ink": "#1E5A70"},
}

RISK_COLORS = {
    "low": {"ink": "#2F8A4A", "badge_bg": "#DFF3D8", "badge_ink": "#1F6B34", "bar": "#6FBF4B"},
    "medium": {"ink": "#C9862A", "badge_bg": "#F8E6C6", "badge_ink": "#8A5A12", "bar": "#E0A84A"},
    "high": {"ink": "#C45B4A", "badge_bg": "#F8D9D4", "badge_ink": "#8A3328", "bar": "#D46B5A"},
}

st.set_page_config(
    page_title="Boris · kleine stappen",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(
    f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)


@st.cache_data
def personas() -> list[dict]:
    data = load_personas()
    problems = []
    for item in data:
        problems.extend(
            f"{item.get('patient', {}).get('persona_id')}: {e}" for e in validate_payload(item)
        )
    if problems:
        st.warning("Fixture checks:\n- " + "\n- ".join(problems))
    by_id = {p["patient"]["persona_id"]: p for p in data}
    return [by_id[pid] for pid in PERSONA_ORDER if pid in by_id]


def render_header() -> None:
    left, right = st.columns([1, 4])
    with left:
        if MASCOT_FILE.exists():
            st.image(str(MASCOT_FILE), width=110)
        else:
            st.markdown(
                """
<div style="width:92px;height:108px;border-radius:28px;background:#3D8BBF;position:relative;box-shadow:0 8px 18px rgba(61,139,191,0.25);">
  <div style="position:absolute;top:-10px;left:36px;width:10px;height:22px;background:#6FBF4B;border-radius:8px;"></div>
  <div style="position:absolute;top:6px;left:18px;width:22px;height:14px;background:#7ED957;border-radius:10px 2px;"></div>
  <div style="position:absolute;top:6px;right:18px;width:22px;height:14px;background:#7ED957;border-radius:2px 10px;"></div>
  <div style="position:absolute;top:32px;left:12px;right:12px;height:36px;background:#EAF4FB;border-radius:16px;"></div>
  <div style="position:absolute;top:42px;left:28px;width:10px;height:10px;background:#1A4A6E;border-radius:50%;"></div>
  <div style="position:absolute;top:42px;right:28px;width:10px;height:10px;background:#1A4A6E;border-radius:50%;"></div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.caption("Zet later `assets/boris-mascot.png` hier.")
    with right:
        st.markdown(
            """
<div style="padding-top:8px;">
  <div style="font-size:0.78rem;letter-spacing:0.08em;text-transform:uppercase;color:#3D8BBF;font-weight:700;">Met Boris</div>
  <div style="font-size:1.65rem;font-weight:750;color:#1A4A6E;line-height:1.2;">Small steps. Big impact.</div>
  <div style="color:#4A6A80;margin-top:4px;">Kleine stappen. Grote impact. Met Boris.</div>
</div>
""",
            unsafe_allow_html=True,
        )


def render_risk(risk: dict, short_title: str) -> None:
    label = risk["risk_label"]
    colors = RISK_COLORS[label]
    score_pct = pct(risk["risk_score"])
    width = max(4, round(float(risk["risk_score"]) * 100))
    st.markdown(
        f"""
<div style="background:#fff;border:1px solid #d5e6f2;border-radius:24px;padding:22px 20px 18px;box-shadow:0 10px 28px rgba(26,74,110,0.06);">
  <div style="font-weight:750;font-size:1.15rem;color:#1A4A6E;">{short_title}</div>
  <div style="color:#5A7A90;font-size:0.92rem;margin:2px 0 8px;">risico op diabetes</div>
  <div style="font-size:3.4rem;font-weight:800;letter-spacing:-0.04em;line-height:1;color:{colors["ink"]};">{score_pct}</div>
  <span style="display:inline-block;margin-top:10px;border-radius:999px;padding:3px 10px;font-size:0.75rem;font-weight:700;text-transform:uppercase;background:{colors["badge_bg"]};color:{colors["badge_ink"]};">{risk_band_nl(label)}</span>
  <div style="margin-top:14px;height:8px;background:#e4eef6;border-radius:999px;overflow:hidden;">
    <div style="width:{width}%;height:8px;background:{colors["bar"]};border-radius:999px;"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_factor(factor: dict) -> None:
    up = factor["direction"] == "increases_risk"
    verb = factor_direction_nl(factor["direction"])
    color = "#C45B4A" if up else "#2F8A4A"
    soft = "#E7A08C" if up else "#7ED957"
    width = max(8, round(float(factor["share"]) * 100))
    value = factor.get("patient_value") or "—"
    unit = factor.get("unit") or ""
    shown = f"{value} {unit}".strip()
    st.markdown(
        f"""
<div style="background:#fff;border:1px solid #d5e6f2;border-radius:18px;padding:12px 14px 14px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
    <div>
      <div style="font-weight:700;color:#1A4A6E;">{factor_display_label(factor)}</div>
      <div style="color:#5A7A90;font-size:0.88rem;">{shown}</div>
      <div style="margin-top:4px;font-size:0.9rem;font-weight:650;color:{color};">{verb}</div>
    </div>
    <div style="font-size:0.85rem;font-weight:700;color:{color};white-space:nowrap;">{round(factor["share"] * 100)}%</div>
  </div>
  <div style="margin-top:8px;height:10px;background:#e4eef6;border-radius:999px;overflow:hidden;">
    <div style="width:{width}%;height:10px;background:linear-gradient(90deg,{soft},{color});border-radius:999px;"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_detail_page(theme: str, patient_name: str) -> None:
    page = get_intervention_page(theme)
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    if st.button("← Terug naar Boris", key="back_home"):
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None
        st.rerun()
    render_header()
    st.caption(page["kicker"])
    st.title(page["title"])
    st.markdown(
        f"""
<div style="background:linear-gradient(180deg,{colors["soft"]},#fff 55%);border:1px solid #d5e6f2;border-left:8px solid {colors["bar"]};border-radius:20px;padding:16px 18px;margin:0 0 1rem 0;">
  <div style="font-size:0.78rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{colors["ink"]};margin-bottom:6px;">Boris voor {patient_name}</div>
  <div style="color:#1A3348;font-size:1.05rem;line-height:1.5;">{page["coach"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.subheader("Waarom dit helpt")
    st.write(page["why"])
    st.caption("Coaching, geen medicijn en geen triage.")
    st.subheader(page["route_name"])
    for i, step in enumerate(page.get("route_steps") or [], start=1):
        st.markdown(f"**{i}.** {step}")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown("**Wanneer**")
        st.write(page["when"])
    with c2:
        st.markdown("**Hoe lang**")
        st.write(page["duration"])
    with c3:
        st.markdown("**Hoe intens**")
        st.write(page["intensity"])
    if page.get("tip"):
        st.info(page["tip"])


def _sync_weight_to_bmi() -> None:
    height_m = float(st.session_state.get("whatif_height_cm") or 170) / 100.0
    st.session_state.whatif_bmi = round(float(st.session_state.whatif_weight) / (height_m**2), 1)


def _sync_bmi_to_weight() -> None:
    height_m = float(st.session_state.get("whatif_height_cm") or 170) / 100.0
    st.session_state.whatif_weight = round(float(st.session_state.whatif_bmi) * (height_m**2), 1)


def _secrets_openai_key() -> str:
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "") or "").strip()
    except Exception:
        return ""


payloads = personas()
by_id = {p["patient"]["persona_id"]: p for p in payloads}

with st.sidebar:
    st.markdown("### Boris")
    use_live_default = models_available()
    use_live = st.toggle(
        "Live model (Kylie A/B)",
        value=use_live_default,
        help="Aan: voorspellingen uit joblib A/B. Uit: mock fixtures.",
        disabled=not use_live_default,
    )
    st.caption("Small steps. Big impact.")
    st.markdown("**Wie ben jij?**")
    persona_id = st.radio(
        "Demo-persona",
        options=list(by_id),
        format_func=lambda pid: by_id[pid]["patient"]["display_name"],
        label_visibility="collapsed",
    )
    baseline = by_id[persona_id]
    body = persona_body(baseline)
    st.session_state.whatif_height_cm = body["height_cm"]
    persona_changed = st.session_state.get("whatif_persona") != persona_id
    resetting = st.session_state.pop("whatif_reset", False)
    if persona_changed or resetting:
        st.session_state.whatif_persona = persona_id
        st.session_state.whatif_weight = round(body["weight_kg"], 1)
        st.session_state.whatif_bmi = round(body["bmi"], 1)
    if persona_changed:
        st.session_state.chat = []
        st.session_state.chat_persona = persona_id
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None
    patient = baseline["patient"]
    st.caption(f"{patient['display_name']}, {patient.get('age', '—')} · start {body['weight_kg']:.0f} kg")
    stored_key = _secrets_openai_key()
    with st.expander("OpenAI-sleutel", expanded=not openai_key_configured(stored_key)):
        st.text_input(
            "OpenAI API key",
            type="password",
            key="openai_api_key",
            placeholder="sk-…",
            help="Zelfde patroon als eerdere opdracht: plak hier, of zet OPENAI_API_KEY in .streamlit/secrets.toml. Wordt niet gecommit.",
        )
        st.caption("Of: omgeving OPENAI_API_KEY, of kopieer secrets.toml.example naar secrets.toml.")

openai_key = resolve_openai_api_key(
    st.session_state.get("openai_api_key"),
    _secrets_openai_key(),
)

if use_live:
    payload = overlay_live_predictions(
        baseline, weight_kg=float(st.session_state.whatif_weight)
    )
else:
    payload = apply_weight_whatif(
        baseline, weight_kg=float(st.session_state.whatif_weight)
    )
patient = payload["patient"]

if st.session_state.get("buddy_view") == "detail":
    render_detail_page(st.session_state.get("detail_theme") or "sport", patient["display_name"])
    st.stop()

render_header()
st.title(f"Hoi {patient['display_name']}")
st.caption("Drie stappen: je risico → waarom jij → doe dit.")

# 1) Risico — slider first so the two big numbers stay live
st.subheader("1. Je risico")
wcol, bcol, rcol = st.columns([3, 2, 1])
with wcol:
    st.slider("Gewicht (kg)", 45.0, 140.0, step=0.5, key="whatif_weight", on_change=_sync_weight_to_bmi)
with bcol:
    st.number_input("BMI", min_value=16.0, max_value=50.0, step=0.1, key="whatif_bmi", on_change=_sync_bmi_to_weight)
with rcol:
    st.write("")
    if st.button("Reset"):
        st.session_state.whatif_reset = True
        st.rerun()

if use_live:
    payload = overlay_live_predictions(
        baseline, weight_kg=float(st.session_state.whatif_weight)
    )
else:
    payload = apply_weight_whatif(
        baseline, weight_kg=float(st.session_state.whatif_weight)
    )
patient = payload["patient"]
whatif = payload.get("whatif") or {}
if whatif.get("active"):
    st.caption(f"Nu {whatif['weight_kg']:.1f} kg · BMI {whatif['bmi']:.1f}.")

c1, c2 = st.columns(2)
risks = {r["id"]: r for r in payload["risks"]}
with c1:
    render_risk(risks["t1_t2"], "Korte termijn")
with c2:
    render_risk(risks["t1_t3"], "Lange termijn")
if use_live:
    st.caption("Live Kylie-modellen A/B (elastic-net). Proxy diabetes / HbA1c > 6,5%. Geen diagnose.")
else:
    st.caption("Mock-cijfers. Klein lettertje: kans dat HbA1c boven 6,5% uitkomt. Geen diagnose.")

# 2) Waarom jij — max 3
st.subheader("2. Waarom jij")
for factor in top_local_factors(payload, limit=3):
    render_factor(factor)

# 3) Doe dit — one primary CTA, max 3 cards
st.subheader("3. Doe dit")
primary = pick_primary_intervention(payload)
secondaries = secondary_interventions(payload, primary, limit=2)
if primary:
    theme = primary.get("theme") or "sport"
    meta = THEME_META.get(theme, {"label": "Stap"})
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    st.markdown(
        f"""
<div style="background:linear-gradient(135deg,{colors["soft"]},#fff 60%);border:1px solid #d5e6f2;border-radius:24px;padding:18px 18px 8px;margin-bottom:8px;">
  <div style="font-size:0.75rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{colors["ink"]};">Eerste stap · {meta["label"]}</div>
  <div style="font-size:1.35rem;font-weight:750;color:#1A4A6E;margin:6px 0;">{primary["title"]}</div>
  <div style="color:#3D5A70;">{primary["summary"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    cta = "Start de Groninger wandeling" if theme == "sport" else f"Open {meta['label'].lower()}"
    if st.button(cta, type="primary", use_container_width=True):
        st.session_state.buddy_view = "detail"
        st.session_state.detail_theme = theme
        st.rerun()

if secondaries:
    cols = st.columns(len(secondaries))
    for col, item in zip(cols, secondaries):
        theme = item.get("theme") or "sport"
        meta = THEME_META.get(theme, {"label": theme})
        with col:
            st.markdown(f"**{meta['label']}** — {item['title']}")
            if st.button("Open", key=f"open_{item.get('id', theme)}", use_container_width=True):
                st.session_state.buddy_view = "detail"
                st.session_state.detail_theme = theme
                st.rerun()

with st.expander("Vraag het Boris", expanded=bool(st.session_state.get("chat"))):
    if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
        st.session_state.chat = []
        st.session_state.chat_persona = persona_id
    if openai_key:
        st.caption(f"Verbonden met OpenAI · {OPENAI_MODEL}")
    else:
        st.caption("Geen API-sleutel. Plak er een in de sidebar — tot die tijd vaste teksten.")
    with st.form("ask_buddy", clear_on_submit=True):
        question = st.text_input("Je vraag", placeholder="Wandelen, eten, slapen…")
        asked = st.form_submit_button("Vraag")
    if asked:
        history = [(prev_q, prev_a) for prev_q, prev_a, _src in st.session_state.chat]
        reply, source = answer_question(
            question, payload, api_key=openai_key, history=history
        )
        st.session_state.chat.append((question, reply, source))
    for q, reply, source in st.session_state.chat:
        st.chat_message("user").write(q)
        with st.chat_message("assistant"):
            st.write(reply)
            if source == "openai":
                st.caption("OpenAI")
            elif source.startswith("guardrail"):
                st.caption("Guardrail — geen medisch advies")
            elif source == "openai-auth":
                st.caption("Sleutel geweigerd")
            else:
                st.caption("Vaste tekst")

st.caption(
    "Demo met Boris. Geen diagnose, geen triage, geen recept. "
    + (payload.get("disclaimer") or "")
)

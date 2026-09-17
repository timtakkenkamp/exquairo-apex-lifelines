"""Electronic buddy — mock Streamlit demo (fork-only, no trained model)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from buddy_lib import (
    PATIENT_RISK_COPY,
    THEME_META,
    answer_question,
    apply_weight_whatif,
    factor_direction_nl,
    factor_display_label,
    factor_share,
    load_personas,
    pct,
    persona_body,
    risk_band_nl,
    validate_payload,
)
from intervention_pages import get_intervention_page

PERSONA_ORDER = ["persona-river", "persona-sam", "persona-noor"]

THEME_COLORS = {
    "sport": {"bar": "#1b7f6b", "soft": "#d7efe8", "ink": "#146354"},
    "food": {"bar": "#e07a3d", "soft": "#fde6d4", "ink": "#b34d1f"},
    "sleep": {"bar": "#5459c4", "soft": "#e4e5f8", "ink": "#3d41a0"},
    "smoking": {"bar": "#6a5678", "soft": "#ece4f0", "ink": "#4e3f59"},
    "alcohol": {"bar": "#c48a2b", "soft": "#f8ebcc", "ink": "#8a5f12"},
}

RISK_COLORS = {
    "low": {"ink": "#2d8a6e", "badge_bg": "#d9f3ea", "badge_ink": "#1d6b54", "bar": "#2d8a6e"},
    "medium": {"ink": "#c9862a", "badge_bg": "#f8e6c6", "badge_ink": "#8a5a12", "bar": "#c9862a"},
    "high": {"ink": "#d45b4a", "badge_bg": "#f8d9d4", "badge_ink": "#9a3328", "bar": "#d45b4a"},
}

st.set_page_config(
    page_title="Buddy · diabetes risico (demo)",
    page_icon="🌿",
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


def render_risk(risk: dict) -> None:
    label = risk["risk_label"]
    colors = RISK_COLORS[label]
    score_pct = pct(risk["risk_score"])
    width = max(4, round(float(risk["risk_score"]) * 100))
    copy_bits = PATIENT_RISK_COPY.get(risk["id"], {})
    title = copy_bits.get("title") or risk.get("horizon")
    subtitle = copy_bits.get("subtitle") or risk.get("label")
    st.markdown(
        f"""
<div style="background:#fffdf8;border:1px solid #e4ddd0;border-radius:18px;padding:18px 18px 16px;box-shadow:0 8px 24px rgba(28,42,37,0.04);">
  <div style="font-weight:700;font-size:1.12rem;color:#1c2a25;line-height:1.25;">{title}</div>
  <div style="color:#5c6b64;font-size:0.86rem;margin:6px 0 8px 0;">{subtitle}</div>
  <div style="font-size:3rem;font-weight:750;letter-spacing:-0.03em;line-height:1;color:{colors["ink"]};">{score_pct}</div>
    <span style="display:inline-block;margin-top:8px;border-radius:999px;padding:3px 10px;font-size:0.75rem;font-weight:700;letter-spacing:0.04em;text-transform:uppercase;background:{colors["badge_bg"]};color:{colors["badge_ink"]};">{risk_band_nl(label)}</span>
  <div style="margin-top:12px;height:8px;background:#eee7da;border-radius:999px;overflow:hidden;">
    <div style="width:{width}%;height:8px;background:{colors["bar"]};border-radius:999px;"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_factor(factor: dict) -> None:
    up = factor["direction"] == "increases_risk"
    verb = factor_direction_nl(factor["direction"])
    color = "#d45b4a" if up else "#1b7f6b"
    soft = "#e7a08c" if up else "#7cc4b0"
    width = max(8, round(float(factor["share"]) * 100))
    value = factor.get("patient_value") or "—"
    unit = factor.get("unit") or ""
    shown = f"{value} {unit}".strip()
    st.markdown(
        f"""
<div style="background:#fffdf8;border:1px solid #e4ddd0;border-radius:14px;padding:12px 14px 14px;margin-bottom:8px;">
  <div style="display:flex;justify-content:space-between;gap:12px;align-items:flex-start;">
    <div>
      <div style="font-weight:650;color:#1c2a25;">{factor_display_label(factor)}</div>
      <div style="color:#5c6b64;font-size:0.88rem;">{shown}</div>
      <div style="margin-top:4px;font-size:0.86rem;font-weight:650;color:{color};">{verb}</div>
    </div>
    <div style="font-size:0.85rem;font-weight:700;color:{color};white-space:nowrap;">{round(factor["share"] * 100)}%</div>
  </div>
  <div style="margin-top:8px;height:10px;background:#efe8db;border-radius:999px;overflow:hidden;">
    <div style="width:{width}%;height:10px;background:linear-gradient(90deg,{soft},{color});border-radius:999px;"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_intervention(item: dict, factor_labels: dict[str, str]) -> None:
    theme = item.get("theme") or "sport"
    meta = THEME_META.get(theme, {"label": theme.title(), "token": theme})
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    links = ", ".join(factor_labels.get(fid, fid) for fid in item.get("linked_factors") or [])
    st.markdown(
        f"""
<div style="background:linear-gradient(180deg,{colors["soft"]},#fffdf8 42%);border:1px solid #e4ddd0;border-top:7px solid {colors["bar"]};border-radius:16px;padding:14px 14px 16px;min-height:200px;">
  <div style="font-size:0.75rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{colors["ink"]};margin-bottom:6px;">{meta["label"]}</div>
  <div style="font-size:1.08rem;font-weight:700;color:#1c2a25;margin:0 0 8px 0;">{item["title"]}</div>
  <div style="color:#3d4a44;font-size:0.92rem;line-height:1.45;margin-bottom:10px;">{item["summary"]}</div>
      <div style="font-size:0.78rem;color:#5c6b64;">Gekoppeld aan: {links or "jouw lokale factoren"}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_detail_page(theme: str, patient_name: str) -> None:
    page = get_intervention_page(theme)
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    if st.button("← Terug naar je leefstijlbeeld", key="back_home"):
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None
        st.rerun()
    st.caption(page["kicker"])
    st.title(page["title"])
    st.markdown(
        f"""
<div style="background:linear-gradient(180deg,{colors["soft"]},#fffdf8 50%);border:1px solid #e4ddd0;border-left:7px solid {colors["bar"]};border-radius:16px;padding:16px 18px;margin:0 0 1rem 0;">
  <div style="font-size:0.78rem;font-weight:750;letter-spacing:0.06em;text-transform:uppercase;color:{colors["ink"]};margin-bottom:6px;">Voorstel voor {patient_name}</div>
  <div style="color:#1c2a25;font-size:1.05rem;line-height:1.5;">{page["coach"]}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.subheader("Waarom dit past bij je risico-beeld")
    st.write(page["why"])
    st.caption("Leefstijlcoaching, geen medicijn en geen triage. Medische vragen horen bij je zorgverlener.")
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
    weight = float(st.session_state.whatif_weight)
    st.session_state.whatif_bmi = round(weight / (height_m**2), 1)


def _sync_bmi_to_weight() -> None:
    height_m = float(st.session_state.get("whatif_height_cm") or 170) / 100.0
    bmi = float(st.session_state.whatif_bmi)
    st.session_state.whatif_weight = round(bmi * (height_m**2), 1)


payloads = personas()
by_id = {p["patient"]["persona_id"]: p for p in payloads}

with st.sidebar:
    st.markdown("### Demo patient")
    st.caption("Switcher for the walkthrough. These are fictional personas, not real people.")
    persona_id = st.radio(
        "Who are we coaching?",
        options=list(by_id),
        format_func=lambda pid: (
            f"{by_id[pid]['patient']['display_name']} · "
            f"{risk_band_nl(by_id[pid]['risks'][1]['risk_label'])} lange termijn"
        ),
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
    st.markdown(f"**{patient['display_name']}**, {patient.get('age', '—')}")
    st.caption(patient.get("tagline", ""))
    st.write(patient.get("story", ""))
    st.caption(
        f"Demo length: {body['height_cm']:.0f} cm · start {body['weight_kg']:.1f} kg · "
        f"BMI {body['bmi']:.1f}"
    )
    st.divider()
    st.caption("Mock JSON → later a colleagues’ model API with the same contract.")
    st.caption(
        "Source: `"
        + baseline.get("source", "mock")
        + "` · schema "
        + baseline.get("schema_version", "?")
    )

payload = apply_weight_whatif(
    baseline,
    weight_kg=float(st.session_state.whatif_weight),
)
patient = payload["patient"]
whatif = payload.get("whatif") or {}

if st.session_state.get("buddy_view") == "detail":
    render_detail_page(st.session_state.get("detail_theme") or "sport", patient["display_name"])
    st.stop()

st.caption("ELEKTRONISCHE BUDDY · DEMO")
st.title(f"Hoi {patient['display_name']} — hier is jouw leefstijlbeeld")
st.write(
    "Twee beelden: **korte-termijn** en **lange-termijn risico op diabetes**, "
    "plus de factoren die *bij jou* horen (geen algemene ranglijst)."
)
st.info(
    "Coachingsmaatje voor een productdemo. Geen diagnose, geen triage, "
    "geen recept. Medische vragen horen bij je zorgverlener. "
    "Onderliggende demo-proxy blijft HbA1c boven 6,5%."
)

st.subheader("Wat als je gewicht verandert?")
st.caption(
    "Pas gewicht of BMI aan. De demo herberekent korte- en lange-termijn risico "
    "en de lokale bijdrage van gewicht/BMI (en taille als die meedoet). "
    "Eenvoudige rekenregel, geen model en geen medisch advies."
)
wcol, bcol, rcol = st.columns([3, 2, 1])
with wcol:
    st.slider(
        "Gewicht (kg)",
        min_value=45.0,
        max_value=140.0,
        step=0.5,
        key="whatif_weight",
        on_change=_sync_weight_to_bmi,
    )
with bcol:
    st.number_input(
        "BMI",
        min_value=16.0,
        max_value=50.0,
        step=0.1,
        key="whatif_bmi",
        on_change=_sync_bmi_to_weight,
    )
with rcol:
    st.write("")
    if st.button("Reset", help="Terug naar het startgewicht van deze persona"):
        st.session_state.whatif_reset = True
        st.rerun()

if whatif.get("active"):
    direction = "omhoog" if whatif["delta_kg"] > 0 else "omlaag"
    st.caption(
        f"Nu {whatif['weight_kg']:.1f} kg · BMI {whatif['bmi']:.1f} "
        f"({direction} {abs(whatif['delta_kg']):.1f} kg t.o.v. start). "
        f"Lengte in deze demo blijft {whatif['height_cm']:.0f} cm."
    )
else:
    st.caption(
        f"Startwaarden: {body['weight_kg']:.1f} kg · BMI {body['bmi']:.1f} · "
        f"lengte {body['height_cm']:.0f} cm (BMI = kg / m²)."
    )

# Re-apply after slider callbacks so the visible numbers match the widgets.
payload = apply_weight_whatif(baseline, weight_kg=float(st.session_state.whatif_weight))
whatif = payload.get("whatif") or {}
patient = payload["patient"]

st.subheader("Jouw twee risico's")
st.caption(
    "Korte- en lange-termijn risico op diabetes. "
    "De demo-proxy eronder blijft HbA1c boven 6,5%."
)
c1, c2 = st.columns(2)
risks = {r["id"]: r for r in payload["risks"]}
with c1:
    render_risk(risks["t1_t2"])
with c2:
    render_risk(risks["t1_t3"])

st.subheader("Wat beïnvloedt jouw risico")
st.caption(
    "Lokale bijdrage voor deze persoon — de staven bewegen als je gewicht aanpast. "
    "Geen team-brede ranglijst en geen getraind model."
)
for factor in factor_share(payload["top_factors"]):
    render_factor(factor)

st.subheader("Kleine stappen die bij je passen")
st.caption(
    "Alleen leefstijl. Kleuren: beweging = groen/blauw, voeding = oranje/koraal, "
    "slaap = indigo, rookvrij = paars, alcohol = amber."
)
st.caption("Tik een kaart voor een concreet voorstel — Beweging opent een Groninger wandellus.")
factor_labels = {f["id"]: factor_display_label(f) for f in payload["top_factors"]}
ix_cols = st.columns(len(payload["interventions"]))
for col, item in zip(ix_cols, payload["interventions"]):
    with col:
        render_intervention(item, factor_labels)
        theme = item.get("theme") or "sport"
        cta = "Open wandelvoorstel" if theme == "sport" else "Open dit voorstel"
        if st.button(cta, key=f"open_{item.get('id', theme)}", use_container_width=True):
            st.session_state.buddy_view = "detail"
            st.session_state.detail_theme = theme
            st.rerun()

st.subheader("A note from your buddy")
note = (payload.get("coaching") or {}).get("template", "")
if whatif.get("active"):
    if whatif["delta_kg"] < 0:
        extra = (
            f" Bij {whatif['weight_kg']:.0f} kg wordt het demobeeld iets rustiger — "
            "een leefstijlknop, geen recept."
        )
    else:
        extra = (
            f" Bij {whatif['weight_kg']:.0f} kg wordt het demobeeld iets strakker. "
            "Kleine, herhaalbare stappen in eten en bewegen tellen meer dan een perfect plan."
        )
    note = f"{note}{extra}"
st.markdown(
    f"""
<div style="background:#fffdf8;border:1px solid #e4ddd0;border-left:7px solid #2a8fb8;border-radius:16px;padding:16px 18px;color:#1c2a25;">
  {note}
</div>
""",
    unsafe_allow_html=True,
)

st.subheader("Ask your buddy")
st.caption(
    'Try a lifestyle question, then try a medical one (e.g. “should I take metformin?”) to see the guardrail.'
)
if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
    st.session_state.chat = []
    st.session_state.chat_persona = persona_id

with st.form("ask_buddy", clear_on_submit=True):
    question = st.text_input(
        "Your question",
        placeholder="Ask about walking, meals, sleep, smoking, or alcohol…",
    )
    asked = st.form_submit_button("Ask")
if asked:
    reply, source = answer_question(question, payload)
    st.session_state.chat.append((question, reply, source))

for q, reply, source in st.session_state.chat:
    st.markdown(f"**You:** {q}")
    bg = "#fff4ee" if source == "guardrail" else "#eef6f3"
    border = "#f0d2c4" if source == "guardrail" else "#cfe5dc"
    st.markdown(
        f"""
<div style="background:{bg};border:1px solid {border};border-radius:12px;padding:12px 14px;margin:0 0 12px 0;">
  {reply}<br><span style="color:#5c6b64;font-size:0.8rem;">Reply source: {source}</span>
</div>
""",
        unsafe_allow_html=True,
    )

st.caption(
    payload.get("disclaimer", "")
    + " Later the colleagues’ model fills the same JSON; this UI should not need a redesign."
)

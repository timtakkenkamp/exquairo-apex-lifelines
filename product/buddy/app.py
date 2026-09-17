"""Boris buddy — 3-step Streamlit demo (mock fixtures or final A/B models)."""

from __future__ import annotations

import base64
from pathlib import Path

import streamlit as st

from buddy_lib import (
    CHAT_PLACEHOLDER,
    OPENAI_MODEL,
    THEME_META,
    WAIST_CM_PER_KG,
    answer_question,
    apply_lifestyle_overlay,
    apply_weight_whatif,
    clip,
    factor_direction_nl,
    factor_display_label,
    load_default_system_prompt,
    load_personas,
    openai_key_configured,
    pct,
    persona_body,
    interventions_for_local_factors,
    linked_factor_labels,
    resolve_openai_api_key,
    risk_band_nl,
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


def audience_mode() -> bool:
    """Zaalweergave via ?demo=1 — hides workshop controls, keeps the 3-step UI."""
    tokens: list[str] = []
    try:
        raw = st.query_params.get("demo", "")
        if isinstance(raw, list):
            raw = raw[0] if raw else ""
        tokens.append(str(raw))
    except Exception:
        pass
    try:
        from urllib.parse import parse_qs, urlparse

        url = str(getattr(st.context, "url", "") or "")
        tokens.append((parse_qs(urlparse(url).query).get("demo") or [""])[0])
        if "demo=1" in url.lower() or "demo=true" in url.lower():
            tokens.append("1")
    except Exception:
        pass
    return any(str(token).strip().lower() in {"1", "true", "yes", "on"} for token in tokens)


AUDIENCE = audience_mode()
st.markdown(
    f"<style>{Path(__file__).with_name('styles.css').read_text(encoding='utf-8')}</style>",
    unsafe_allow_html=True,
)
if AUDIENCE:
    st.markdown(
        '<div class="buddy-audience-flag" aria-hidden="true"></div>',
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


def _mascot_data_uri() -> str:
    if not MASCOT_FILE.exists():
        return ""
    encoded = base64.b64encode(MASCOT_FILE.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{encoded}"


def render_header(*, audience: bool = False) -> None:
    uri = _mascot_data_uri()
    if uri:
        face = f'<img class="buddy-hero-face" src="{uri}" alt="Boris" />'
    else:
        face = '<div class="buddy-hero-face buddy-hero-fallback" aria-hidden="true"></div>'
    kicker = (
        '<div class="buddy-hero-kicker">Boris</div>'
        if audience
        else '<div class="buddy-hero-kicker">Met Boris</div>'
    )
    band = "buddy-hero buddy-hero--zaal" if audience else "buddy-hero"
    st.markdown(
        f"""
<div class="{band}">
  <div class="buddy-hero-mark">{face}</div>
  <div class="buddy-hero-copy">
    {kicker}
    <div class="buddy-hero-line">Kleine stappen. Grote impact.</div>
  </div>
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


def format_factor_value(factor: dict) -> str:
    """Patient-facing value: Ja/Nee for 0/1 flags, no raw 1.0."""
    raw = factor.get("patient_value")
    unit = str(factor.get("unit") or "").strip()
    if raw is None or raw == "" or raw == "—":
        return ""
    try:
        number = float(raw)
    except (TypeError, ValueError):
        return f"{raw} {unit}".strip()
    if not unit and (abs(number - 0.0) < 1e-9 or abs(number - 1.0) < 1e-9):
        return "Ja" if abs(number - 1.0) < 1e-9 else "Nee"
    if number == int(number):
        pretty = str(int(number))
    else:
        pretty = f"{number:.1f}".rstrip("0").rstrip(".")
    return f"{pretty} {unit}".strip()


def render_factor(factor: dict) -> None:
    up = factor["direction"] == "increases_risk"
    verb = factor_direction_nl(factor["direction"])
    color = "#C45B4A" if up else "#2F8A4A"
    soft = "#E7A08C" if up else "#7ED957"
    width = max(8, round(float(factor.get("share") or 0) * 100))
    shown = format_factor_value(factor)
    value_html = (
        f'<div style="color:#5A7A90;font-size:0.88rem;">{shown}</div>' if shown else ""
    )
    st.markdown(
        f"""
<div class="buddy-factor" style="background:#fff;border:1px solid #d5e6f2;border-radius:18px;padding:12px 14px 14px;margin-bottom:8px;">
  <div>
    <div style="font-weight:700;color:#1A4A6E;">{factor_display_label(factor)}</div>
    {value_html}
    <div style="margin-top:4px;font-size:0.9rem;font-weight:650;color:{color};">{verb}</div>
  </div>
  <div style="margin-top:8px;height:10px;background:#e4eef6;border-radius:999px;overflow:hidden;">
    <div style="width:{width}%;height:10px;background:linear-gradient(90deg,{soft},{color});border-radius:999px;"></div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_intervention_tile(item: dict, payload: dict) -> None:
    theme = item.get("theme") or "sport"
    meta = THEME_META.get(theme, {"label": "Stap"})
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    blurb = item.get("summary") or item.get("explanation") or ""
    st.markdown(
        f"""
<div class="buddy-tile" style="--buddy-tile-bar:{colors["bar"]};--buddy-tile-ink:{colors["ink"]};">
  <div class="buddy-tile-kicker">{meta["label"]}</div>
  <div class="buddy-tile-title">{item["title"]}</div>
  <div class="buddy-tile-blurb">{blurb}</div>
</div>
""",
        unsafe_allow_html=True,
    )
    cta = (
        "Open de Groninger wandeling"
        if item.get("id") == "activity-walks"
        else f"Meer over {meta['label'].lower()}"
    )
    if st.button(cta, key=f"open_{item.get('id', theme)}", use_container_width=True):
        st.session_state.buddy_view = "detail"
        st.session_state.detail_theme = theme
        st.rerun()


def render_detail_page(theme: str, patient_name: str, payload: dict) -> None:
    page = get_intervention_page(theme)
    colors = THEME_COLORS.get(theme, THEME_COLORS["sport"])
    item = next(
        (card for card in (payload.get("interventions") or []) if card.get("theme") == theme),
        None,
    )
    if st.button("← Terug naar Boris", key="back_home"):
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None
        st.rerun()
    render_header(audience=AUDIENCE)
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
    if item and item.get("how"):
        st.subheader("Hoe")
        st.write(item["how"])
    if item:
        links = linked_factor_labels(item, payload)
        if links:
            st.caption("Past bij jou: " + ", ".join(links))
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


def _nudge_waist_with_weight(old_weight: float, new_weight: float) -> None:
    """Keep taille visible and aligned with the 0.7 cm/kg mock track when gewicht moves."""
    if "whatif_waist" not in st.session_state:
        return
    delta = float(new_weight) - float(old_weight)
    if abs(delta) < 1e-9:
        return
    waist = float(st.session_state.whatif_waist)
    st.session_state.whatif_waist = round(clip(waist + WAIST_CM_PER_KG * delta, 60.0, 140.0), 0)


def _sync_weight_to_bmi() -> None:
    """Keep the BMI slider in lockstep when gewicht moves; taille follows 0.7 cm/kg."""
    height_m = float(st.session_state.get("whatif_height_cm") or 170) / 100.0
    new_weight = float(st.session_state.whatif_weight)
    old_weight = float(st.session_state.get("_whatif_weight_for_waist") or new_weight)
    st.session_state.whatif_bmi = round(new_weight / (height_m**2), 1)
    _nudge_waist_with_weight(old_weight, new_weight)
    st.session_state._whatif_weight_for_waist = new_weight


def _sync_bmi_to_weight() -> None:
    """BMI is a patient lever too — same slider chrome as taille / beweeg / slaap."""
    height_m = float(st.session_state.get("whatif_height_cm") or 170) / 100.0
    new_weight = round(float(st.session_state.whatif_bmi) * (height_m**2), 1)
    old_weight = float(st.session_state.get("_whatif_weight_for_waist") or new_weight)
    st.session_state.whatif_weight = new_weight
    _nudge_waist_with_weight(old_weight, new_weight)
    st.session_state._whatif_weight_for_waist = new_weight


def _secrets_openai_key() -> str:
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "") or "").strip()
    except Exception:
        return ""


def apply_persona_state(persona_id: str, baseline: dict) -> None:
    body = persona_body(baseline)
    st.session_state.whatif_height_cm = body["height_cm"]
    defaults = {
        "whatif_weight": round(body["weight_kg"], 1),
        "whatif_bmi": round(body["bmi"], 1),
        "whatif_waist": round(body["waist_cm"], 0),
        "whatif_move": int(round(body["move_min_week"])),
        "whatif_sleep": round(body["sleep_hours"], 1),
        "whatif_drinks": int(round(body["sugary_drinks_week"])),
        "_whatif_weight_for_waist": round(body["weight_kg"], 1),
    }
    persona_changed = st.session_state.get("whatif_persona") != persona_id
    resetting = st.session_state.pop("whatif_reset", False)
    if persona_changed or resetting:
        st.session_state.whatif_persona = persona_id
        for key, value in defaults.items():
            st.session_state[key] = value
    else:
        for key, value in defaults.items():
            st.session_state.setdefault(key, value)
    if persona_changed:
        st.session_state.chat = []
        st.session_state.chat_persona = persona_id
        st.session_state.buddy_view = "home"
        st.session_state.detail_theme = None


def payload_from_whatif(baseline: dict, use_live: bool) -> dict:
    weight_kg = float(st.session_state.whatif_weight)
    waist_cm = float(st.session_state.whatif_waist)
    move_min = float(st.session_state.whatif_move)
    sleep_h = float(st.session_state.whatif_sleep)
    drinks = float(st.session_state.whatif_drinks)
    if use_live:
        live = overlay_live_predictions(baseline, weight_kg=weight_kg, waist_cm=waist_cm)
        return apply_lifestyle_overlay(
            live,
            baseline,
            move_min_week=move_min,
            sleep_hours=sleep_h,
            sugary_drinks_week=drinks,
        )
    return apply_weight_whatif(
        baseline,
        weight_kg=weight_kg,
        waist_cm=waist_cm,
        move_min_week=move_min,
        sleep_hours=sleep_h,
        sugary_drinks_week=drinks,
    )


payloads = personas()
by_id = {p["patient"]["persona_id"]: p for p in payloads}
use_live_default = models_available()
if "system_prompt" not in st.session_state:
    st.session_state.system_prompt = load_default_system_prompt()
if st.session_state.pop("system_prompt_reset", False):
    st.session_state.system_prompt = load_default_system_prompt()

if AUDIENCE:
    use_live = use_live_default
    persona_id = st.session_state.get("audience_persona") or PERSONA_ORDER[0]
    if persona_id not in by_id:
        persona_id = PERSONA_ORDER[0]
else:
    with st.sidebar:
        st.markdown("### Boris")
        use_live = st.toggle(
            "Live model (final A/B)",
            value=use_live_default,
            help="Aan: final model A (elastic-net) en B (XGBoost). Uit: mock fixtures.",
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
        stored_key = _secrets_openai_key()
        st.caption(
            f"{by_id[persona_id]['patient']['display_name']}, "
            f"{by_id[persona_id]['patient'].get('age', '—')} · "
            f"start {persona_body(by_id[persona_id])['weight_kg']:.0f} kg"
        )
        with st.expander("OpenAI-sleutel", expanded=not openai_key_configured(stored_key)):
            st.text_input(
                "OpenAI API key",
                type="password",
                key="openai_api_key",
                placeholder="sk-…",
                help="Zelfde patroon als eerdere opdracht: plak hier, of zet OPENAI_API_KEY in .streamlit/secrets.toml. Wordt niet gecommit.",
            )
            st.caption("Of: omgeving OPENAI_API_KEY, of kopieer secrets.toml.example naar secrets.toml.")
        with st.expander("System prompt (demo)", expanded=False):
            st.caption(
                "Zoals bij Barbecue Bob: vaste rol-instructie voor OpenAI. "
                "Patiënten zien dit niet in de hoofdchat. Sessie-context van Pietje/Sam/Noor wordt eronder geplakt."
            )
            st.text_area("System prompt", key="system_prompt", height=280)
            if st.button("Herstel default"):
                st.session_state.system_prompt_reset = True
                st.rerun()
        if st.button("Zaalweergave"):
            st.query_params["demo"] = "1"
            st.rerun()
        st.caption("Of plak `?demo=1` achter de URL. Keuken (key, prompt, live-toggle) gaat dan weg.")

baseline = by_id[persona_id]
apply_persona_state(persona_id, baseline)

openai_key = resolve_openai_api_key(
    st.session_state.get("openai_api_key"),
    _secrets_openai_key(),
)

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]

if st.session_state.get("buddy_view") == "detail":
    render_detail_page(
        st.session_state.get("detail_theme") or "sport",
        patient["display_name"],
        payload,
    )
    st.stop()

render_header(audience=AUDIENCE)
st.title(f"Hoi {patient['display_name']}")
if AUDIENCE:
    st.markdown('<div class="buddy-pills-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
    picked = st.pills(
        "Wie ben jij?",
        options=list(by_id),
        format_func=lambda pid: by_id[pid]["patient"]["display_name"],
        key="audience_persona_pills",
        default=persona_id,
        label_visibility="collapsed",
    )
    if picked and picked != persona_id:
        st.session_state.audience_persona = picked
        st.rerun()

# 1) Risico — slider first so the two big numbers stay live
st.subheader("1. Je risico")
st.markdown('<div class="buddy-whatif-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
with st.container(border=True):
    st.caption("Wat als je gewicht of leefstijl verandert?")
    wcol, bcol, rcol = st.columns([2.8, 2.6, 1.1], vertical_alignment="bottom")
    with wcol:
        st.slider(
            "Gewicht (kg)",
            45.0,
            140.0,
            step=0.5,
            key="whatif_weight",
            on_change=_sync_weight_to_bmi,
        )
    with bcol:
        st.slider(
            "BMI",
            16.0,
            50.0,
            step=0.1,
            format="%.1f",
            key="whatif_bmi",
            on_change=_sync_bmi_to_weight,
            help="Volgt uit gewicht; zelf ook te schuiven. Lengte blijft vast.",
        )
    with rcol:
        if st.button("Reset", use_container_width=True):
            st.session_state.whatif_reset = True
            st.rerun()
    tcol, mcol, scol, dcol = st.columns(4, vertical_alignment="bottom")
    with tcol:
        st.slider(
            "Taille (cm)",
            60.0,
            140.0,
            step=1.0,
            key="whatif_waist",
            help="Middelomtrek — zelf meetbaar.",
        )
    with mcol:
        st.slider(
            "Beweegminuten per week",
            0,
            420,
            step=10,
            key="whatif_move",
            help="Wandelen, fietsen, sport.",
        )
    with scol:
        st.slider(
            "Slaap (uur per nacht)",
            4.0,
            10.0,
            step=0.5,
            key="whatif_sleep",
            help="Gemiddeld, niet perfect.",
        )
    with dcol:
        st.slider(
            "Suikerdranken per week",
            0,
            21,
            step=1,
            key="whatif_drinks",
            help="Frisdrank, sap, energiedrank.",
        )

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]
whatif = payload.get("whatif") or {}
if whatif.get("active"):
    st.caption(
        f"Nu {whatif['weight_kg']:.1f} kg · BMI {whatif['bmi']:.1f} · "
        f"taille {float(whatif.get('waist_cm') or 0):.0f} cm · "
        f"{float(whatif.get('move_min_week') or 0):.0f} min · "
        f"{float(whatif.get('sleep_hours') or 0):.1f} uur slaap · "
        f"{float(whatif.get('sugary_drinks_week') or 0):.0f} suikerdranken."
    )

c1, c2 = st.columns(2)
risks = {r["id"]: r for r in payload["risks"]}
with c1:
    render_risk(risks["t1_t2"], "Korte termijn")
with c2:
    render_risk(risks["t1_t3"], "Lange termijn")

# 2) Waarom jij — max 3
st.subheader("2. Waarom jij")
for factor in top_local_factors(payload, limit=3):
    render_factor(factor)

# 3) Doe dit — three tiles, ordered by this person's strongest factors
st.subheader("3. Doe dit")
st.markdown('<div class="buddy-tiles-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
cards = interventions_for_local_factors(payload, limit=3)
if cards:
    cols = st.columns(len(cards), gap="small")
    for col, item in zip(cols, cards):
        with col:
            render_intervention_tile(item, payload)

# 4) Chat — always visible
st.subheader("4. Vraag het Boris")
if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
    st.session_state.chat = []
    st.session_state.chat_persona = persona_id
if not AUDIENCE:
    if openai_key:
        st.caption(f"Verbonden met OpenAI · {OPENAI_MODEL}")
    else:
        st.caption("Geen API-sleutel. Plak er een in de sidebar — tot die tijd vaste teksten.")
with st.form("ask_buddy", clear_on_submit=True):
    question = st.text_input(
        "Je vraag",
        placeholder=CHAT_PLACEHOLDER,
        label_visibility="collapsed",
    )
    asked = st.form_submit_button("Vraag")
if asked:
    history = [(prev_q, prev_a) for prev_q, prev_a, _src in st.session_state.chat]
    reply, source = answer_question(
        question,
        payload,
        api_key=openai_key,
        history=history,
        system_prompt=st.session_state.get("system_prompt"),
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

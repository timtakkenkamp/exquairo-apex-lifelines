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
    factor_display_label,
    load_default_system_prompt,
    load_personas,
    openai_key_configured,
    pct,
    persona_body,
    factor_action_pairs,
    linked_factor_labels,
    resolve_openai_api_key,
    risk_band_nl,
    validate_payload,
)
from intervention_pages import get_intervention_page
from live_model import models_available, overlay_live_predictions
from model_adapter import body_roundness_index

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
    band = "buddy-hero buddy-hero--zaal" if audience else "buddy-hero"
    st.markdown(
        f"""
<div class="{band}">
  <div class="buddy-hero-mark">{face}</div>
  <div class="buddy-hero-copy">
    <div class="buddy-hero-name">Boris</div>
    <div class="buddy-hero-line">Je risico over 5 jaar</div>
  </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_risk(risk: dict) -> None:
    label = risk["risk_label"]
    colors = RISK_COLORS[label]
    score_pct = pct(risk["risk_score"])
    width = max(4, round(float(risk["risk_score"]) * 100))
    st.markdown(
        f"""
<div class="buddy-risk-hero">
  <div class="buddy-risk-title">Risico op diabetes <span>over 5 jaar</span></div>
  <div class="buddy-risk-num" style="color:{colors["ink"]};">{score_pct}</div>
  <span class="buddy-risk-band" style="background:{colors["badge_bg"]};color:{colors["badge_ink"]};">{risk_band_nl(label)}</span>
  <div class="buddy-risk-track">
    <div style="width:{width}%;background:{colors["bar"]};"></div>
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
    if abs(number - 0.0) < 1e-9 or abs(number - 1.0) < 1e-9:
        if not unit or unit.lower() in {"flag", "ja/nee", "0/1"}:
            return "Ja" if abs(number - 1.0) < 1e-9 else "Nee"
    if number == int(number):
        pretty = str(int(number))
    else:
        pretty = f"{number:.1f}".rstrip("0").rstrip(".")
    return f"{pretty} {unit}".strip()


def render_factor(factor: dict) -> None:
    shown = format_factor_value(factor)
    value_html = (
        f'<div style="color:#5A7A90;font-size:0.88rem;">{shown}</div>' if shown else ""
    )
    st.markdown(
        f"""
<div class="buddy-factor" style="background:#fff;border:1px solid #d5e6f2;border-radius:18px;padding:14px 16px;margin-bottom:8px;">
  <div style="font-weight:700;color:#1A4A6E;">{factor_display_label(factor)}</div>
  {value_html}
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
    if st.button(
        cta,
        key=f"open_{item.get('id', theme)}",
        type="primary",
        use_container_width=True,
    ):
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
    """Keep hidden taille aligned with the 0.7 cm/kg mock track when gewicht moves."""
    if "whatif_waist" not in st.session_state:
        return
    delta = float(new_weight) - float(old_weight)
    if abs(delta) < 1e-9:
        return
    waist = float(st.session_state.whatif_waist)
    st.session_state.whatif_waist = round(clip(waist + WAIST_CM_PER_KG * delta, 60.0, 140.0), 0)


def _current_height_cm() -> float:
    return float(st.session_state.get("whatif_height_cm") or 170)


def _sync_bri_from_waist() -> None:
    height_cm = _current_height_cm()
    waist = float(st.session_state.get("whatif_waist") or 80)
    st.session_state.whatif_bri = round(clip(body_roundness_index(waist, height_cm), 1.0, 12.0), 2)


def _sync_weight_to_shape() -> None:
    """Gewicht nudges taille (0.7 cm/kg); BRI follows taille + height."""
    new_weight = float(st.session_state.whatif_weight)
    old_weight = float(st.session_state.get("_whatif_weight_for_waist") or new_weight)
    _nudge_waist_with_weight(old_weight, new_weight)
    st.session_state._whatif_weight_for_waist = new_weight
    _sync_bri_from_waist()


def _bri_sentence() -> str:
    bri = float(st.session_state.get("whatif_bri") or 0)
    return (
        f"BRI {bri:.1f} — de vorm van je taille, uit middelomvang en lengte."
    )


def _secrets_openai_key() -> str:
    try:
        return str(st.secrets.get("OPENAI_API_KEY", "") or "").strip()
    except Exception:
        return ""


def _sync_audience_persona() -> None:
    """Keep zaal pills as the source of truth without a mid-script rerun.

    Pietje is the pills default (`persona-river`). A form submit can remount
    pills back to that default for one run; a `st.rerun()` then aborted before
    the chat form was processed — so only Pietje's Vraag-click survived.
    """
    picked = st.session_state.get("audience_persona_pills")
    if picked in PERSONA_ORDER:
        st.session_state.audience_persona = picked


def apply_persona_state(persona_id: str, baseline: dict) -> None:
    body = persona_body(baseline)
    st.session_state.whatif_height_cm = body["height_cm"]
    defaults = {
        "whatif_weight": round(body["weight_kg"], 1),
        "whatif_waist": round(body["waist_cm"], 0),
        "whatif_bri": round(body["bri"], 2),
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
    if st.session_state.get("audience_persona") not in by_id:
        st.session_state.audience_persona = PERSONA_ORDER[0]
    persona_id = st.session_state.audience_persona
    # Reassert before pills mount so a remount cannot snap back to Pietje.
    st.session_state.audience_persona_pills = persona_id
else:
    with st.sidebar:
        st.markdown("### Boris")
        use_live = st.toggle(
            "Live model (final A/B)",
            value=use_live_default,
            help="Aan: final model A (elastic-net, 5 jaar). Model B blijft in de repo, niet in beeld. Uit: mock fixtures.",
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

if AUDIENCE:
    bar_l, bar_r = st.columns([1.35, 1.75], vertical_alignment="center")
    with bar_l:
        render_header(audience=True)
    with bar_r:
        st.markdown('<div class="buddy-pills-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
        st.pills(
            "Wie ben jij?",
            options=list(by_id),
            format_func=lambda pid: by_id[pid]["patient"]["display_name"],
            key="audience_persona_pills",
            label_visibility="collapsed",
            on_change=_sync_audience_persona,
        )
else:
    render_header(audience=False)

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]
risks = {r["id"]: r for r in payload["risks"]}
render_risk(risks["t1_t2"])

st.markdown('<div class="buddy-whatif-flag" aria-hidden="true"></div>', unsafe_allow_html=True)
with st.container(border=True):
    st.slider(
        "Gewicht (kg)",
        45.0,
        140.0,
        step=0.5,
        key="whatif_weight",
        on_change=_sync_weight_to_shape,
    )
    st.markdown(f'<p class="buddy-bri-line">{_bri_sentence()}</p>', unsafe_allow_html=True)
    mcol, scol, dcol = st.columns(3, vertical_alignment="bottom")
    with mcol:
        st.slider("Beweegminuten per week", 0, 420, step=10, key="whatif_move")
    with scol:
        st.slider("Slaap (uur per nacht)", 4.0, 10.0, step=0.5, key="whatif_sleep")
    with dcol:
        st.slider("Suikerdranken per week", 0, 21, step=1, key="whatif_drinks")
    if st.button("Reset"):
        st.session_state.whatif_reset = True
        st.rerun()

payload = payload_from_whatif(baseline, use_live)
patient = payload["patient"]
st.markdown('<div class="buddy-voorjou-section buddy-tiles-flag">', unsafe_allow_html=True)
for factor, item in factor_action_pairs(payload, limit=3):
    render_factor(factor)
    render_intervention_tile(item, payload)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown('<div class="buddy-chat-section">', unsafe_allow_html=True)
if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
    st.session_state.chat = []
    st.session_state.chat_persona = persona_id
if not AUDIENCE:
    if openai_key:
        st.caption(f"Verbonden met OpenAI · {OPENAI_MODEL}")
    else:
        st.caption("Geen API-sleutel. Plak er een in de sidebar — tot die tijd vaste teksten.")
with st.form(f"ask_buddy_{persona_id}", clear_on_submit=True):
    question = st.text_input(
        "Je vraag",
        placeholder=CHAT_PLACEHOLDER,
        label_visibility="collapsed",
        key=f"buddy_ask_{persona_id}",
    )
    asked = st.form_submit_button("Vraag", type="primary")
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
for q, reply, _source in st.session_state.chat:
    st.chat_message("user").write(q)
    st.chat_message("assistant").write(reply)
st.markdown("</div>", unsafe_allow_html=True)

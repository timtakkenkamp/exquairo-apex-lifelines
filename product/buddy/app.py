"""Electronic buddy — mock Streamlit demo (fork-only, no trained model)."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from buddy_lib import (
    THEME_META,
    answer_question,
    factor_share,
    load_personas,
    pct,
    validate_payload,
)

st.set_page_config(
    page_title="Buddy · HbA1c lifestyle companion",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)


@st.cache_data
def personas() -> list[dict]:
    data = load_personas()
    problems = []
    for item in data:
        problems.extend(f"{item.get('patient', {}).get('persona_id')}: {e}" for e in validate_payload(item))
    if problems:
        st.warning("Fixture checks:\n- " + "\n- ".join(problems))
    return data


def risk_card(risk: dict) -> str:
    label = risk["risk_label"]
    score_pct = pct(risk["risk_score"])
    width = max(4, round(float(risk["risk_score"]) * 100))
    return f"""
    <div class="risk-card {label}">
      <div class="horizon">{risk["horizon"]}</div>
      <div class="when">{risk["label"]}</div>
      <div class="pct">{score_pct}</div>
      <span class="badge {label}">{label}</span>
      <div class="risk-sub">Chance HbA1c will be <strong>&gt; 6.5%</strong></div>
      <div class="meter {label}"><span style="width:{width}%"></span></div>
    </div>
    """


def factor_row(factor: dict) -> str:
    up = factor["direction"] == "increases_risk"
    direction = "up" if up else "down"
    verb = "Raises the picture" if up else "Lowers the picture"
    width = max(8, round(float(factor["share"]) * 100))
    value = factor.get("patient_value") or "—"
    unit = factor.get("unit") or ""
    shown = f"{value} {unit}".strip()
    return f"""
    <div class="factor-row">
      <div class="factor-top">
        <div>
          <div class="factor-name">{factor["label"]}</div>
          <div class="factor-val">{shown}</div>
        </div>
        <div class="factor-dir {direction}">{verb} · {round(factor["share"] * 100)}%</div>
      </div>
      <div class="factor-bar {direction}"><span style="width:{width}%"></span></div>
    </div>
    """


def intervention_card(item: dict, factor_labels: dict[str, str]) -> str:
    theme = item.get("theme") or "sport"
    meta = THEME_META.get(theme, {"label": theme.title(), "token": theme})
    links = ", ".join(factor_labels.get(fid, fid) for fid in item.get("linked_factors") or [])
    return f"""
    <article class="ix-card {meta["token"]}">
      <div class="ix-theme">{meta["label"]}</div>
      <h3>{item["title"]}</h3>
      <p>{item["summary"]}</p>
      <div class="ix-link">Linked to: {links or "your local factors"}</div>
    </article>
    """


payloads = personas()
by_id = {p["patient"]["persona_id"]: p for p in payloads}
labels = {
    pid: f"{p['patient']['display_name']} · {p['risks'][1]['risk_label']} T1→T3"
    for pid, p in by_id.items()
}

with st.sidebar:
    st.markdown("### Demo patient")
    st.caption("Switcher for the 15:00 walkthrough. These are fictional personas, not real people.")
    persona_id = st.radio(
        "Who are we coaching?",
        options=list(by_id),
        format_func=lambda pid: labels[pid],
    )
    payload = by_id[persona_id]
    patient = payload["patient"]
    st.markdown(f"**{patient['display_name']}**, {patient.get('age', '—')}")
    st.caption(patient.get("tagline", ""))
    st.write(patient.get("story", ""))
    snap = patient.get("snapshot") or {}
    if snap:
        st.markdown("**Snapshot (mock inputs)**")
        for key, value in snap.items():
            st.write(f"{key.replace('_', ' ')}: `{value}`")
    st.divider()
    st.caption("Mock JSON → later a colleagues’ model API with the same contract.")
    st.caption("Source: `" + payload.get("source", "mock") + "` · schema " + payload.get("schema_version", "?"))

st.markdown(
    f"""
    <div class="buddy-kicker">Electronic buddy · mock demo</div>
    <h1 class="buddy-title">Hi {patient["display_name"]} — here is your lifestyle picture</h1>
    <p class="buddy-lead">
      Two horizons for the chance HbA1c will be <strong>&gt; 6.5%</strong>,
      plus the factors that matter <em>for you</em> (not a global leaderboard).
    </p>
    <div class="disclaimer-banner">
      Coaching companion for a product demo. Not a diagnosis, not triage, not a prescription.
      Medical questions belong with a care provider.
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Your two risk pictures")
st.caption("T1 is the first visit. T2 and T3 are later visits. Percentages are mocked for this demo.")
c1, c2 = st.columns(2)
risks = {r["id"]: r for r in payload["risks"]}
with c1:
    st.markdown(risk_card(risks["t1_t2"]), unsafe_allow_html=True)
with c2:
    st.markdown(risk_card(risks["t1_t3"]), unsafe_allow_html=True)

st.subheader("What is shaping your picture")
st.caption("Local importance for this persona only. Bar length is this person’s mix, not a team-wide ranking.")
for factor in factor_share(payload["top_factors"]):
    st.markdown(factor_row(factor), unsafe_allow_html=True)

st.subheader("Small steps that fit you")
st.caption("Lifestyle only. Theme colours: movement = green/blue, food = orange/coral, sleep = indigo, smoke-free = plum, alcohol = amber.")
factor_labels = {f["id"]: f["label"] for f in payload["top_factors"]}
cards = "".join(intervention_card(ix, factor_labels) for ix in payload["interventions"])
st.markdown(f'<div class="ix-grid">{cards}</div>', unsafe_allow_html=True)

st.subheader("A note from your buddy")
note = (payload.get("coaching") or {}).get("template", "")
st.markdown(f'<div class="coach-card">{note}</div>', unsafe_allow_html=True)

st.subheader("Ask your buddy")
st.caption("Try a lifestyle question, then try a medical one (e.g. “should I take metformin?”) to see the guardrail.")
if "chat" not in st.session_state or st.session_state.get("chat_persona") != persona_id:
    st.session_state.chat = []
    st.session_state.chat_persona = persona_id

question = st.chat_input("Ask about walking, meals, sleep, smoking, or alcohol…")
if question:
    reply, source = answer_question(question, payload)
    st.session_state.chat.append((question, reply, source))

for q, reply, source in st.session_state.chat:
    with st.chat_message("user"):
        st.write(q)
    with st.chat_message("assistant"):
        klass = "guardrail" if source == "guardrail" else ""
        st.markdown(f'<div class="reply {klass}">{reply}</div>', unsafe_allow_html=True)
        st.caption(f"Reply source: {source}")

st.markdown(
    f'<p class="footer-note">{payload.get("disclaimer", "")} '
    "Later the colleagues’ model fills the same JSON; this UI should not need a redesign.</p>",
    unsafe_allow_html=True,
)

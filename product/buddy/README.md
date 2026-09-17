# Electronic buddy (mock demo)

Patient-facing **electronic buddy** for this Tim-owned fork. Near-term it is a product demo: two diabetes-risk pictures, local factors, lifestyle cards, and a weight what-if. A colleagues’ model can later fill the same JSON. Nothing here is a clinical claim.

## Locked demo decisions

| Decision | Value |
| --- | --- |
| Patient-facing titles | **Korte-termijn risico op diabetes** and **Lange-termijn risico op diabetes** |
| Mock proxy underneath | Chance HbA1c will be **> 6.5%** (shown as a small subtitle, not the card title) |
| Factors | Local (per persona), 3–5 items — mock stand-ins for later model features |
| What-if | Weight (kg) and BMI sliders update mock risks + BMI/waist bars |
| Cards | Lifestyle only, with theme colours |
| Tone | Coaching, motivating, not over-the-top |
| Guardrails | No medication, no triage, no hard medical advice |

## How to run (15:00 demo)

From the repo root, after cloning this fork:

```bash
uv sync
uv run streamlit run product/buddy/app.py
```

Without `uv`:

```bash
pip install -r product/buddy/requirements.txt
streamlit run product/buddy/app.py
```

Then open the URL Streamlit prints (usually http://localhost:8501). Use the sidebar to switch **River / Sam / Noor**.

Optional: if `OPENAI_API_KEY` is already in the environment, “Ask your buddy” may add a short LLM blurb. The app works offline with templated copy if the key is missing.

## What-if formula (transparent mock)

Not a trained model. BMI = `kg / m²` (height is fixed per persona).

```
short_term = clip(base_short + 0.025 * (BMI - BMI0), 0.02, 0.95)
long_term  = clip(base_long  + 0.035 * (BMI - BMI0), 0.03, 0.97)
bmi_bar    = clip(base_bmi_importance + 0.045 * (BMI - BMI0), 0.04, 0.70)
waist_cm   = waist0 + 0.7 * (kg - kg0)     # only if the persona has a waist factor
```

BMI direction flips at 25: below → **verlaagt je risico op diabetes**, at/above → **verhoogt je risico op diabetes**. Reset restores the persona’s start weight.

## What is mocked vs later model

| On screen | Today | Later |
| --- | --- | --- |
| Short- / long-term diabetes % | Persona JSON + weight what-if heuristic | Model probabilities (same two cards) |
| Top factors | Hardcoded local importances; BMI/waist move with the what-if | Patient-specific attributions from the team model |
| Intervention cards | Clickable; Movement opens a Groningen walk | Same cards, mapped from factor ids |
| Coaching note | Template (optional OpenAI) | Same contract field |
| Ask-your-buddy | Guardrails + templates | Same rules; still no prescribing |

The UI reads `product/buddy/fixtures/persona-*.json`. `contract.example.json` is the canonical River payload (schema `0.2.0`).

## Files

| File | Role |
| --- | --- |
| `app.py` | Streamlit UI (home + session-state detail views) |
| `intervention_pages.py` | Movement (Groningen walk) + Food/Sleep stubs |
| `buddy_lib.py` | Loader, validation, coaching, guardrails |
| `styles.css` | Theme tokens (sport / food / sleep / smoking / alcohol) |
| `fixtures/` | River, Sam, Noor mocks |
| `contract.example.json` | Example payload (River) |
| `personas.md` | Persona stories |
| `test_buddy.py` | Fixture + guardrail checks |

```bash
uv run python product/buddy/test_buddy.py
```

## Guardrails

The buddy will **not** prescribe, diagnose, or triage. Medical / medication / emergency questions are deflected to a care provider. Lifestyle coaching (move, eat, sleep, smoke-free days, alcohol-free evenings) is in scope.

## Out of scope

- Training or evaluating models
- Changing team preprocessing
- Pushing to `kyliekeijzer/exquairo-apex-lifelines`

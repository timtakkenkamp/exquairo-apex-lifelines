# Electronic buddy (mock demo)

Patient-facing **electronic buddy** for this Tim-owned fork. Near-term it is a product demo: two HbA1c-risk pictures, local factors, and lifestyle cards. A colleagues’ model can later fill the same JSON. Nothing here is a clinical claim.

## Locked demo decisions

| Decision | Value |
| --- | --- |
| Outcome | Chance HbA1c will be **> 6.5%** (not ≥, not another cutoff, not metabolic disorder) |
| Horizons | **T1→T2** and **T1→T3** (percent + low / medium / high) |
| Factors | Local (per persona), 3–5 items — mock stand-ins for later model features |
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

## What is mocked vs later model

| On screen | Today | Later |
| --- | --- | --- |
| T1→T2 / T1→T3 percents | Hardcoded in persona JSON | Model probabilities for HbA1c > 6.5% |
| Top factors | Hardcoded local importances | Patient-specific attributions from the team model |
| Intervention cards | Curated lifestyle library | Same cards, mapped from factor ids |
| Coaching note | Template (optional OpenAI) | Same contract field |
| Ask-your-buddy | Guardrails + templates | Same rules; still no prescribing |

The UI reads `product/buddy/fixtures/persona-*.json`. `contract.example.json` is the canonical River payload (schema `0.2.0`).

## Files

| File | Role |
| --- | --- |
| `app.py` | Streamlit UI |
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

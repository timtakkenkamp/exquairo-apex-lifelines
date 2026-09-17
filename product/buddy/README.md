# Boris buddy (simplified mock)

Patient-facing demo on **Tim’s fork only**. Three steps: **je risico → waarom jij → doe dit**. Style follows the Boris board (soft blues, sprout green, rounded cards, *Small steps. Big impact. With Boris.*).

Nothing here is a clinical claim.

## How to run

```bash
uv sync
uv run streamlit run product/buddy/app.py
```

Without `uv`:

```bash
pip install -r product/buddy/requirements.txt
streamlit run product/buddy/app.py
```

Open the URL Streamlit prints (usually http://localhost:8501). Sidebar: **River / Sam / Noor**.

## What was simplified

| Before | Now |
| --- | --- |
| Long home, English leftovers, always-on ask box | 3-step Dutch home, ask-box in **Vraag het Boris** expander |
| 5 local factors | Max **3** (*verhoogt/verlaagt je risico op diabetes*) |
| Three equal cards | **One primary CTA** (River → Groningen walk) + max 2 extra |
| Cream/coral chrome | Boris sky-blue + sprout green |

Official mascot: drop `product/buddy/assets/boris-mascot.png`. Until then the app uses a placeholder robot + sprout. See `assets/README.md`.

## Kept

- Two big numbers: korte- / lange-termijn risico op diabetes (HbA1c > 6.5% only as small disclaimer)
- Weight/BMI what-if (live risks + bars)
- Movement detail: Groningen Plantsoen–gracht–Martini-lus + back
- Personas River / Sam / Noor
- Guardrails: no meds, no triage
- Chat via OpenAI when a key is present (sidebar, `.streamlit/secrets.toml`, or `OPENAI_API_KEY`); otherwise Dutch templates

## OpenAI chat (zelfde patroon als eerdere opdracht)

De vragenbox **Vraag het Boris** gebruikt `gpt-4o-mini` zodra er een sleutel is. De sleutel wordt niet gecommit.

1. Plak de key in de sidebar onder **OpenAI-sleutel**, of
2. Kopieer `.streamlit/secrets.toml.example` naar `.streamlit/secrets.toml` en vul `OPENAI_API_KEY` in, of
3. Zet `OPENAI_API_KEY` in je omgeving.

Zonder sleutel blijft de demo werken met vaste Nederlandse teksten. Medische vragen worden nog steeds geweigerd voordat OpenAI wordt aangeroepen.

## What-if formula

```
short_term = clip(base_short + 0.025 * (BMI - BMI0), 0.02, 0.95)
long_term  = clip(base_long  + 0.035 * (BMI - BMI0), 0.03, 0.97)
```

Not a trained model. BMI direction flips at 25.

```bash
uv run python product/buddy/test_buddy.py
```

Do not push this playground to `kyliekeijzer/exquairo-apex-lifelines`.

## Live models (stap 3)

Sidebar toggle **Live model (Kylie A/B)** uses `models/model_{a,b}_best_logreg_elasticnet.joblib` via `live_model.py` + `model_adapter.py`. Persona feature snapshots live in `fixtures/persona-*-features.json`. Toggle off = mock fixtures.

## Stap 4 — coaching API + guardrails

- Strengere NL/EN medical + jailbreak guardrails (pre + post LLM).
- Thin FastAPI bridge: `uv run uvicorn product.buddy.api:app --app-dir product/buddy --port 8080`
  - `GET /health`, `GET /personas`, `POST /predict`, `POST /ask`
- Demo video: `product/buddy/demo/boris-buddy-demo.mp4`

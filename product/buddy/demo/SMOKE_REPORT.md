# Boris Buddy live-model smoke

**Result: PASS**

Date: 2026-09-17  
Branch: `cursor/buddy-live-smoke-49ff` off `cursor/sandbox-coordinator-buddy-33af`  
Env: `uv sync` (CPython 3.12.3). Streamlit credentials: `~/.streamlit/credentials.toml` (`email = ""`).

## Pipeline (automated) — PASS

`uv run python product/buddy/demo/smoke_live_pipeline.py`

Joblibs present: `models/model_{a,b}_best_logreg_elasticnet.joblib`.  
`overlay_live_predictions` source is `live_kylie_models`. Risk ids `t1_t2` / `t1_t3`, scores in [0, 1], top factors non-empty. Live ≠ mock at the same weight. Weight +7 kg moves at least one live score.

| Persona | kg | Live t1_t2 / t1_t3 | Mock t1_t2 / t1_t3 | Live @ +7 kg |
| --- | ---: | --- | --- | --- |
| River | 94.5 | **0.9227 / 0.9090** | 0.4803 / 0.6704 | 0.9248 / 0.9294 |
| Sam | 82.7 | 0.3336 / 0.4437 | 0.2700 / 0.3801 | 0.3402 / 0.5102 |
| Noor | 66.0 | 0.0258 / 0.0982 | 0.0796 / 0.1295 | 0.0266 / 0.1269 |

River matches the prior local smoke (~0.92 / 0.91 vs mock 0.48 / 0.67). Long-term risk moves more at 101.5 kg (0.909 → 0.929).

## FastAPI — PASS

Started with `cd product/buddy && uv run uvicorn api:app --host 127.0.0.1 --port 8080`.  
(README’s `product.buddy.api:app --app-dir product/buddy` fails: `product` is not a package.)

| Endpoint | Result |
| --- | --- |
| `GET /health` | `ok: true`, `live_models: true` |
| `GET /personas` | River, Sam, Noor |
| `POST /predict` live River 94.5 | source `live_kylie_models`, 0.9227 / 0.9090 |
| `POST /predict` mock River 94.5 | source `mock`, 0.4803 / 0.6704 |
| `POST /predict` live River 101.5 | 0.9248 / 0.9294 |
| `POST /ask` metformin | `source: guardrail` (deflect) |
| `POST /ask` “wandelen Groningen” | `source: template` (coaching, not deflect) |

## UI + video — PASS

Streamlit: `uv run streamlit run product/buddy/app.py --server.headless true --server.port 8501`.  
Video: [`boris-buddy-smoke.mp4`](boris-buddy-smoke.mp4) (~22s, Playwright drive of the live UI). Replay helper: `record_ui_smoke.py`.

Walkthrough (persona **River**, **Live model (Kylie A/B)** ON):

| Step | Observed |
| --- | --- |
| Home | Caption “Live Kylie-modellen A/B”. Risks **92% / 91%**. Slider 94.50 kg. |
| Weight what-if | BMI 33.5 → slider **101.40 kg**. Risks **92% / 93%**. Caption “Nu 101.4 kg · BMI 33.5.” |
| Groningen walk | Live top factor is HbA1c, so primary CTA is **Open voeding**. Walk is secondary **Beweging → Open**. Detail page: Noorderplantsoen → grachten → Martinitoren. |
| Back | Slider display jumped to **45.00** / BMI **16.00** (known quirk). |
| Reset | Restored baseline so chat stays readable. |
| “Should I take metformin?” | Guardrail: *Ik ben een leefstijl-buddy, geen zorgverlener…* |
| “wandelen Groningen” | Coaching template: *Start with walks you can keep…* |

## Known quirk — weight slider after detail

Confirmed. `st.slider(..., key="whatif_weight")` is not mounted on the intervention page (`st.stop()`). Streamlit drops unmounted widget keys, so coming back remounts the slider at min **45 kg** (BMI widget at min 16). Not a one-liner without a persist key; left as-is.

## Out of scope / not failures

- README uvicorn import path (works as `cd product/buddy && uvicorn api:app`).
- HIP_T1 mapped to factor id `waist` (two “waist” rows can appear).
- Playwright cannot reliably drag the React Aria range thumb; the recording uses the linked BMI field, which updates the weight slider and live scores.
- No retraining, no UI redesign.

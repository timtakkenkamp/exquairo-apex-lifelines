# Boris Buddy live-model smoke

**Result: PASS** (pipeline + API). UI walkthrough video follows in this PR.

Date: 2026-09-17  
Branch: `cursor/buddy-live-smoke-49ff` off `cursor/sandbox-coordinator-buddy-33af`  
Command: `uv sync` then `uv run python product/buddy/demo/smoke_live_pipeline.py`

## Pipeline (automated) — PASS

Joblibs present: `models/model_a_best_logreg_elasticnet.joblib`, `models/model_b_best_logreg_elasticnet.joblib`.  
`overlay_live_predictions` source is `live_kylie_models`. Risk ids `t1_t2` / `t1_t3`, scores in [0, 1], top factors non-empty. Live ≠ mock at the same weight. Weight +7 kg moves at least one live score.

| Persona | kg | Live t1_t2 / t1_t3 | Mock t1_t2 / t1_t3 | Live @ +7 kg |
| --- | ---: | --- | --- | --- |
| River | 94.5 | **0.9227 / 0.9090** | 0.4803 / 0.6704 | 0.9248 / 0.9294 |
| Sam | 82.7 | 0.3336 / 0.4437 | 0.2700 / 0.3801 | 0.3402 / 0.5102 |
| Noor | 66.0 | 0.0258 / 0.0982 | 0.0796 / 0.1295 | 0.0266 / 0.1269 |

River matches the prior local smoke (~0.92 / 0.91 vs mock 0.48 / 0.67). Long-term risk moves more when weight goes to 101.5 kg (0.909 → 0.929).

## FastAPI — PASS

Started with `cd product/buddy && uv run uvicorn api:app --host 127.0.0.1 --port 8080`  
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

## UI + video

- Streamlit: `uv run streamlit run product/buddy/app.py` on `:8501` (credentials.toml so no email prompt).
- Video: `product/buddy/demo/boris-buddy-smoke.mp4` (recorded after this report’s pipeline section).

Notes for the walkthrough:

- Live toggle defaults **ON** when joblibs exist (and is disabled if they do not).
- Under live models River’s strongest local factor is **HbA1c**, so the primary CTA is the food card, not “Start de Groninger wandeling”. The Groningen walk is still available as a secondary **Open** (Beweging).
- Weight +7 kg on River: short risk barely moves (0.9227 → 0.9248); long risk 0.9090 → 0.9294. UI should show ~92% / 91% then ~92% / 93%.

## Known quirk — weight slider after detail

`st.slider(..., key="whatif_weight")` is not rendered on the intervention detail page (`st.stop()`). Streamlit drops unmounted widget keys, so coming back can remount the slider at the min **45 kg**. Not a one-liner without a persist key; left as-is. Confirm in the UI recording.

## Out of scope / not failures

- README uvicorn import path (works if you `cd product/buddy` and run `api:app`).
- HIP_T1 is mapped to factor id `waist` (so two “waist” rows can appear). Cheap mapping, not changed.
- No retraining, no UI redesign.

# Demo personas

Fictional patients for the mock buddy. Values are **placeholders** inspired by columns in the synth Lifelines-style table (`HBAC_*`, `BMI_*`, `SPORTS_T1`, `SMOKING`, family T2DM flags, sleep, alcohol). They are not real people and not model outputs.

Use `persona_id` as the fixture key when a UI or API mock is added.

## persona-river — higher mock risk

- **Display name:** River (demo)
- **Story:** Mid-50s, higher BMI, little reported sport, mother with type 2 diabetes.
- **Illustrative inputs:** age ~54, BMI 31.2, `HBAC` 6.2%, no sports, family T2DM (mother), former irregular sleep.
- **Buddy should show:** moderate-to-higher `risk_score`, factors around BMI / inactivity / family history, cards for walking + meal pattern + care-team check-in.
- **Example payload:** `contract.example.json` (`persona_id`: `persona-river`).

## persona-sam — mixed / mid mock risk

- **Display name:** Sam (demo)
- **Story:** Early 40s, BMI in the mid-20s, cycles to work some days, smokes occasionally, alcohol above the group’s “none” pattern.
- **Illustrative inputs:** age ~42, BMI 26.1, `HBAC` 5.8%, `CYCLE_COMMUTE_T1` yes, `SMOKING` yes, moderate `SUMOFALCOHOL`.
- **Buddy should show:** mid `risk_score`, local factors for smoking and alcohol (activity may *decrease* risk), cards for smoking reduction and alcohol-free days.

## persona-noor — lower mock risk

- **Display name:** Noor (demo)
- **Story:** Late 30s, active, BMI in a lower range, no family T2DM flags, HbA1c well below the mock threshold.
- **Illustrative inputs:** age ~38, BMI 23.4, `HBAC` 5.3%, sports yes, smoking no, sleep quality flagged as OK.
- **Buddy should show:** low `risk_score`, fewer “increases_risk” factors (maybe protective activity/BMI), maintenance cards rather than urgent change.

## Notes for later wiring

- Keep persona files/JSON next to this doc so the Streamlit mock can switch patients without a model.
- When a model exists, map real local attributions onto the same `top_factors[].id` values used here (`bmi`, `sports`, `family_t2dm`, `smoking`, `alcohol`, `sleep`, …).
- Do not present these stories as validated risk profiles.

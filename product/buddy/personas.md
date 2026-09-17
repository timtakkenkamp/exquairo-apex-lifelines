# Demo personas

Fictional patients for the mock buddy. Values are **placeholders** inspired by columns in the synth Lifelines-style table (`HBAC_*`, `BMI_*`, `SPORTS_T1`, `SMOKING`, family T2DM flags, sleep, alcohol). They are not real people and not model outputs.

Use `persona_id` as the fixture key. JSON lives in `fixtures/`.

Patient-facing outcomes for every persona:

- **Korte-termijn risico op diabetes** (mock proxy: HbA1c > 6.5%)
- **Lange-termijn risico op diabetes** (same proxy, longer horizon)

## persona-river — higher mock risk

- **Display name:** River (they/them), 54 · 174 cm · start 94.5 kg · BMI 31.2
- **Story:** Higher weight, little reported sport, mother with type 2 diabetes, patchy sleep.
- **Mock risks:** short-term 48% medium · long-term 67% high
- **Local factors:** BMI, inactivity, waist, family T2DM, sleep (all risk-raising in this mock)
- **Cards:** walking (sport / green-blue), steadier plates (food / coral), calmer wind-down (sleep / indigo)
- **What-if:** weight/BMI sliders move both risk cards plus the BMI and waist bars
- **Payloads:** `fixtures/persona-river.json` and `contract.example.json`

## persona-sam — mixed / mid mock risk

- **Display name:** Sam (he/him), 42 · 178 cm · start 82.7 kg · BMI 26.1
- **Story:** BMI mid-20s, cycles to work some days, smokes occasionally, drinks more than “none”.
- **Mock risks:** short-term 27% medium · long-term 38% medium
- **Local factors:** smoking and alcohol raise; cycling and commute activity lower; BMI is a milder raise than River
- **Cards:** smoke-free days (plum), alcohol-free evenings (amber), protect the bike habit (sport)

## persona-noor — lower mock risk

- **Display name:** Noor (she/her), 38 · 168 cm · start 66.0 kg · BMI 23.4
- **Story:** Active, BMI in a lower range, no family T2DM flags, HbA1c well below the mock threshold.
- **Mock risks:** short-term 8% low · long-term 13% low
- **Local factors:** sports, BMI, sleep, and non-smoking are protective; a small busy-day kcal nudge raises
- **Cards:** keep training, steady busy-day meals, guard sleep — maintenance, not overhaul

## Notes for later wiring

- When a model exists, map real local attributions onto the same `top_factors[].id` values (`bmi`, `sports`, `family_t2dm`, `smoking`, `alcohol`, `sleep`, `waist`, `kcal`, `cycle_commute`, …).
- Do not present these stories as validated risk profiles.

# Demo personas

Fictional patients for the mock buddy. Values are **placeholders** inspired by columns in the synth Lifelines-style table (`HBAC_*`, `BMI_*`, `SPORTS_T1`, `SMOKING`, family T2DM flags, sleep, alcohol). They are not real people and not model outputs.

Use `persona_id` as the fixture key. JSON lives in `fixtures/`. Outcome for every persona: chance HbA1c will be **> 6.5%** on **T1→T2** and **T1→T3**.

## persona-river — higher mock risk

- **Display name:** River (they/them), 54
- **Story:** Higher weight, little reported sport, mother with type 2 diabetes, patchy sleep.
- **Mock risks:** T1→T2 48% medium · T1→T3 67% high
- **Local factors:** BMI, inactivity, waist, family T2DM, sleep (all risk-raising in this mock)
- **Cards:** walking (sport / green-blue), steadier plates (food / coral), calmer wind-down (sleep / indigo)
- **Payloads:** `fixtures/persona-river.json` and `contract.example.json`

## persona-sam — mixed / mid mock risk

- **Display name:** Sam (he/him), 42
- **Story:** BMI mid-20s, cycles to work some days, smokes occasionally, drinks more than “none”.
- **Mock risks:** T1→T2 27% medium · T1→T3 38% medium
- **Local factors:** smoking and alcohol raise; cycling and commute activity lower; BMI is a milder raise than River
- **Cards:** smoke-free days (plum), alcohol-free evenings (amber), protect the bike habit (sport)

## persona-noor — lower mock risk

- **Display name:** Noor (she/her), 38
- **Story:** Active, BMI in a lower range, no family T2DM flags, HbA1c well below the mock threshold.
- **Mock risks:** T1→T2 8% low · T1→T3 13% low
- **Local factors:** sports, BMI, sleep, and non-smoking are protective; a small busy-day kcal nudge raises
- **Cards:** keep training, steady busy-day meals, guard sleep — maintenance, not overhaul

## Notes for later wiring

- When a model exists, map real local attributions onto the same `top_factors[].id` values (`bmi`, `sports`, `family_t2dm`, `smoking`, `alcohol`, `sleep`, `waist`, `kcal`, `cycle_commute`, …).
- Do not present these stories as validated risk profiles.

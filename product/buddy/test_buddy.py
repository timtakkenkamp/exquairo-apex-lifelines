"""Stdlib checks for mock fixtures and guardrails."""

from __future__ import annotations

import unittest

from buddy_lib import (
    DEFLECT_MESSAGE,
    EXAMPLE_CONTRACT,
    PATIENT_RISK_COPY,
    answer_question,
    apply_weight_whatif,
    factor_direction_nl,
    is_medical_or_triage,
    load_payload,
    load_personas,
    validate_payload,
)


class FixtureTests(unittest.TestCase):
    def test_three_personas_and_valid_contract(self):
        personas = load_personas()
        self.assertEqual(len(personas), 3)
        ids = {p["patient"]["persona_id"] for p in personas}
        self.assertEqual(ids, {"persona-river", "persona-sam", "persona-noor"})
        for payload in personas:
            self.assertEqual(validate_payload(payload), [])
        example = load_payload(EXAMPLE_CONTRACT)
        self.assertEqual(validate_payload(example), [])
        self.assertEqual(example["patient"]["persona_id"], "persona-river")

    def test_local_factors_differ_across_personas(self):
        by_id = {p["patient"]["persona_id"]: p for p in load_personas()}
        river_top = by_id["persona-river"]["top_factors"][0]["id"]
        sam_top = by_id["persona-sam"]["top_factors"][0]["id"]
        noor_top = by_id["persona-noor"]["top_factors"][0]["id"]
        self.assertNotEqual(river_top, sam_top)
        self.assertNotEqual(sam_top, noor_top)
        self.assertEqual(by_id["persona-river"]["risks"][1]["risk_label"], "high")
        self.assertEqual(by_id["persona-noor"]["risks"][0]["risk_label"], "low")


class WhatIfTests(unittest.TestCase):
    def test_heavier_weight_raises_risks_and_bmi_bar(self):
        river = next(p for p in load_personas() if p["patient"]["persona_id"] == "persona-river")
        heavier = apply_weight_whatif(river, weight_kg=104.5)
        lighter = apply_weight_whatif(river, weight_kg=84.5)
        base_short = river["risks"][0]["risk_score"]
        base_long = river["risks"][1]["risk_score"]
        self.assertGreater(heavier["risks"][0]["risk_score"], base_short)
        self.assertGreater(heavier["risks"][1]["risk_score"], base_long)
        self.assertLess(lighter["risks"][0]["risk_score"], base_short)
        self.assertLess(lighter["risks"][1]["risk_score"], base_long)
        # Long-term coefficient is larger, so the long card moves more.
        self.assertGreater(
            heavier["risks"][1]["risk_score"] - base_long,
            heavier["risks"][0]["risk_score"] - base_short,
        )
        base_bmi = next(f for f in river["top_factors"] if f["id"] == "bmi")
        heavy_bmi = next(f for f in heavier["top_factors"] if f["id"] == "bmi")
        light_bmi = next(f for f in lighter["top_factors"] if f["id"] == "bmi")
        self.assertGreater(heavy_bmi["importance"], base_bmi["importance"])
        self.assertLess(light_bmi["importance"], base_bmi["importance"])
        base_waist = next(f for f in river["top_factors"] if f["id"] == "waist")
        heavy_waist = next(f for f in heavier["top_factors"] if f["id"] == "waist")
        self.assertGreater(float(heavy_waist["patient_value"]), float(base_waist["patient_value"]))
        self.assertEqual(heavier["risks"][0]["horizon"], PATIENT_RISK_COPY["t1_t2"]["title"])
        self.assertEqual(heavier["risks"][1]["horizon"], PATIENT_RISK_COPY["t1_t3"]["title"])

    def test_reset_weight_matches_baseline(self):
        river = next(p for p in load_personas() if p["patient"]["persona_id"] == "persona-river")
        same = apply_weight_whatif(river, weight_kg=94.5)
        self.assertAlmostEqual(same["risks"][0]["risk_score"], 0.48, places=3)
        self.assertAlmostEqual(same["risks"][1]["risk_score"], 0.67, places=3)
        self.assertFalse(same["whatif"]["active"])


class CopyTests(unittest.TestCase):
    def test_factor_direction_is_dutch(self):
        self.assertEqual(
            factor_direction_nl("increases_risk"),
            "verhoogt je risico op diabetes",
        )
        self.assertEqual(
            factor_direction_nl("decreases_risk"),
            "verlaagt je risico op diabetes",
        )
        app = (EXAMPLE_CONTRACT.parent / "app.py").read_text(encoding="utf-8").lower()
        self.assertNotIn("raises the picture", app)
        self.assertNotIn("lowers the picture", app)


class GuardrailTests(unittest.TestCase):
    def test_medical_deflects(self):
        self.assertTrue(is_medical_or_triage("Should I take metformin?"))
        self.assertTrue(is_medical_or_triage("Can you diagnose me?"))
        self.assertFalse(is_medical_or_triage("How do I start walking after dinner?"))
        river = next(p for p in load_personas() if p["patient"]["persona_id"] == "persona-river")
        text, source = answer_question("What pills should I take?", river)
        self.assertEqual(source, "guardrail")
        self.assertEqual(text, DEFLECT_MESSAGE)
        text, source = answer_question("How can I walk more?", river)
        self.assertEqual(source, "template")
        self.assertIn("wandel", text.lower())


if __name__ == "__main__":
    unittest.main()

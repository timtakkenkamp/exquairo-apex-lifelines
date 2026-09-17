"""Stdlib checks for mock fixtures and guardrails."""

from __future__ import annotations

import unittest

from buddy_lib import (
    DEFLECT_MESSAGE,
    EXAMPLE_CONTRACT,
    answer_question,
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
        self.assertIn("walk", text.lower())


if __name__ == "__main__":
    unittest.main()

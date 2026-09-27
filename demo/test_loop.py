"""Tests for the bounded critique-revise loop."""

import unittest

from demo.critique_revise import (
    CHECKLIST,
    DemoProvider,
    parse_critique_payload,
    run_loop,
)


def valid_payload() -> dict[str, object]:
    return {
        "criteria": [
            {"name": "Rõ ràng", "passed": True, "comment": "Dễ đọc."},
            {"name": "Đủ ý", "passed": True, "comment": "Đủ bốn ý."},
            {"name": "Đúng độ dài", "passed": True, "comment": "Có 110 từ."},
        ],
        "summary": "Đạt checklist.",
    }


class LoopTests(unittest.TestCase):
    def test_stops_after_one_revision_when_checklist_passes(self) -> None:
        result = run_loop(DemoProvider("early-stop"), "test")
        self.assertEqual(result.revision_count, 1)
        self.assertEqual(len(result.critiques), 2)
        self.assertTrue(result.critiques[-1].passed)

    def test_never_exceeds_two_revisions(self) -> None:
        result = run_loop(DemoProvider("two-rounds"), "test")
        self.assertEqual(result.revision_count, 2)
        self.assertLessEqual(result.revision_count, 2)

    def test_keeps_initial_and_final_versions(self) -> None:
        result = run_loop(DemoProvider(), "test")
        self.assertNotEqual(result.initial_version, result.final_version)
        self.assertGreater(len(result.initial_version), 0)
        self.assertGreater(len(result.final_version), 0)

    def test_checklist_is_fixed(self) -> None:
        self.assertEqual(len(CHECKLIST), 3)
        self.assertIn("Rõ ràng", CHECKLIST[0])
        self.assertIn("Đủ ý", CHECKLIST[1])
        self.assertIn("Đúng độ dài", CHECKLIST[2])

    def test_rejects_empty_criteria(self) -> None:
        payload = valid_payload()
        payload["criteria"] = []
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)

    def test_rejects_missing_criterion(self) -> None:
        payload = valid_payload()
        payload["criteria"] = payload["criteria"][:2]  # type: ignore[index]
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)

    def test_rejects_duplicate_criterion(self) -> None:
        payload = valid_payload()
        criteria = payload["criteria"]  # type: ignore[assignment]
        criteria[2] = dict(criteria[0])  # type: ignore[index]
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)

    def test_rejects_unknown_criterion_name(self) -> None:
        payload = valid_payload()
        payload["criteria"][0]["name"] = "Sáng tạo"  # type: ignore[index]
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)

    def test_rejects_non_boolean_passed(self) -> None:
        payload = valid_payload()
        payload["criteria"][0]["passed"] = "false"  # type: ignore[index]
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)

    def test_rejects_empty_comment(self) -> None:
        payload = valid_payload()
        payload["criteria"][0]["comment"] = "   "  # type: ignore[index]
        with self.assertRaises(ValueError):
            parse_critique_payload(payload)


if __name__ == "__main__":
    unittest.main(verbosity=2)
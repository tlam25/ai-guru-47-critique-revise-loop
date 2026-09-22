"""Tests for the bounded critique-revise loop."""

import unittest

from demo.critique_revise import CHECKLIST, DemoProvider, run_loop


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
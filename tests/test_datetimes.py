"""Date/time components must not be permutable as independent numbers."""
import unittest
from test_check_rewrite import checker, prose_scan


class DateTimeChecks(unittest.TestCase):
    def test_component_swaps_cannot_pass(self):
        for before, after in (
            ("2026-01-02", "2026-02-01"), ("2026/01/02", "2026/02/01"),
            ("2026年1月2日", "2026年2月1日"), ("12:05", "05:12"),
            ("2026-01-02T03:04:05+06:00", "2026-02-01T03:04:05+06:00"),
        ):
            with self.subTest(before=before):
                self.assertEqual(checker.compare("Deadline: " + before, "Deadline: " + after)["status"], "failed")

    def test_datetime_is_one_literal_and_preserves_timezone(self):
        for value in ("2026-10-30T10:15:20Z", "2026-10-30 10:15:20.123+08:00", "9:15"):
            with self.subTest(value=value):
                self.assertEqual(prose_scan.numbers(prose_scan.snapshot(value)), [value])

    def test_ordinary_rephrasing_and_reordering_are_allowed(self):
        self.assertEqual(checker.compare("Start 2026-01-02, end 2026-02-01.",
                                        "End: 2026-02-01. Start: 2026-01-02.")["status"], "passed")
        self.assertEqual(checker.compare("At 12:05, retry twice.", "Retry twice at 12:05.")["status"], "passed")

    def test_dates_do_not_absorb_protected_content_or_list_markers(self):
        source = "- 2026-01-02\n- 2026-02-01"
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot(source)), ["2026-01-02", "2026-02-01"])
        self.assertEqual(checker.compare("2026 `date` 01", "2026 `date` 02")["status"], "failed")


if __name__ == "__main__":
    unittest.main()

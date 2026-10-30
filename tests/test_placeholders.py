"""Protect interpolation contracts without treating percentage prose as code."""
import unittest
import subprocess
import sys
from test_check_rewrite import checker, prose_scan, SCRIPTS


class PlaceholderChecks(unittest.TestCase):
    def test_long_invalid_printf_fields_have_bounded_runtime(self):
        script = "from prose_scan import snapshot; snapshot('%'+'0'*100000+'z'); snapshot('%1'*40000)"
        process = subprocess.run([sys.executable, "-B", "-c", script], cwd=SCRIPTS,
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_printf_argument_type_width_and_precision_are_protected(self):
        for before, after in (("%1$s", "%1$d"), ("%08.2f", "%8.2f"),
                              ("%.2f", "%.3f"), ("%(amount)+.2f", "%(total)+.2f"),
                              ("%2$*1$d", "%1$*2$d"), ("%*.*f", "%*.*g"),
                              ("%#x", "%x"), ("%%", "%")):
            with self.subTest(before=before):
                result = checker.compare("Value: " + before, "Value: " + after)
                self.assertEqual(result["status"], "failed")
                self.assertIn("placeholders", {v["category"] for v in result["violations"]})

    def test_printf_fields_allow_surrounding_wording_and_escape_pairs(self):
        for field in ("%1$s", "%08.2f", "%(amount)+.2f", "%2$*1$d", "%*.*f", "%%s", "%%%s"):
            self.assertEqual(checker.compare("Please use " + field, "Use " + field)["status"], "passed")
        self.assertEqual(prose_scan.snapshot("%%s").items()["placeholders"], ["%%"])
        self.assertEqual(prose_scan.snapshot("%%%s").items()["placeholders"], ["%%", "%s"])

    def test_percentage_prose_and_protected_code_do_not_become_printf_fields(self):
        for text in ("20% of revenue", "5% growth", "95% stable", "20% of the sample"):
            self.assertNotIn("placeholders", prose_scan.snapshot(text).items())
        result = checker.compare("`%1$s`", "`%1$d`")
        self.assertEqual({v["category"] for v in result["violations"]}, {"inline_code"})


if __name__ == "__main__":
    unittest.main()

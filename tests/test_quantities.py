"""Quantity preservation regressions, including ordinary wording and scope controls."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "core/yaya/scripts"
sys.path.insert(0, str(SCRIPTS))
import check_rewrite as checker
import prose_scan


class QuantityChecks(unittest.TestCase):
    def assert_change(self, before, after):
        result = checker.compare(before, after)
        self.assertEqual(result["status"], "failed", result)
        self.assertIn("numbers", {item["category"] for item in result["violations"]})

    def test_currency_and_scale_changes_are_not_plain_wording(self):
        pairs = [
            ("Revenue: USD 5 million.", "Revenue: EUR 5 million."),
            ("Revenue: USD 5 million.", "Revenue: USD 5 billion."),
            ("Revenue: USD5 million.", "Revenue: EUR5 million."),
            ("Budget: 5 million USD.", "Budget: 5 million EUR."),
            ("Budget: $5 billion.", "Budget: $5 million."),
            ("Cash: CNY 300.", "Cash: JPY 300."),
            ("Cash: SGD 300.", "Cash: HKD 300."),
            ("现金为人民币500万元。", "现金为美元500万元。"),
            ("收入 500 万美元。", "收入 500 万欧元。"),
            ("预算 2 万亿元。", "预算 2 亿元。"),
            ("Loss: -USD 50.", "Loss: USD 50."),
            ("Balance: USD -50.", "Balance: USD +50."),
            ("Budget: 5 thousand.", "Budget: 5 million."),
            ("Budget: 5 trillion.", "Budget: 5 billion."),
        ]
        for before, after in pairs:
            with self.subTest(before=before, after=after):
                self.assert_change(before, after)

    def test_scientific_coefficient_exponent_sign_and_precision(self):
        pairs = [
            ("Tolerance: 1e-3.", "Tolerance: 1e+3."),
            ("Tolerance: 1e3.", "Tolerance: 9e3."),
            ("Tolerance: 1e3.", "Tolerance: 1e4."),
            ("Tolerance: -1e-3.", "Tolerance: 1e-3."),
            ("Tolerance: 1.20E-3.", "Tolerance: 1.20E-4."),
            ("Tolerance: .5e-3.", "Tolerance: .5e+3."),
            ("Current: −0.5.", "Current: +0.5."),
            ("Current: -.5.", "Current: +.5."),
            ("Timeout: 1e3 ms.", "Timeout: 1e3 s."),
            ("阈值为1e-3，保持不变。", "阈值为1e+3，保持不变。"),
        ]
        for before, after in pairs:
            with self.subTest(before=before, after=after):
                self.assert_change(before, after)

    def test_financial_rate_units_and_technical_capacity(self):
        pairs = [
            ("增长 3 个百分点。", "增长 3 个基点。"),
            ("增长 3 个百分点。", "增长 3%。"),
            ("Up 3 percentage points.", "Up 3 basis points."),
            ("Up 3 percentage points.", "Up 3 percent."),
            ("Up 3 bp.", "Up 3%."),
            ("Limit: 8 MiB.", "Limit: 8 GiB."),
            ("Limit: 8 MB.", "Limit: 8 Mb."),
            ("Rate: 8 Mbps.", "Rate: 8 Gbps."),
            ("Rate: 8 MiB/s.", "Rate: 8 MiB."),
            ("Delay: 8 μs.", "Delay: 8 ms."),
        ]
        for before, after in pairs:
            with self.subTest(before=before, after=after):
                self.assert_change(before, after)

    def test_ordinary_wording_and_sentence_order_are_editable(self):
        pairs = [
            ("We are currently reviewing the USD 5 million forecast.", "We are reviewing the USD 5 million forecast."),
            ("It is worth noting that the limit is 8 MiB.", "The limit is 8 MiB."),
            ("我们现在开始进行人民币500万元预算的审核。", "我们开始审核人民币500万元预算。"),
            ("需要注意的是，阈值为1e-3。", "阈值为1e-3。"),
            ("Growth: 3 percentage points, unaudited.", "Unaudited growth: 3 percentage points."),
            ("A: USD 5 million. B: EUR 6 million.", "B: EUR 6 million. A: USD 5 million."),
            ("There are 5 people and 3 meetings.", "There are 3 meetings and 5 people."),
            ("阅读材料 5 次，然后分析。", "先读材料 5 次，再分析。"),
            ("Read 5 manuals.", "Use 5 manuals."),
            ("Review 5 millionaires.", "Interview 5 millionaires."),
        ]
        for before, after in pairs:
            with self.subTest(before=before):
                self.assertEqual(checker.compare(before, after)["status"], "passed")

    def test_recognized_quantity_spelling_is_conservative(self):
        # Numerically equivalent conversions or reformatting require review too.
        for before, after in [("USD 5 million", "$5 million"), ("1e3 ms", "1 s"),
                              ("1.00", "1"), ("8 MiB", "8MiB"), ("3 bp", "3 basis points")]:
            with self.subTest(before=before, after=after):
                self.assert_change(before, after)

    def test_accounting_parentheses_are_part_of_currency_values(self):
        for amount in ("(USD 5 million)", "($1,250.00)", "(5 million USD)", "（500 万元）", "( EUR 50 )"):
            with self.subTest(amount=amount):
                self.assertEqual(prose_scan.numbers(prose_scan.snapshot(amount)), [amount])
                self.assert_change("Balance: " + amount, "Balance: " + amount[1:-1].strip())

    def test_parenthetical_prose_is_editable_and_negative_values_can_move(self):
        self.assertEqual(checker.compare("Balance (estimated): USD 5 million.",
                                        "Estimated balance: USD 5 million.")["status"], "passed")
        self.assertEqual(checker.compare("A: (USD 5 million); B: EUR 6 million.",
                                        "B: EUR 6 million; A: (USD 5 million).")["status"], "passed")
        self.assert_change("Balance: (USD 5).", "Balance: -USD 5.")

    def test_accounting_parentheses_do_not_cross_protected_spans(self):
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("(USD 5 `estimated`)")), ["USD 5"])

    def test_list_bullets_do_not_become_negative_quantities(self):
        before = "- USD 5 million\n- 8 MiB\n"
        after = "USD 5 million; 8 MiB."
        self.assertEqual(checker.compare(before, after)["status"], "passed")
        self.assertEqual(checker.compare("+ 1e-3\n", "1e-3.")["status"], "passed")
        self.assert_change("- USD -5 million\n", "USD 5 million.")
        self.assert_change("- -8 MiB\n", "8 MiB.")

    def test_protected_spans_keep_their_own_category(self):
        cases = [("`USD 5 million`", "inline_code"),
                 ("> USD 5 million\n", "blockquotes"),
                 ("```text\nUSD 5 million\n```\n", "fences"),
                 ("| Amount |\n| --- |\n| USD 5 million |\n", "tables")]
        for before, category in cases:
            with self.subTest(category=category):
                result = checker.compare(before, before.replace("USD", "EUR"))
                self.assertEqual({c["category"] for c in result["violations"]}, {category})
        # Masked content is a boundary, not whitespace joining a currency to a value.
        text = "USD `price` 5 million."
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot(text)), ["5 million"])
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("USD\n5 million")), ["5 million"])

    def test_removal_duplication_and_exact_grant(self):
        before, after = "USD 5 million and USD 5 million.", "USD 5 million."
        self.assert_change(before, after)
        self.assert_change(after, before)
        before, after = "Budget: USD 5 million.", "Budget: EUR 5 billion."
        difference = {k: checker.compare(before, after)["changes"][0][k]
                      for k in ("category", "before", "after")}
        grant = {"schema": 1, "before_sha256": hashlib.sha256(before.encode()).hexdigest(),
                 "after_sha256": hashlib.sha256(after.encode()).hexdigest(), "changes": [difference]}
        self.assertEqual(checker.compare(before, after, allow=grant)["status"], "passed")
        with self.assertRaises(prose_scan.InputError):
            checker.compare(before, "Budget: EUR 6 billion.", allow=grant)

    def test_semantic_and_unlisted_unit_limits_remain_visible(self):
        for before, after in [("A: USD 5 million; B: EUR 6 million.", "A: EUR 6 million; B: USD 5 million."),
                              ("Do not retry after 2 failures.", "Retry after 2 failures."),
                              ("Value: 5 widgets.", "Value: 5 gadgets.")]:
            with self.subTest(before=before):
                result = checker.compare(before, after)
                self.assertEqual(result["status"], "passed")
                self.assertTrue(any("associations" in line for line in result["limitations"]))

    def test_long_invalid_number_like_text_has_bounded_runtime(self):
        script = ("import prose_scan; "
                  "samples=['9'*100000+'x', '９'*100000+'x', '1e+'*30000]; "
                  "[prose_scan.numbers(prose_scan.snapshot(s)) for s in samples]")
        result = subprocess.run([sys.executable, "-B", "-c", script], cwd=SCRIPTS,
                                capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

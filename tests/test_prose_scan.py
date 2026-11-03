"""Protected spans and quantities found by prose_scan, checked through check_rewrite."""

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


class ReferenceChecks(unittest.TestCase):
    def test_email_and_uri_autolinks_preserve_targets_and_allow_prose_edits(self):
        for target in ("<team@example.com>", "<team+reports@example.com>", "<mailto:team@example.com>",
                       "<https://example.com/report>", "<ftp://example.com/report>", "<urn:example:report>"):
            with self.subTest(target=target):
                source = "Please read " + target + "."
                self.assertEqual(checker.compare(source, "Read " + target + ".")["status"], "passed")
                result = checker.compare(source, source.replace("example", "changed"))
                self.assertEqual(result["status"], "failed")
                self.assertIn("urls", {v["category"] for v in result["violations"]})

    def test_malformed_autolinks_remain_unsupported_and_code_stays_shielded(self):
        for source in ("<mailto:team name@example.com>", "<https://example.com", "<a@@example.com>"):
            self.assertEqual(checker.compare(source, source)["status"], "unsupported")
        source = "`<team@example.com>`"
        result = checker.compare(source, source.replace("team", "other"))
        self.assertEqual({v["category"] for v in result["violations"]}, {"inline_code"})
        self.assertEqual(checker.compare("<span>Old</span>", "<span>New</span>")["status"], "passed")

    def test_long_escaped_link_label_has_bounded_runtime(self):
        script = "from check_rewrite import compare; s='[ '+chr(92)*100000+' ](target)'; assert compare(s,s)['status']=='passed'"
        process = subprocess.run([sys.executable, "-B", "-c", script], cwd=SCRIPTS,
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)

    def test_image_link_role_changes_fail_for_each_supported_link_form(self):
        for source in ("![diagram](flow.svg)", "![diagram][id]\n\n[id]: flow.svg\n",
                       "![id][]\n\n[id]: flow.svg\n", "![id]\n\n[id]: flow.svg\n",
                       "![a [nested] label](flow.svg)", "![array `a[0]`](flow.svg)"):
            with self.subTest(source=source):
                result = checker.compare(source, source[1:])
                self.assertEqual(result["status"], "failed")
                self.assertIn("link_roles", {v["category"] for v in result["violations"]})
                self.assertEqual(checker.compare(source[1:], source)["status"], "failed")

    def test_image_alt_text_and_escaped_image_punctuation_are_editable(self):
        for source in ("![old](flow.svg)", "![old][id]\n\n[id]: flow.svg\n", r"\![old](flow.svg)"):
            self.assertEqual(checker.compare(source, source.replace("old", "new"))["status"], "passed")
        self.assertEqual(checker.compare(r"\![old](flow.svg)", "[old](flow.svg)")["status"], "passed")
        self.assertEqual(checker.compare(r"\\![old](flow.svg)", r"\\[old](flow.svg)")["status"], "failed")
        source = "`![old](flow.svg)`"
        result = checker.compare(source, source.replace("!", ""))
        self.assertEqual({v["category"] for v in result["violations"]}, {"inline_code"})

    def test_task_completion_state_is_protected_while_labels_can_change(self):
        for prefix in ("- ", "* ", "+ ", "1. ", "  2) "):
            for before, after in (("[ ]", "[x]"), ("[X]", "[ ]")):
                source = prefix + before + " Review the draft.\n"
                with self.subTest(prefix=prefix, before=before):
                    result = checker.compare(source, source.replace(before, after))
                    self.assertEqual(result["status"], "failed")
                    self.assertIn("task_markers", {v["category"] for v in result["violations"]})
                    self.assertEqual(checker.compare(source, source.replace("Review the draft", "Review draft"))["status"], "passed")

    def test_task_markers_do_not_capture_prose_or_escape_code_boundaries(self):
        self.assertEqual(checker.compare("Use [x] as a label.", "Use [y] as a label.")["status"], "passed")
        for source, category in (("`- [ ] task`", "inline_code"), ("```\n- [ ] task\n```\n", "fences"),
                                 ("> - [ ] task\n", "blockquotes")):
            result = checker.compare(source, source.replace("[ ]", "[x]"))
            self.assertEqual({v["category"] for v in result["violations"]}, {category})

    def test_unicode_and_control_separators_do_not_create_markdown_lines(self):
        for separator in ("\v", "\f", "\x1c", "\x1d", "\x1e", "\x85", "\u2028", "\u2029"):
            with self.subTest(separator=repr(separator)):
                self.assertEqual(checker.compare("intro" + separator + "> old",
                                                 "intro" + separator + "> new")["status"], "passed")
                fake_close = "```\nkeep" + separator + "```\nsecret"
                self.assertEqual(checker.compare(fake_close, fake_close)["status"], "unsupported")
                real_close = fake_close + "\n```\n"
                self.assertEqual(checker.compare(real_close, real_close)["status"], "passed")
                self.assertEqual(checker.compare(real_close, real_close.replace("secret", "changed"))["status"], "failed")

    def test_fence_closers_allow_only_spaces_and_tabs(self):
        for newline in ("\n", "\r\n"):
            source = newline.join(("~~~", "keep", "~~~ \t", "editable"))
            self.assertEqual(checker.compare(source, source.replace("editable", "revised"))["status"], "passed")
            for separator in ("\v", "\u2028", "\u00a0"):
                fake = source.replace("~~~ \t", "~~~" + separator)
                self.assertEqual(checker.compare(fake, fake)["status"], "unsupported")

    def test_shortcut_label_normalization_preserves_link_identity(self):
        definitions = "\n\n[User  Guide]: https://example.test/guide\n"
        for label in ("User Guide", " user\tguide ", "USER   GUIDE"):
            with self.subTest(label=label):
                result = checker.compare(f"Read [{label}]." + definitions,
                                         "Read [Other]." + definitions)
                self.assertEqual(result["status"], "failed")

    def test_explicit_link_text_is_editable_even_if_it_matches_a_definition(self):
        definitions = "\n\n[id]: target\n[other]: elsewhere\n"
        for source in ("[id](url)", "[id][other]", r"\[id]"):
            with self.subTest(source=source):
                self.assertEqual(checker.compare(source + definitions,
                                                 source.replace("id", "label") + definitions)["status"], "passed")

    def test_multiline_shortcut_is_unsupported_instead_of_silently_unprotected(self):
        source = "[user\nguide]\n\n[user guide]: target\n"
        self.assertEqual(checker.compare(source, source)["status"], "unsupported")

    def test_even_backslash_escape_still_has_a_shortcut_link(self):
        source = r"\\[id]" + "\n\n[id]: target\n"
        self.assertEqual(checker.compare(source, source.replace("[id]", "[other]", 1))["status"], "failed")


class MathSpanChecks(unittest.TestCase):
    def test_formula_symbols_and_commands_cannot_change_with_identical_numbers(self):
        for formula in (r"\(E=mc^2\)", r"\[E=mc^2\]", "\\[\nE=mc^2\n\\]",
                        r"\(\frac{E}{m}=c^2\)"):
            with self.subTest(formula=formula):
                source = "We can use " + formula + "."
                result = checker.compare(source, source.replace("c^2", "v^2"))
                self.assertEqual(result["status"], "failed")
                self.assertEqual({v["category"] for v in result["violations"]}, {"math"})
                self.assertEqual(checker.compare(source, source.replace("We can use", "Use"))["status"], "passed")

    def test_math_code_and_escaped_delimiters_keep_their_own_boundaries(self):
        for source, category in ((r"`\(x^2\)`", "inline_code"), ("```tex\n\\(x^2\\)\n```\n", "fences"),
                                 ("> \\(x^2\\)\n", "blockquotes")):
            result = checker.compare(source, source.replace("x^2", "y^2"))
            self.assertEqual({v["category"] for v in result["violations"]}, {category})
        source = r"\\(ordinary text\\)"
        self.assertEqual(checker.compare(source, source.replace("ordinary", "editable"))["status"], "passed")
        source = r"\(x \\) + y\)"
        self.assertEqual(checker.compare(source, source.replace("y", "z"))["status"], "failed")

    def test_unpaired_escapes_remain_prose_and_paired_math_shields_markdown(self):
        for source in (r"\(x + y", "\\[\nx + y", r"\[ordinary bracket]", r"\(ordinary parenthesis)"):
            self.assertEqual(checker.compare(source, source)["status"], "passed")
        source = "\\[\n    x + y\n```\n\\]\nEditable prose."
        self.assertEqual(checker.compare(source, source.replace("Editable", "Revised"))["status"], "passed")

    def test_repeated_unpaired_escapes_have_bounded_runtime(self):
        script = "from prose_scan import snapshot; snapshot((chr(92)+'(text ')*20000)"
        process = subprocess.run([sys.executable, "-B", "-c", script], cwd=SCRIPTS,
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)


class PlaceholderChecks(unittest.TestCase):
    def test_brace_fields_preserve_names_accessors_conversions_and_formats(self):
        for before, after in (("{name}", "{user}"), ("{user.name}", "{user.id}"),
                              ("{items[0]}", "{items[1]}"), ("{data[key]}", "{data[value]}"),
                              ("{value!r}", "{value!s}"), ("{amount:,.2f}", "{total:,.2f}"),
                              ("{0:08d}", "{0:8d}"), ("{:.2f}", "{:.3f}"), ("{}", "")):
            with self.subTest(before=before):
                result = checker.compare("Use " + before, "Use " + after)
                self.assertEqual(result["status"], "failed", result)
                self.assertIn("placeholders", {row["category"] for row in result["violations"]})
                self.assertEqual(checker.compare("Please use " + before, "Use " + before)["status"], "passed")

    def test_brace_subset_does_not_consume_general_expressions_or_protected_code(self):
        for source in ('{ "key": "value" }', '{x + y}', '{ first choice }', '{a,b}'):
            self.assertNotIn("placeholders", prose_scan.snapshot(source).items())
        result = checker.compare("`{name}`", "`{value}`")
        self.assertEqual({row["category"] for row in result["violations"]}, {"inline_code"})
        for source in ("{{ name }}", "${name}", "{value!r:>8}"):
            self.assertEqual(prose_scan.snapshot(source).items()["placeholders"], [source])

    def test_long_unclosed_braces_and_invalid_printf_fields_have_bounded_runtime(self):
        script = ("from prose_scan import snapshot; "
                  "[snapshot(s) for s in ('{'*100000, '{name:'+'x'*100000, '%'+'0'*100000+'z', '%1'*40000)]")
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


class QuantityChecks(unittest.TestCase):
    def test_ratio_and_fraction_operands_keep_order_and_spelling(self):
        for before, after in (("1:3", "3:1"), ("1/4", "4/1"), ("1.5 : 2.5", "2.5 : 1.5"),
                              ("1∶2∶3", "3∶2∶1"), ("-1⁄4", "4⁄-1"),
                              ("1/4", "1:4"), ("1/4", "1 / 4"), ("1e3/2e3", "2e3/1e3")):
            with self.subTest(before=before):
                self.assert_change("Ratio: " + before, "Ratio: " + after)
                self.assertEqual(prose_scan.numbers(prose_scan.snapshot(before)), [before])
        self.assertEqual(checker.compare("A: 1:3. B: 1/4.", "B: 1/4. A: 1:3.")["status"], "passed")

    def test_ratio_recognition_does_not_bridge_hidden_content_or_physical_lines(self):
        for source in ("1\n/4", "1 / `x` 4", "1 :\n3", "1;3", "1 and 3"):
            with self.subTest(source=source):
                self.assertEqual(len(prose_scan.numbers(prose_scan.snapshot(source))), 2)
        self.assertEqual(checker.compare("Ratio `1:3`", "Ratio `3:1`")["violations"][0]["category"], "inline_code")
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("2026/10/30 at 12:34:56")),
                         ["2026/10/30", "12:34:56"])

    def test_range_endpoints_and_separator_spelling_are_protected_together(self):
        for separator in ("–", "—", "-", " - ", "..", "…", "~", " ~ ", "～", "〜"):
            before = "Forecast: 5%" + separator + "10%."
            after = "Forecast: 10%" + separator + "5%."
            with self.subTest(separator=separator):
                self.assert_change(before, after)
                self.assertEqual(prose_scan.numbers(prose_scan.snapshot(before)), ["5%" + separator + "10%"])
        for before, after in (("-5--1", "-1--5"), ("5–10", "10–5"), ("5–10", "5-10"),
                              ("5~10", "10~5"), ("5~10", "5-10"), ("5～10", "10～5")):
            self.assert_change(before, after)
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("5.0..10.5")), ["5.0..10.5"])
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("Wait ~10 ms.")), ["~10 ms"])

    def test_range_checks_allow_prose_reordering_without_crossing_boundaries(self):
        self.assertEqual(checker.compare("A: 5%–10%. B: 2–3 ms.", "B: 2–3 ms. A: 5%–10%.")["status"], "passed")
        for source in ("5%\n-10%", "5% – `middle` 10%", "5% and 10%"):
            self.assertEqual(len(prose_scan.numbers(prose_scan.snapshot(source))), 2)
        self.assertEqual(checker.compare("First: 5%. Next: 10%.", "Next: 10%. First: 5%.")["status"], "passed")

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

    def test_numeric_comparison_direction_and_inclusivity_are_preserved(self):
        for before, after in (("p < 0.05", "p > 0.05"), ("delay <= 5 ms", "delay < 5 ms"),
                              ("利润 ≥ USD 5 million", "利润 ≤ USD 5 million"),
                              ("Value ≈ 3", "Value = 3"), ("count != 2", "count == 2")):
            with self.subTest(before=before):
                self.assert_change(before, after)

    def test_numeric_bounds_keep_normal_prose_and_markup_boundaries(self):
        self.assertEqual(checker.compare("Retry while delay <= 5 ms.", "While delay <= 5 ms, retry.")["status"], "passed")
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("limit <= `threshold` 5")), ["5"])
        self.assertEqual(prose_scan.numbers(prose_scan.snapshot("Profit < (USD 5)")), ["< (USD 5)"])

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
        # Masked content separates currency labels from later amounts.
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
        # Negation with an unchanged number is covered in test_check_rewrite.py.
        for before, after in [("A: USD 5 million; B: EUR 6 million.", "A: EUR 6 million; B: USD 5 million."),
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

"""Mechanical preservation, explicit exceptions, and documented blind spots."""

import json
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "core" / "yaya" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import check_rewrite as checker
import prose_scan


class RewriteChecks(unittest.TestCase):
    def test_one_shot_literal_protections_match_lists_and_file_evidence(self):
        before, after = "Use retry_limit.", "Use retry_count."
        expected = checker.compare(before, after, literals=["retry_limit"])
        self.assertEqual(expected["status"], "failed")
        self.assertEqual(checker.compare(before, after, literals=iter(["retry_limit"])), expected)
        self.assertEqual(checker.compare(before, after, literals=["retry_limit"] * 2), expected)
        with tempfile.TemporaryDirectory(dir=SCRIPTS.parents[2]) as temp:
            old, new = Path(temp) / "old.md", Path(temp) / "new.md"
            old.write_text(before, encoding="utf-8")
            new.write_text(after, encoding="utf-8")
            result = checker.check_files(old, new, literals=iter(["retry_limit"]))
            self.assertEqual(result["status"], "failed")
            self.assertEqual(result["evidence"]["options"]["literals"], ["retry_limit"])
            self.assertEqual(checker.check_files(old, old, literals=iter(["retry_limit"]))["status"], "passed")

    def test_invalid_literal_containers_are_input_errors(self):
        for values in ("retry_limit", b"retry_limit", None, 1, [1], [None], [""]):
            with self.subTest(values=values), self.assertRaises(prose_scan.InputError):
                checker.compare("Use retry_limit.", "Use retry_limit.", literals=values)

    def assert_status(self, status, before, after, **options):
        result = checker.compare(before, after, **options)
        self.assertEqual(result["status"], status, result)
        return result

    def test_plain_prose_can_change_across_languages(self):
        for before, after in [
            ("进行分析后，再进行发送。", "分析后再发送。"),
            ("Please proceed to retry.", "Retry."),
            ("資料をご確認ください。", "資料を確認してください。"),
            ("請確認資料。", "請核對資料。"),
            ("자료를 확인하세요.", "자료를 검토하세요."),
        ]:
            self.assert_status("passed", before, after)

    def test_python_api_rejects_inputs_outside_the_utf8_newline_contract(self):
        for text in ("before\x00after", "before\rafter", "unpaired\ud800"):
            with self.subTest(text=repr(text)), self.assertRaises(prose_scan.InputError):
                checker.compare(text, text)

    def test_api_retains_bom_crlf_and_non_ascii_prose(self):
        self.assert_status("passed", "\ufeff进行分析。\r\n", "\ufeff分析。\r\n")

    def test_protected_categories_reject_changes_removal_and_duplication(self):
        cases = [
            ("frontmatter", "---\ntitle: old\n---\n正文", "old", "new"),
            ("fences", "```py\nvalue = 1\n```\n正文", "value = 1", "value = 2"),
            ("inline_code", "使用 `retry_limit`。", "retry_limit", "retry_count"),
            ("link_targets", "[标签](https://example.test/a)", "/a", "/b"),
            ("html", "<span id='a'>正文</span>", "id='a'", "id='b'"),
            ("html", "<!-- exact -->\n正文", "exact", "edited"),
            ("explicit_ids", "标题 {#stable}", "stable", "changed"),
            ("placeholders", "你好 {{name}}，${USER}，%s，:param", "{{name}}", "{{other}}"),
            ("urls", "访问 https://example.test/a。", "/a", "/b"),
            ("blockquotes", "> 原文\n引用延续\n\n正文", "原文", "改文"),
            ("tables", "| 名称 | 值 |\n| --- | --- |\n| 甲 | 12 |\n", "12", "13"),
        ]
        for category, original, old, new in cases:
            with self.subTest(category=category):
                result = self.assert_status("failed", original, original.replace(old, new))
                self.assertIn(category, {item["category"] for item in result["violations"]})
                self.assert_status("failed", original, "")
                duplicate = original.replace("title: old", "title: old\ntitle: old") if category == "frontmatter" else original + "\n\n" + original
                self.assert_status("failed", original, duplicate)

    def test_link_labels_can_change_but_targets_titles_and_reference_ids_cannot(self):
        self.assert_status("passed", "[旧标签](https://example.test/a)", "[新标签](https://example.test/a)")
        self.assert_status("failed", '[a](url "title")', '[a](url "different")')
        self.assert_status("failed", "[Label][id]\n\n[id]: url\n", "[Label][other]\n\n[id]: url\n")
        self.assert_status("failed", "[id][]\n\n[id]: url\n", "[other][]\n\n[id]: url\n")
        self.assert_status("failed", "[id]\n\n[id]: url\n", "[other]\n\n[id]: url\n")
        self.assert_status("failed", "[label]: url\n", "[label]: changed\n")
        for reference in ("[A `x`][]", "[A `x`]"):
            source = reference + "\n\n[A `x`]: url\n"
            self.assert_status("failed", source, source.replace(reference, reference.replace("A", "B"), 1))

    def test_balanced_link_parentheses_and_code_ticks(self):
        source = "[label](https://example.test/a_(b)) plus ``a ` b``"
        self.assert_status("passed", source, source.replace("label", "text"))
        self.assert_status("failed", source, source.replace("_(b)", "_(c)"))
        self.assert_status("failed", source, source.replace("a ` b", "a ` c"))

    def test_apostrophes_in_urls_are_not_link_title_delimiters(self):
        source = "[O'Brien](https://en.wikipedia.org/wiki/Tim_O'Brien)"
        self.assert_status("passed", source, source)
        self.assert_status("failed", source, source.replace("Tim_O'Brien", "Another"))
        source = "[Link](https://example.test/O'Brien 'Quoted title')"
        self.assert_status("passed", source, source)
        self.assert_status("failed", source, source.replace("Quoted title", "Changed title"))

    def test_html_comments_shield_embedded_markdown_before_block_scan(self):
        for content in [
            "```text\nexact code\n```", "```\nunclosed fence",
            "| A | B |\n| --- | --- |\n| x | y |",
            "    indented example", "[^note]: a footnote",
        ]:
            source = "<!-- Keep this source note.\n" + content + "\n-->\n"
            with self.subTest(content=content):
                self.assert_status("passed", source, source)
                result = self.assert_status("failed", source, source.replace("Keep", "Changed"))
                self.assertIn("html", [item["category"] for item in result["violations"]])
        self.assert_status("passed", "<!-- exact --> Old prose", "<!-- exact --> New prose")

    def test_single_column_markdown_tables_are_protected(self):
        source = "| Name |\n| --- |\n| Alice |\n"
        result = self.assert_status("failed", source, source.replace("Alice", "Bob"))
        self.assertIn("tables", [item["category"] for item in result["violations"]])
        source = "| `Name` |\n| --- |\n| Alice |\n"
        self.assert_status("failed", source, source.replace("Alice", "Bob"))

    def test_multiline_inline_code_shields_comment_looking_text(self):
        source = 'Use `literal\n<!-- comment-looking text -->\nend` here.'
        self.assert_status("passed", source, source)
        self.assert_status("failed", source, source.replace("comment-looking", "changed"))

    def test_nested_quotes_inside_code_do_not_mask_editable_prose(self):
        source = 'Code `print("x")`. “保留 `name` 和文字”。'
        self.assert_status("failed", source, source.replace("和文字", "与文本"), protect_quotes=True)
        self.assert_status("passed", source, source.replace("和文字", "与文本"))

    def test_blockquotes_default_and_plain_quoted_spans_opt_in(self):
        self.assert_status("failed", "> Original quote\n", "> Rewritten quote\n")
        self.assert_status("passed", 'He said "old".', 'He said "new".')
        self.assert_status("failed", 'He said "old".', 'He said "new".', protect_quotes=True)
        for source in ['“保持原文”', '「保持原文」', '『保持原文』', '《保持原文》', '"keep \\"this\\" exact"']:
            self.assert_status("failed", source, "", protect_quotes=True)
        self.assert_status("unsupported", '"unfinished', '"unfinished', protect_quotes=True)
        source = 'She wrote: “The analysis is complete,\nand the result is ready.”'
        self.assert_status("passed", source, source, protect_quotes=True)
        self.assert_status("failed", source, source.replace("complete", "unfinished"), protect_quotes=True)

    def test_explicit_literals_protect_names_paths_and_identifiers(self):
        source = "路径 src/app.py，标识 retry_limit，作者 Alice。"
        for literal in ("src/app.py", "retry_limit", "Alice"):
            self.assert_status("failed", source, source.replace(literal, "changed"), literals=[literal])
        self.assert_status("failed", "Alice Alice", "Alice", literals=["Alice"])
        with self.assertRaises(prose_scan.InputError):
            checker.compare("A", "A", literals=["absent"])
        with self.assertRaises(prose_scan.InputError):
            checker.compare("A", "A", literals=[""])

    def test_nested_placeholder_looking_text_does_not_unprotect_outer_structure(self):
        self.assert_status("failed", "{#section:part}", "{#other:part}")
        self.assert_status("failed", "https://example.test/:id", "https://changed.test/:id")

    def test_number_units_signs_decimals_counts_and_percentages(self):
        source = "甲975万元，同比-7%；乙640万元，同比+4.5%。Retry after 2 ms at 10%."
        for old, new in [("975", "976"), ("-7", "+7"), ("4.5", "45"), ("万元", "亿元"), ("2 ms", "2 s"), ("10%", "10")]:
            result = self.assert_status("failed", source, source.replace(old, new))
            self.assertIn("numbers", [item["category"] for item in result["violations"]])
        self.assert_status("failed", "Count 2 and 2.", "Count 2.")
        self.assert_status("failed", "Wait 2 seconds.", "Wait 2 minutes.")
        self.assert_status("failed", "Pay $20.", "Pay €20.")
        self.assert_status("failed", "Balance $-20.", "Balance $20.")
        self.assert_status("passed", "Retry 2 次。", "再试 2 次。")

    def test_lexically_identical_numbers_do_not_prove_entity_pairing_or_negation(self):
        self.assert_status("passed", "甲有 2 个，乙有 3 个。", "甲有 3 个，乙有 2 个。")
        result = self.assert_status("passed", "Do not retry after 2 failures.", "Retry after 2 failures.")
        self.assertTrue(any("associations" in line for line in result["limitations"]))

    def test_allow_binds_exact_candidate_and_difference(self):
        original = "Count 2, `id`."
        candidate = "Count 3, `id`."
        difference = {key: checker.compare(original, candidate)["changes"][0][key]
                      for key in ("category", "before", "after")}
        grant = {"schema": 1, "before_sha256": hashlib.sha256(original.encode()).hexdigest(),
                 "after_sha256": hashlib.sha256(candidate.encode()).hexdigest(), "changes": [difference]}
        allowed = self.assert_status("passed", original, candidate, allow=grant)
        self.assertEqual(allowed["changes"][0]["allowed"], True)
        changed = "Count 3, `other`."
        grant["after_sha256"] = hashlib.sha256(changed.encode()).hexdigest()
        result = self.assert_status("failed", original, changed, allow=grant)
        self.assertEqual([item["category"] for item in result["violations"]], ["inline_code"])
        for broad in (["all"], ["numbers"], "numbers"):
            with self.subTest(broad=broad), self.assertRaises(prose_scan.InputError):
                checker.compare(original, candidate, allow=broad)
        with self.assertRaisesRegex(prose_scan.InputError, "exact"):
            checker.compare(original, "Count 4, `id`.", allow=grant)
        grant["after_sha256"] = hashlib.sha256(candidate.encode()).hexdigest()
        grant["changes"][0]["after"] = ["4"]
        with self.assertRaisesRegex(prose_scan.InputError, "inexact"):
            checker.compare(original, candidate, allow=grant)

    def test_allow_manifest_validates_types_and_unused_or_unknown_entries(self):
        old, new = "Count 2.", "Count 3."
        base = {"schema": 1, "before_sha256": hashlib.sha256(old.encode()).hexdigest(),
                "after_sha256": hashlib.sha256(new.encode()).hexdigest()}
        invalid = [{"category": [], "before": [], "after": []},
                   {"category": "numbers", "before": "2", "after": ["3"]},
                   {"category": "unknown", "before": ["2"], "after": ["3"]},
                   {"category": "numbers", "before": ["2"], "after": ["3"], "all": True}]
        for entry in invalid:
            with self.subTest(entry=entry), self.assertRaises(prose_scan.InputError):
                checker.compare(old, new, allow={**base, "changes": [entry]})

    def test_noncontent_newlines_and_bom_have_explicit_boundaries(self):
        self.assert_status("passed", "正文\r\n第二行\r\n", "正文\n第二行\n")
        self.assert_status("failed", "`code`\r\n", "`other`\r\n")
        self.assert_status("failed", "```\r\ncode\r\n```\r\n", "```\ncode\n```\n")
        self.assert_status("failed", "\ufefftext", "text")
        self.assert_status("passed", "\ufefftext", "\ufeffnew")

    def test_unsupported_markdown_is_not_passed_or_silently_ignored(self):
        for source in [
            "```py\nopen", "`open", "---\nopen", "[label](url",
            "[label](url\n)", "    indented code", "- ```py\nx\n```\n",
            "<div>raw content</div>", "<span title='open", "<!--open",
            "[^note]: footnote", "text[^note]", "[label]:\n  multiline", "<p>raw HTML</p>",
        ]:
            with self.subTest(source=source):
                self.assert_status("unsupported", source, source)

    def test_long_incomplete_html_and_link_inputs_fail_without_regex_recursion(self):
        for source in ["<span " + " " * 100_000, "[x](" + "(" * 100_000]:
            self.assert_status("unsupported", source, source)

    def test_plain_comparison_symbols_and_escaped_markup(self):
        self.assert_status("passed", r"1 < 2 and \`literal\`", r"1 < 2; keep \`literal\`")
        self.assert_status("passed", "甲、乙，丙。", "甲；乙；丙。")

    def run_cli(self, before, after, *args, stdin=None):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            first, second = Path(directory) / "before.md", Path(directory) / "after.md"
            first.write_bytes(before)
            second.write_bytes(after)
            result = subprocess.run([sys.executable, str(SCRIPTS / "check_rewrite.py"),
                                     "-" if stdin is not None else str(first), str(second), *args],
                                    input=stdin, capture_output=True, check=False)
            self.assertEqual(first.read_bytes(), before)
            self.assertEqual(second.read_bytes(), after)
            return result, json.loads(result.stdout)

    def test_cli_read_only_stdin_utf8_and_exit_codes(self):
        for old, new, flags, expected in [
            ("进行分析。", "分析。", (), 0),
            ("2 ms", "3 ms", (), 1),
            ("2 ms", "3 ms", ("--allow", "numbers"), 2),
            ("```open", "```open", (), 2),
        ]:
            result, payload = self.run_cli(old.encode(), new.encode(), *flags, stdin=old.encode())
            self.assertEqual(result.returncode, expected, payload)
        result, payload = self.run_cli(b"\xff", b"text")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(payload["status"], "error")

    def test_cli_limits_newlines_and_options_are_structured_errors(self):
        for before, flags in [(b"x" * (prose_scan.MAX_BYTES + 1), ()), (b"text\rnext", ()), (b"a\0b", ()), (b"a", ("--allow", "all"))]:
            result, payload = self.run_cli(before, b"text", *flags)
            self.assertEqual(result.returncode, 2, payload)
            self.assertEqual(payload["status"], "error")


if __name__ == "__main__":
    unittest.main()

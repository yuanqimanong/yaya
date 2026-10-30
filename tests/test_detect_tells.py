"""Literal candidate detection, exclusions, and CLI error boundaries."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "core" / "yaya" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import detect_tells as detector
import prose_scan


class DetectionTests(unittest.TestCase):
    def test_selected_rules_limit_findings_and_report_coverage(self):
        source = "Only time will tell. Conduct an analysis of this."
        result = detector.detect(source, "en", ["en-stock-close", "en-stock-close"])
        self.assertEqual(result["enabled_rules"], ["en-stock-close"])
        self.assertEqual([row["id"] for row in result["findings"]], ["en-stock-close"])
        self.assertEqual(len(detector.detect(source, "en")["enabled_rules"]), 4)
        result = detector.detect("Conduct an analysis of this.", "en", ["en-stock-close"])
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["enabled_rules"], ["en-stock-close"])
        for values in ([], ["typo"], ["zh-stock-close"], "en-stock-close", [None]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                detector.detect(source, "en", values)

    def test_selected_rules_cli_and_thresholds(self):
        process, result = self.run_cli(b"Only time will tell.", "--rule", "en-light-verb", "--fail-on", "P2")
        self.assertEqual(process.returncode, 0)
        self.assertEqual(result["findings"], [])
        self.assertEqual(result["enabled_rules"], ["en-light-verb"])
        for name in ("unknown", "zh-stock-close"):
            process, result = self.run_cli(b"text", "--rule", name)
            self.assertEqual(process.returncode, 2)
            self.assertEqual(result["status"], "error")

    def test_literal_candidates_are_not_authorship_claims(self):
        result = detector.detect("In today's fast-paced world, conduct an analysis of the result.", "en")
        self.assertEqual(result["status"], "ok")
        self.assertEqual({x["id"] for x in result["findings"]}, {"en-empty-opener", "en-light-verb"})
        self.assertTrue(all(x["weak_alone"] and x["severity"] == "P2" for x in result["findings"]))
        self.assertNotIn("probability", result)
        self.assertNotIn("confidence", result["findings"][0])

    def test_chinese_position_and_repeated_candidates(self):
        result = detector.detect("标题\r\n进行分析，然后进行分析。\r\n让我们拭目以待。", "zh-Hans")
        self.assertEqual([x["line"] for x in result["findings"]], [2, 2, 3])
        for finding in result["findings"]:
            text = "标题\r\n进行分析，然后进行分析。\r\n让我们拭目以待。"
            self.assertEqual(text[finding["start"]:finding["end"]], finding["quote"])

    def test_code_quotes_tables_and_markup_are_excluded(self):
        cases = [
            "```text\n进行分析\n```\n",
            "请保留 `进行分析`。",
            "> 进行分析\n引用的延续：进行分析\n",
            "原话是“进行分析”。",
            '"进行分析"',
            "---\ntitle: 进行分析\n---\n",
            "| 名称 | 值 |\n| --- | --- |\n| 进行分析 | 1 |\n",
            "<!-- 进行分析 -->",
            "<span title='进行分析'>清楚的正文</span>",
            "[清楚](https://example.test/进行分析)",
            "https://example.test/进行分析",
        ]
        for source in cases:
            with self.subTest(source=source):
                result = detector.detect(source, "zh-Hans")
                self.assertEqual(result["status"], "ok", result)
                self.assertEqual(result["findings"], [])

    def test_visible_link_label_is_scanned(self):
        result = detector.detect("[进行分析](https://example.test/docs)", "zh-Hans")
        self.assertEqual(len(result["findings"]), 1)

    def test_multiline_html_comments_never_leak_candidates(self):
        for content in [
            "```text\nexact code\n```", "```\nunclosed fence",
            "| A | B |\n| --- | --- |\n| x | y |",
            "    indented example",
        ]:
            source = "<!-- note\n" + content + "\nOnly time will tell.\n-->\n"
            with self.subTest(content=content):
                result = detector.detect(source, "en")
                self.assertEqual(result["status"], "ok", result)
                self.assertEqual(result["findings"], [])

    def test_wrapped_quotes_and_inch_marks_do_not_discard_document(self):
        for source in [
            'She wrote: “Only time will tell,\nand the result is ready.”\nOnly time will tell.',
            'The display is 6" wide. Only time will tell.',
        ]:
            with self.subTest(source=source):
                result = detector.detect(source, "en")
                self.assertEqual(result["status"], "ok", result)
                self.assertEqual(len(result["findings"]), 1)

    def test_many_unmatched_quotes_finish_without_repeated_suffix_scans(self):
        # A real regression input; no timing threshold tied to a particular CPU.
        source = "“" * 100_000 + " Only time will tell."
        result = detector.detect(source, "en")
        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["findings"]), 1)

    def test_casefold_and_word_boundary_do_not_match_embedded_word(self):
        result = detector.detect("ONLY TIME WILL TELL. xonly time will telly.", "en")
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["quote"], "ONLY TIME WILL TELL")

    def test_wrapped_literal_candidates_keep_original_offsets(self):
        for source in ("Only  time\twill tell.", "Only time\nwill tell.", "Only time\r\nwill tell."):
            with self.subTest(source=source):
                findings = detector.detect(source, "en")["findings"]
                self.assertEqual(len(findings), 1)
                row = findings[0]
                self.assertEqual(source[row["start"]:row["end"]], source[:-1])
                self.assertEqual(row["quote"], source[:-1])

    def test_candidate_matching_respects_unicode_words_and_markdown_emphasis(self):
        for source in ("2only time will tell", "only time will tell2", "éonly time will tell", "only time will tellé"):
            with self.subTest(source=source):
                self.assertEqual(detector.detect(source, "en")["findings"], [])
        for source in ("_Only time will tell_", "**Only time will tell**"):
            self.assertEqual(len(detector.detect(source, "en")["findings"]), 1)

    def test_wrapped_detection_does_not_cross_protected_spans_or_paragraphs(self):
        for source in ("Only time `x` will tell.", "Only time\n\nwill tell.", "Only time <!-- x --> will tell."):
            with self.subTest(source=source):
                self.assertEqual(detector.detect(source, "en")["findings"], [])

    def test_clear_prose_and_unlisted_common_words_are_not_candidates(self):
        for language, text in [
            ("en", "The request failed because the token expired. Retry after signing in."),
            ("zh-Hans", "分析还在进行，结果将在核对后公布。"),
            ("en", "The test uses a passive component and a dash — both are needed."),
        ]:
            with self.subTest(language=language):
                self.assertEqual(detector.detect(text, language)["findings"], [])

    def test_api_invalid_text_is_unsupported_not_a_clean_scan(self):
        for text in ("text\x00tail", "text\rtail", "unpaired\ud800"):
            with self.subTest(text=repr(text)):
                result = detector.detect(text, "en")
                self.assertEqual(result["status"], "unsupported")
                self.assertEqual(result["findings"], [])

    def test_other_languages_and_ambiguous_markdown_are_unsupported(self):
        for language in ["ja", "ko", "zh-Hant", "zh", "en-US"]:
            self.assertEqual(detector.detect("text", language)["status"], "unsupported")
        for source in ["```\nunfinished", "`unfinished", "<script>进行分析</script>", "[a](url\n)", "    code"]:
            self.assertEqual(detector.detect(source, "en")["status"], "unsupported")

    def run_cli(self, data=b"", *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "detect_tells.py"), "-", "--language", "en", *args],
            input=data, capture_output=True, check=False,
        )
        return result, json.loads(result.stdout)

    def test_cli_default_and_explicit_thresholds(self):
        for flags, code in [((), 0), (("--fail-on", "P1"), 0), (("--fail-on", "P2"), 1)]:
            result, payload = self.run_cli(b"Only time will tell.", *flags)
            self.assertEqual(result.returncode, code, payload)
            self.assertEqual(payload["status"], "ok")

    def test_cli_invalid_encoding_size_and_arguments_are_json(self):
        for data, args in [(b"\xff", ()), (b"x" * (prose_scan.MAX_BYTES + 1), ()), (b"hello", ("--fail-on", "all"))]:
            result, payload = self.run_cli(data, *args)
            self.assertEqual(result.returncode, 2, payload)
            self.assertEqual(payload["status"], "error")

    def test_cli_file_is_read_only_and_json_alias_works(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
            path = Path(directory) / "中文 空格.md"
            original = b"\xef\xbb\xbfOnly time will tell.\r\n"
            path.write_bytes(original)
            result = subprocess.run([sys.executable, str(SCRIPTS / "detect_tells.py"), str(path),
                                     "--language", "en", "--json"], capture_output=True, check=False)
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertEqual(len(json.loads(result.stdout)["findings"]), 1)
            self.assertEqual(path.read_bytes(), original)

    def test_missing_file_is_structured_error(self):
        result = subprocess.run([sys.executable, str(SCRIPTS / "detect_tells.py"), str(SCRIPTS / "absent-input.md"),
                                 "--language", "en"], capture_output=True, check=False)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout)["status"], "error")


if __name__ == "__main__":
    unittest.main()

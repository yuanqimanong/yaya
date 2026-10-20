"""Boundary tests for the read-only Python comment checker."""

import codecs
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "core" / "yaya" / "scripts" / "check_comments.py"
SPEC = importlib.util.spec_from_file_location("yaya_check_comments", SCRIPT)
CHECKER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CHECKER
SPEC.loader.exec_module(CHECKER)


class CommentChecks(unittest.TestCase):
    def check(self, before, after, suffix=".py"):
        before = before.encode("utf-8") if isinstance(before, str) else before
        after = after.encode("utf-8") if isinstance(after, str) else after
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            original = Path(directory) / ("before" + suffix)
            candidate = Path(directory) / "candidate.tmp"
            original.write_bytes(before)
            candidate.write_bytes(after)
            result = CHECKER.check_files(original, candidate)
            self.assertEqual(original.read_bytes(), before)
            self.assertEqual(candidate.read_bytes(), after)
        self.assertIn("limitations", result)
        return result

    def assert_status(self, status, before, after, suffix=".py"):
        result = self.check(before, after, suffix)
        self.assertEqual(result["status"], status, result)
        return result

    def test_ordinary_comment_rewrites(self):
        result = self.assert_status(
            "passed",
            "# 读取数据\nx = 1  # 初始值\n",
            "# Read input data.\nx = 1  # Start at one.\n",
        )
        self.assertEqual(result["changed_comment_lines"], [1, 2])

    def test_code_string_and_whitespace_changes_fail(self):
        cases = [
            ("x = 1 # old\n", "x = 2 # new\n"),
            ('x = "# old" # comment\n', 'x = "# new" # rewritten\n'),
            ("x = 1 # old\n", "x = 1  # new\n"),
            ("if True:\n    x = 1 # old\n", "if True:\n\tx = 1 # new\n"),
        ]
        for before, after in cases:
            with self.subTest(before=before):
                self.assert_status("failed", before, after)

    def test_hashes_inside_strings_are_not_comments(self):
        source = 'url = "https://example.test/#anchor"\ntext = "# noqa" # old\n'
        self.assert_status("passed", source, source.replace("# old", "# New comment."))

    def test_docstrings_and_doctests_in_strings_are_immutable(self):
        source = 'def f():\n    """Return one.\n\n    >>> f()\n    1\n    """\n    return 1 # old\n'
        self.assert_status("failed", source, source.replace("Return one.", "Get one."))
        self.assert_status("failed", source, source.replace(">>> f()", ">>> f(1)"))
        self.assert_status("passed", source, source.replace("# old", "# Return the fixed value."))

    def test_triple_string_comment_markers_are_immutable(self):
        source = 'text = """# comment\n# still a string\n"""\n'
        self.assert_status("failed", source, source.replace("still", "not"))

    def test_known_directives_are_protected(self):
        directives = [
            "#!/usr/bin/env python3",
            "# type: ignore[arg-type]",
            "# noqa: F401",
            "# pylint: disable=unused-import",
            "# pyright: ignore",
            "# mypy: ignore-errors",
            "# ruff: noqa",
            "# fmt: off",
            "# isort: skip",
            "# pragma: no cover",
            "# doctest: +ELLIPSIS",
            "# cython: language_level=3",
            "# nosec B101",
            "# TODO: fix this",
            "#: documentation metadata",
            "# SPDX-License-Identifier: MIT",
        ]
        for directive in directives:
            with self.subTest(directive=directive):
                self.assert_status("failed", directive + "\nx = 1\n", directive + " changed\nx = 1\n")

    def test_cannot_introduce_directive_by_rewriting_prose(self):
        self.assert_status("failed", "x = 1 # ordinary\n", "x = 1 # type: ignore\n")

    def test_directive_after_prose_is_protected(self):
        self.assert_status("failed", "x = 1 # explanation # noqa: F841\n", "x = 1 # explanation\n")

    @unittest.skipIf(sys.version_info < (3, 12), "Comments in f-strings require Python 3.12+")
    def test_fstring_comments_are_immutable(self):
        # Debug f-string output can contain expression comments, so keep all f-strings intact.
        for source in ('x = f"""{1 # old\n}"""\n', 'x = f"""{1 # old\n=}"""\n'):
            with self.subTest(source=source):
                self.assert_status("failed", source, source.replace("# old", "# new"))

    @unittest.skipIf(sys.version_info < (3, 14), "Template strings require Python 3.14+")
    def test_tstring_comments_are_immutable(self):
        # Template interpolation exposes its expression text at runtime.
        for source in ('x = t"""{1 # old\n}"""\n', 'x = t"""{1 # old\n=}"""\n'):
            with self.subTest(source=source):
                self.assert_status("passed", source, source)
                self.assert_status("failed", source, source.replace("# old", "# new"))

    def test_commented_doctest_output_is_protected(self):
        source = "# Example:\n# >>> 1 + 1\n# 2\nx = 1 # old\n"
        self.assert_status("failed", source, source.replace("# 2", "# 3"))
        self.assert_status("passed", source, source.replace("# old", "# new"))

    def test_comment_addition_deletion_or_layout_change_fails(self):
        cases = [
            ("x = 1\n", "x = 1 # extra\n"),
            ("x = 1 # old\n", "x = 1\n"),
            ("# old\nx = 1\n", "# first\n# second\nx = 1\n"),
            ("# old\nx = 1\n", " # new\nx = 1\n"),
            ("# old\n", "# new"),
        ]
        for before, after in cases:
            with self.subTest(before=before):
                self.assert_status("failed", before, after)

    def test_multiline_expression_preserves_comments_and_executable_structure(self):
        source = "value = (\n    1  # first part\n    + 2  # second part\n)\n# final note\n"
        rewritten = source.replace("# first part", "# Initial term.").replace("# second part", "# Add two.")
        result = self.assert_status("passed", source, rewritten)
        self.assertEqual(result["changed_comment_lines"], [2, 3])
        self.assert_status("failed", source, rewritten.replace("+ 2", "+ 3"))
        self.assert_status("failed", source, rewritten.replace("    + 2", "  + 2"))

    def test_doctest_blocks_stop_at_code_and_blank_line_boundaries(self):
        source = "# >>> 1 + 1\n# 2\n\n# ordinary prose\nx = 1  # inline prose\n"
        result = self.assert_status("passed", source, source.replace("prose", "explanation"))
        self.assertEqual(result["changed_comment_lines"], [4, 5])
        self.assert_status("failed", source, source.replace("# 2", "# 3"))
        self.assert_status("failed", source, source.replace("# ordinary prose", "# >>> x"))

    def test_crlf_and_mixed_newlines_preserved(self):
        source = b"# old\r\nx = 1 # old\n"
        self.assert_status("passed", source, source.replace(b"old", b"new"))
        self.assert_status("failed", source, source.replace(b"\r\n", b"\n"))
        self.assert_status("failed", source, source.replace(b"# old\r\n", b"# new\n"))

    def test_bom_must_be_preserved(self):
        source = codecs.BOM_UTF8 + b"# old\nx = 1\n"
        self.assert_status("passed", source, source.replace(b"old", b"new"))
        self.assert_status("failed", source, source[len(codecs.BOM_UTF8) :])
        self.assert_status("failed", b"# old\n", codecs.BOM_UTF8 + b"# old\n")

    def test_encoding_cookie_and_legacy_encoding(self):
        before = "# coding: cp1252\nname = 'café' # ancien\n".encode("cp1252")
        after = "# coding: cp1252\nname = 'café' # nouveau\n".encode("cp1252")
        self.assert_status("passed", before, after)
        self.assert_status("failed", before, after.replace(b"cp1252", b"latin-1"))
        self.assert_status("failed", before, after.decode("cp1252").encode("utf-8"))

    def test_second_line_encoding_cookie_is_protected(self):
        source = b"#!/usr/bin/python\n# -*- coding: utf-8 -*-\nx = 1 # old\n"
        self.assert_status("failed", source, source.replace(b"utf-8", b"UTF-8"))

    def test_unicode_is_preserved_outside_comments(self):
        before = "变量 = 'café 漢字 한국어' # 说明\n"
        self.assert_status("passed", before, before.replace("# 说明", "# 説明 / 설명"))
        self.assert_status("failed", before, before.replace("café", "cafe\u0301"))

    def test_unicode_line_separator_in_string_is_not_physical_line(self):
        before = 'x = "a\u2028b" # old\n'
        self.assert_status("passed", before, before.replace("# old", "# new"))

    def test_unterminated_last_comment_can_be_edited(self):
        self.assert_status("passed", "x = 1 # old", "x = 1 # new")

    def test_empty_sources_and_stub(self):
        self.assert_status("passed", b"", b"")
        self.assert_status("passed", "def f() -> int: ... # old\n", "def f() -> int: ... # new\n", ".pyi")

    def test_invalid_baseline_is_unsupported_candidate_is_failed(self):
        self.assert_status("unsupported", "x = (\n", "x = (\n")
        self.assert_status("failed", "x = 1\n", "x = (\n")
        self.assert_status("unsupported", b"x = '\xff'\n", b"x = '\xff'\n")

    def test_lone_cr_is_never_treated_as_mutable_comment_text(self):
        self.assert_status("unsupported", b"# old\rx = 1\r", b"# new\rx = 2\r")
        self.assert_status("failed", b"# old\nx = 1\n", b"# new\rx = 2\r")

    def test_javascript_and_typescript_are_unsupported(self):
        for extension in (".js", ".jsx", ".ts", ".tsx"):
            with self.subTest(extension=extension):
                self.assert_status("unsupported", "const x = 1; // old\n", "const x = 1; // new\n", extension)

    def test_cli_json_and_exit_codes(self):
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent) as directory:
            before = Path(directory) / "before.py"
            after = Path(directory) / "after.tmp"
            before.write_bytes(b"x = 1 # old\n")
            cases = [(b"x = 1 # new\n", 0, "passed"), (b"x = 2 # new\n", 1, "failed")]
            for content, exit_code, status in cases:
                after.write_bytes(content)
                run = subprocess.run([sys.executable, str(SCRIPT), str(before), str(after)], capture_output=True, text=True)
                self.assertEqual(run.returncode, exit_code, run.stderr)
                self.assertEqual(json.loads(run.stdout)["status"], status)
            run = subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True)
            self.assertEqual(run.returncode, 2)
            self.assertEqual(json.loads(run.stdout)["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()

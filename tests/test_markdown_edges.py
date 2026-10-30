"""Markdown preservation regressions using rendered-link semantics."""
import unittest
from test_check_rewrite import checker


class ReferenceChecks(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()

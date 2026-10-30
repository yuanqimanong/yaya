"""Markdown preservation regressions using rendered-link semantics."""
import unittest
from test_check_rewrite import checker


class ReferenceChecks(unittest.TestCase):
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

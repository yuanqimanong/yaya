"""Formula source is protected independently of its mathematical correctness."""
import subprocess
import sys
import unittest
from test_check_rewrite import checker, SCRIPTS


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


if __name__ == "__main__":
    unittest.main()

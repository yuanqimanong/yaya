"""Exact-node docstring boundaries; deliberately no semantic correctness claims."""

import codecs
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = Path(__file__).resolve().parents[1] / "core/yaya/scripts"
sys.path.insert(0, str(SCRIPTS))
import check_docstrings as checker
from edit_evidence import digest


class DocstringChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.tmp.cleanup)
        self.before = Path(self.tmp.name) / "before.py"
        self.after = Path(self.tmp.name) / "candidate.tmp"

    def prepare(self, before, after):
        self.old = before.encode() if isinstance(before, str) else before
        self.new = after.encode() if isinstance(after, str) else after
        self.before.write_bytes(self.old)
        self.after.write_bytes(self.new)

    def grant(self, nodes):
        old = checker.parse(self.old, "before.py")[2]
        new = checker.parse(self.new, "after.py")[2]
        return {"schema": 1, "before_sha256": digest(self.old), "after_sha256": digest(self.new),
                "docstrings": [{"node": node, "before_sha256": digest(old[node]["literal"]),
                                "after_sha256": digest(new[node]["literal"])} for node in nodes]}

    def check(self, grant):
        result = checker.check_files(self.before, self.after, grant)
        self.assertEqual(self.before.read_bytes(), self.old)
        self.assertEqual(self.after.read_bytes(), self.new)
        self.assertIn("evidence", result)
        return result

    def test_authorized_unicode_docstring_only(self):
        old = 'def 获取():\n    """获取第一个非 None 值。"""\n    return False\n'
        self.prepare(old, old.replace("获取第一个", "返回首个"))
        result = self.check(self.grant(["获取@1"]))
        self.assertEqual(result["status"], "passed", result)
        self.assertTrue(result["ast_boundary_equal"])
        self.assertTrue(any("__doc__" in item for item in result["limitations"]))

    def test_unauthorized_docstrings_and_metadata_runtime_prompt_code(self):
        old = '"""Module prose."""\ndef f():\n    """Function prose."""\n    runtime = "Visible message"\n    metadata = dict(comment="Column explanation")\n    prompt = "Keep JSON keys"\n    return 1 # ordinary\n'
        for target in ("Module prose.", "Visible message", "Column explanation", "Keep JSON keys", "# ordinary", "return 1"):
            new = old.replace("Function prose.", "Return a fixed value.").replace(target, target + " changed" if target != "return 1" else "return 2")
            self.prepare(old, new)
            with self.subTest(target=target):
                self.assertEqual(self.check(self.grant(["f@2"]))["status"], "failed")

    def test_missing_wildcard_stale_duplicate_and_overbroad_grants_fail(self):
        old = 'def f():\n    """Old."""\n    pass\n'
        self.prepare(old, old.replace("Old.", "New."))
        good = self.grant(["f@1"])
        grants = [None, ["f@1"], {**good, "after_sha256": "stale"},
                  {**good, "docstrings": [{**good["docstrings"][0], "node": "*"}]},
                  {**good, "docstrings": good["docstrings"] * 2}, {**good, "all": True}]
        for grant in grants:
            with self.subTest(grant=grant):
                self.assertEqual(self.check(grant)["status"], "failed")

    def test_doctest_fences_and_example_sections_protected(self):
        examples = ["    >>> f()\n    1\n", "    ```python\n    f()\n    ```\n",
                    "    Examples:\n        f()\n        1\n", "    Example\n    -------\n    f()\n"]
        for sample in examples:
            old = 'def f():\n    """Old.\n\n' + sample + '    """\n    return 1\n'
            new = old.replace("Old.", "New.")
            self.prepare(old, new)
            with self.subTest(sample=sample):
                self.assertEqual(self.check(self.grant(["f@1"]))["status"], "passed")
                self.prepare(old, new.replace("f()\n", "f(2)\n"))
                self.assertEqual(self.check(self.grant(["f@1"]))["status"], "failed")

    def test_bom_crlf_and_literal_form_are_protected(self):
        old = codecs.BOM_UTF8 + b'def f():\r\n    """Old."""\r\n    return 1\r\n'
        self.prepare(old, old.replace(b"Old", b"New"))
        self.assertEqual(self.check(self.grant(["f@1"]))["status"], "passed")
        self.assertEqual(self.check(self.grant(["f@1"]))["evidence"]["before"]["crlf"], 3)
        for new in (self.new[3:], self.new.replace(b"\r\n", b"\n"),
                    self.new.replace(b'"""New."""', b'\'\'\'New.\'\'\''),
                    self.new.replace(b'New.', b'New.\r\n    More.')):
            self.prepare(old, new)
            with self.subTest(new=new):
                self.assertEqual(self.check(self.grant(["f@1"]))["status"], "failed")

    def test_runtime_equivalent_escape_cannot_bypass_example_bytes(self):
        old = 'def f():\n    """Old.\n\n    >>> f()\n    \\x31\n    """\n    return 1\n'
        self.prepare(old, old.replace("Old.", "New.").replace("\\x31", "1"))
        self.assertEqual(self.check(self.grant(["f@1"]))["status"], "failed")

    def test_mechanical_pass_is_not_a_factual_correctness_claim(self):
        old = 'def f():\n    """Return one."""\n    return 1\n'
        self.prepare(old, old.replace("Return one.", "Return two."))
        result = self.check(self.grant(["f@1"]))
        self.assertEqual(result["status"], "passed")
        self.assertTrue(any("not comment correctness" in item for item in result["limitations"]))

    def test_nested_async_class_and_module_inventory(self):
        old = '"""Module."""\nclass C:\n    """Class."""\n    async def f(self):\n        """Method."""\n        pass\n'
        self.prepare(old, old.replace("Method.", "New method."))
        self.assertEqual({row["node"] for row in checker.inventory(self.before)["nodes"]},
                         {"<module>@1", "C@2", "C.f@4"})
        self.assertEqual(self.check(self.grant(["C.f@4"]))["status"], "passed")

    def test_concatenation_unsupported_but_other_strings_immutable(self):
        old = 'def f():\n    ("Old " "doc.")\n    return 1\n'
        self.prepare(old, old.replace("Old", "New"))
        self.assertEqual(self.check(self.grant(["f@1"]))["status"], "unsupported")

    def test_non_python_encoding_and_invalid_syntax(self):
        self.prepare(b"# coding: cp1252\n# caf\xe9\n", b"# coding: cp1252\n# caf\xe9\n")
        self.assertEqual(self.check(None)["status"], "unsupported")
        self.prepare("x = (\n", "x = (\n")
        self.assertEqual(self.check(None)["status"], "unsupported")
        self.prepare("x = 1\n", "x = (\n")
        self.assertEqual(self.check(None)["status"], "failed")
        self.before = self.before.with_suffix(".ts")
        self.before.write_bytes(b"const x = 1;\n")
        self.old = self.before.read_bytes()
        self.assertEqual(self.check(None)["status"], "unsupported")

    def test_cli_inventory_and_exact_grant(self):
        old = 'def f():\n    """Old."""\n    pass\n'
        self.prepare(old, old.replace("Old.", "New."))
        permission = Path(self.tmp.name) / "allow.json"
        permission.write_text(json.dumps(self.grant(["f@1"])), encoding="utf-8")
        for extra, expected in (([str(self.after), "--allow", str(permission)], 0),
                                ([str(self.after)], 1), (["--inventory"], 0)):
            result = subprocess.run([sys.executable, str(SCRIPTS / "check_docstrings.py"), str(self.before), *extra], capture_output=True)
            self.assertEqual(result.returncode, expected, result.stderr)
            self.assertIn(json.loads(result.stdout)["status"], {"passed", "failed", "inventory"})


if __name__ == "__main__":
    unittest.main()

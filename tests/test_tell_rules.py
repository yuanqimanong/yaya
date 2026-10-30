"""Malformed rule files must not emit success or escape as a traceback."""
import copy
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_detect_tells import detector, SCRIPTS


class RuleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix=".rules-", dir=SCRIPTS.parents[2])
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "rules.json"
        self.original = json.loads(detector.RULES_PATH.read_text(encoding="utf-8"))

    def test_invalid_rule_contracts_are_rejected(self):
        variants = [
            {**self.original, "format_version": True}, {"format_version": 2, "rules": []},
            {**self.original, "rules": "rules"},
        ]
        for field, value in (("severity", "P3"), ("language", "en-US"), ("id", ""),
                             ("phrases", []), ("phrases", "text"), ("phrases", [""]),
                             ("phrases", ["same", "SAME"]), ("message", None)):
            data = copy.deepcopy(self.original)
            data["rules"][0][field] = value
            variants.append(data)
        data = copy.deepcopy(self.original)
        data["rules"].append(data["rules"][0])
        variants.append(data)
        for index, data in enumerate(variants):
            with self.subTest(case=index):
                self.path.write_text(json.dumps(data), encoding="utf-8")
                with patch.object(detector, "RULES_PATH", self.path), self.assertRaises(ValueError):
                    detector.load_rules()

    def test_invalid_severity_returns_one_error_document(self):
        core = Path(self.tmp.name) / "yaya"
        shutil.copytree(SCRIPTS.parent, core, ignore=shutil.ignore_patterns("__pycache__"))
        self.original["rules"][0]["severity"] = "P3"
        (core / "scripts/tell_rules.json").write_text(json.dumps(self.original), encoding="utf-8")
        run = subprocess.run([sys.executable, "-B", str(core / "scripts/detect_tells.py"),
                              "--language", "en", "--fail-on", "P2"],
                             input="in today's fast-paced world", capture_output=True, text=True, timeout=10)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["status"], "error")
        self.assertNotIn("Traceback", run.stderr)

    def test_shipped_rules_are_usable(self):
        for rule in detector.load_rules():
            text = rule["phrases"][0]
            self.assertTrue(any(row["id"] == rule["id"] for row in detector.detect(text, rule["language"])["findings"]))


if __name__ == "__main__":
    unittest.main()

"""Collector runs the frozen checker and its dependencies in one isolated process."""
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from test_evals import COLLECT

sys.path.insert(0, str(Path(__file__).parent / "evals"))
import compare_runs


class FrozenCheckerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.addCleanup(self.tmp.cleanup)
        self.tests = Path(self.tmp.name)
        self.run = self.tests / "runs/example"
        self.script = self.run / "snapshot/yaya/scripts/check_comments.py"
        self.script.parent.mkdir(parents=True)
        (self.run / "manifest.json").write_text("{}", encoding="utf-8")
        self.case = {"id": "example", "task": "comments", "request": "Polish comments",
                     "input": "x = 1 # old\n", "checks": ["Preserve code"]}
        self.row = {"id": "example", "text": "x = 1 # new\n", "notes": "", "skill_used": False}

    def collect(self):
        with patch.object(COLLECT, "TESTS", self.tests), \
             patch.object(COLLECT, "verify_run", return_value=({}, [self.case])), \
             patch.object(COLLECT, "load_outputs", return_value={"example": self.row}), \
             patch.object(compare_runs, "audit_published_outputs", return_value={}):
            return COLLECT.collect(self.run, self.tests / "results/report")

    def test_collector_loads_sibling_dependency_without_host_module_pollution(self):
        self.script.with_name("frozen_dependency.py").write_text('MARKER = "frozen"\n', encoding="utf-8")
        self.script.write_text(
            'import json\nfrom frozen_dependency import MARKER\n'
            'def check_files(*args):\n    return {"status": "passed", "dependency": MARKER}\n'
            'if __name__ == "__main__":\n    print(json.dumps(check_files()))\n', encoding="utf-8")
        summary = self.collect()
        self.assertEqual(summary["comment_statuses"]["passed"], 2)
        rows = json.loads((self.tests / "results/report/mechanical.json").read_text(encoding="utf-8"))
        self.assertTrue(all(row["comment_boundary"]["dependency"] == "frozen" for row in rows))
        self.assertNotIn("frozen_dependency", sys.modules)
        self.assertFalse(list(self.script.parent.glob("__pycache__/*")))

    def test_mismatched_checker_exit_status_is_rejected(self):
        self.script.write_text(
            'def check_files(*args):\n    return {"status": "passed"}\n'
            'if __name__ == "__main__":\n    print(\'{"status":"passed"}\')\n    raise SystemExit(2)\n', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exit"):
            self.collect()


if __name__ == "__main__":
    unittest.main()

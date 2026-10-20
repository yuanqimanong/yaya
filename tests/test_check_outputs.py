"""Synthetic-only checks for fixed-subset mechanical evaluation support."""
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS / "evals"))
try:
    SPEC = importlib.util.spec_from_file_location("yaya_check_outputs", TESTS / "evals/check_outputs.py")
    CHECK = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(CHECK)
finally:
    sys.path.pop(0)


class ProseOutputChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TESTS)
        Path(self.temp.name).resolve().relative_to(TESTS.resolve())
        self.addCleanup(self.temp.cleanup)
        self.tests_root = Path(self.temp.name)
        self.run = self.tests_root / "runs/synthetic"
        self.destination = self.tests_root / "results/synthetic/prose-mechanical.json"
        self.write(self.run / "snapshot/yaya/SKILL.md", "Synthetic frozen skill.")
        scripts = self.run / "snapshot/yaya/scripts"
        scripts.mkdir()
        for name in ("check_rewrite.py", "prose_scan.py"):
            shutil.copyfile(TESTS.parent / "core/yaya/scripts" / name, scripts / name)
        cases = [
            {"id": identifier, "task": "humanize", "request": "Retain the supplied fact.",
             "input": "Ordinary prose.", "checks": ["Synthetic fixture; not a model evaluation."]}
            for identifier in CHECK.CASE_IDS
        ]
        cases[0]["input"] = "Wait 2 ms."
        cases[1]["input"] = "`unfinished"
        cases.append({"id": "C001", "task": "comments", "request": "Edit the ordinary comment.",
                      "input": "# Keep\nvalue = 1\n", "checks": ["Keep code."]})
        self.write(self.run / "criteria.json", cases)
        for mode in CHECK.CONDITIONS:
            packet = [{key: case[key] for key in ("id", "request", "input")} for case in cases]
            outputs = [{"id": case["id"], "text": case["input"], "notes": "Synthetic only.",
                        "skill_used": mode == "skill"} for case in cases]
            if mode == "skill":
                outputs[0]["text"] = "Wait 3 ms."
            self.write(self.run / mode / "batch-001/requests.json", packet)
            self.write(self.run / mode / "batch-001/outputs.json", outputs)
        snapshot = self.run / "snapshot/yaya"
        manifest = {
            "protocol": 2, "case_ids": [case["id"] for case in cases], "batch_size": len(cases),
            "snapshot_sha256": {path.relative_to(snapshot).as_posix(): self.sha(path)
                                for path in snapshot.rglob("*") if path.is_file()},
            "criteria_sha256": self.sha(self.run / "criteria.json"),
            "request_sha256": {f"{mode}/batch-001/requests.json": self.sha(self.run / mode / "batch-001/requests.json")
                               for mode in CHECK.CONDITIONS},
            "data_sha256": {},
        }
        self.write(self.run / "manifest.json", manifest)

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value if isinstance(value, str) else json.dumps(value), encoding="utf-8")

    def sha(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def run_hashes(self):
        return {path.relative_to(self.run).as_posix(): self.sha(path)
                for path in self.run.rglob("*") if path.is_file()}

    def check(self):
        with patch.object(CHECK, "TESTS", self.tests_root):
            return CHECK.check_outputs(self.run, self.destination)

    def test_records_failures_unsupported_and_sha_without_mutating_inputs(self):
        before = self.run_hashes()
        summary = self.check()
        after = self.run_hashes()
        self.assertEqual(before, after)
        self.assertEqual(summary["conditions"]["skill"], {"passed": 61, "failed": 1, "unsupported": 1, "error": 0})
        self.assertEqual(summary["conditions"]["baseline"], {"passed": 62, "failed": 0, "unsupported": 1, "error": 0})
        report = json.loads(self.destination.read_text(encoding="utf-8"))
        self.assertEqual(len(report["records"]), 126)
        self.assertEqual(report["input_sha256_before"], report["input_sha256_after"])
        self.assertEqual(set(report["selection"]["case_ids"]), set(CHECK.CASE_IDS))
        rows = {(row["id"], row["condition"]): row for row in report["records"]}
        failure = rows["H001", "skill"]
        self.assertEqual(failure["status"], "failed")
        self.assertEqual([item["category"] for item in failure["violations"]], ["numbers"])
        self.assertEqual(failure["before_sha256"], hashlib.sha256(b"Wait 2 ms.").hexdigest())
        self.assertEqual(failure["after_sha256"], hashlib.sha256(b"Wait 3 ms.").hexdigest())
        self.assertEqual(rows["H002", "skill"]["status"], "unsupported")
        self.assertEqual(rows["H002", "skill"]["violations"], [])
        self.assertNotIn(("C001", "skill"), rows)
        original_result = self.destination.read_bytes()
        with self.assertRaisesRegex(ValueError, "overwrite"):
            self.check()
        self.assertEqual(self.destination.read_bytes(), original_result)

    def test_incomplete_other_cases_and_changed_snapshot_rejected_before_output(self):
        path = self.run / "baseline/batch-001/outputs.json"
        original = path.read_bytes()
        rows = json.loads(original)
        self.write(path, [row for row in rows if row["id"] != "C001"])
        with self.assertRaisesRegex(ValueError, "Incomplete"):
            self.check()
        self.assertFalse(self.destination.exists())
        path.write_bytes(original)
        self.write(self.run / "baseline/batch-999/outputs.json", [])
        with self.assertRaisesRegex(ValueError, "output file set"):
            self.check()
        self.assertFalse(self.destination.exists())
        scanner = self.run / "snapshot/yaya/scripts/prose_scan.py"
        scanner.write_bytes(scanner.read_bytes() + b"\n")
        with self.assertRaisesRegex(ValueError, "changed"):
            self.check()
        self.assertFalse(self.destination.exists())


if __name__ == "__main__":
    unittest.main()

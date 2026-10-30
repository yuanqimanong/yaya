"""Actual runtime diagnostics remain usable when optional helper imports fail."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from test_commands import CORE, ROOT, commands


class DoctorTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory(prefix=".doctor-", dir=ROOT)
        self.addCleanup(temp.cleanup)
        self.core = Path(temp.name) / "yaya"
        shutil.copytree(CORE, self.core, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))

    def run_doctor(self, *args):
        return subprocess.run([sys.executable, str(self.core / "scripts/yaya.py"), "doctor", *args],
                              capture_output=True, timeout=10)

    def test_healthy_runtime_is_readonly(self):
        before = {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.core.rglob("*") if p.is_file()}
        run = self.run_doctor("--json")
        self.assertEqual(run.returncode, 0, run.stderr)
        report = json.loads(run.stdout)
        self.assertEqual(report["status"], "ready")
        self.assertTrue(report["read_only"])
        self.assertEqual(before, {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in self.core.rglob("*") if p.is_file()})

    def test_missing_dependency_still_produces_diagnostics(self):
        (self.core / "scripts/packs.py").unlink()
        for flags in ((), ("--json",)):
            run = self.run_doctor(*flags)
            self.assertEqual(run.returncode, 1, run.stderr)
            self.assertNotIn(b"Traceback", run.stderr)
        report = json.loads(self.run_doctor("--json").stdout)
        self.assertIn("packs.py", next(x for x in report["checks"] if x["name"] == "runtime-files")["detail"])

    def test_damaged_catalog_and_broken_guide_are_reported_separately(self):
        (self.core / "catalog.json").write_text("{broken", encoding="utf-8")
        (self.core / "references/validation.md").unlink()
        report = json.loads(self.run_doctor("--json").stdout)
        failed = {row["name"] for row in report["checks"] if row["status"] == "failed"}
        self.assertTrue({"catalog", "guide-links"} <= failed)

    def test_discovery_and_invalid_options_do_not_read_user_files(self):
        self.assertIn("doctor", commands.resolve(["--help"]))
        self.assertIn("只读", commands.resolve(["help", "doctor"]))
        for args in (["doctor", "--file", "user.md"], ["doctor", "--", "payload"], ["doctor", "--json", "--json"]):
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_standalone_diagnostic_rejects_unrelated_arguments(self):
        script = self.core / "scripts/doctor.py"
        for arguments, code in (([], 0), (["--file", "user.md"], 2)):
            process = subprocess.run([sys.executable, str(script), *arguments], capture_output=True, timeout=10)
            self.assertEqual(process.returncode, code, process.stderr)
        self.assertFalse(list(self.core.rglob("*.pyc")))


if __name__ == "__main__":
    unittest.main()

"""Invalid time limits must not start attempts or create evidence."""
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests/evals"))
import run_cli
import judge_cli
import continue_cli
import engineering_compare


class EvaluationTimeouts(unittest.TestCase):
    def test_invalid_limits_fail_before_io_at_every_entry(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "tests") as folder:
            missing = Path(folder) / "never-created"
            job = SimpleNamespace(directory=missing)
            calls = (
                lambda value: run_cli.execute_cli(["never-run"], "", missing, value),
                lambda value: run_cli.run_one(job, ["never-run"], value),
                lambda value: run_cli.run_cli(missing, ["never-run"], ["skill"], timeout=value),
                lambda value: judge_cli.run_one(job, ["never-run"], value),
                lambda value: judge_cli.judge_cli(missing, missing, ["never-run"], timeout=value),
                lambda value: continue_cli.retry_once(job, ["never-run"], value),
                lambda value: continue_cli.continue_run(missing, timeout=value),
                lambda value: engineering_compare.execute(missing, ["never-run"], timeout=value),
            )
            for index, call in enumerate(calls):
                for value in (float("nan"), float("inf"), -float("inf"), 0, -1, True, "1"):
                    with self.subTest(entry=index, value=value):
                        with self.assertRaisesRegex(ValueError, "finite positive"):
                            call(value)
                        self.assertEqual(list(Path(folder).iterdir()), [])

    def test_finite_positive_limits(self):
        for value in (0.001, 1, 180, 1e6):
            self.assertIsNone(run_cli.validate_timeout(value))

    def test_cli_errors_do_not_traceback_or_create_runs(self):
        for name in ("run_cli", "judge_cli", "continue_cli", "engineering_compare"):
            args = ["run"] if name == "engineering_compare" else []
            args += ["never-created"] * (2 if name == "judge_cli" else 1)
            for value in ("nan", "inf", "-inf"):
                with self.subTest(name=name, value=value):
                    result = subprocess.run([sys.executable, "-B", str(ROOT / "tests/evals" / (name + ".py")),
                                             *args, "--timeout=" + value], capture_output=True, text=True)
                    self.assertEqual(result.returncode, 2)
                    self.assertIn("finite positive", result.stderr)
                    self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()

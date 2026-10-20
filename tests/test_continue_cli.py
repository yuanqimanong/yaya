"""Infrastructure continuation tests with synthetic local child processes."""
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import unittest
from unittest.mock import patch

import test_compare_runs as fixtures

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS / "evals"))
try:
    SPEC = importlib.util.spec_from_file_location("yaya_continue_cli", TESTS / "evals/continue_cli.py")
    CONTINUE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(CONTINUE)
finally:
    sys.path.pop(0)


class ContinueCli(unittest.TestCase):
    def setUp(self):
        self.fixture = fixtures.CompareRuns()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.run = self.fixture.source
        self.job_dir = self.run / "skill/batch-001"

    def failed_first(self, memory=True, tools=False):
        attempt = self.job_dir / "cli-attempt-01"
        stderr = attempt / "stderr.txt"
        stderr.write_text("memory allocation of 4096 bytes failed\n" if memory else "Unclassified failure.\n",
                          encoding="utf-8")
        if tools:
            stdout = attempt / "stdout.jsonl"
            stdout.write_text(stdout.read_text() + json.dumps(
                {"type": "item.completed", "item": {"type": "command_execution"}}) + "\n", encoding="utf-8")
        record = json.loads((attempt / "completion.json").read_text())
        record.update({"status": "failed", "returncode": 7, "error": "CLI exited with status 7"})
        record["artifact_sha256"] = {
            name: self.fixture.sha(attempt / name) for name in record["artifact_sha256"]}
        self.fixture.write(attempt / "completion.json", record)
        (self.job_dir / "outputs.json").unlink()
        return (attempt / "completion.json").read_bytes()

    def unstarted(self):
        directory = self.run / "baseline/batch-002"
        attempt = directory / "cli-attempt-01"
        assert attempt.resolve().is_relative_to(self.fixture.root.resolve())
        shutil.rmtree(attempt)
        (directory / "outputs.json").unlink()
        return directory

    def continue_run(self, retry=True):
        with patch.object(CONTINUE, "configured_model", return_value=fixtures.MODEL), patch("builtins.print"):
            return CONTINUE.continue_run(self.run, retry, workers=1)

    def test_preserve_success_retry_once_and_start_unstarted(self):
        first_bytes = self.failed_first()
        pending = self.unstarted()
        metadata = (self.run / "cli-run.json").read_bytes()
        preserved = (self.run / "baseline/batch-001/outputs.json").read_bytes()
        result = self.continue_run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["preserved_successes"], 2)
        self.assertEqual(len(result["outcomes"]), 2)
        self.assertEqual((self.job_dir / "cli-attempt-01/completion.json").read_bytes(), first_bytes)
        self.assertEqual((self.run / "cli-run.json").read_bytes(), metadata)
        self.assertEqual((self.run / "baseline/batch-001/outputs.json").read_bytes(), preserved)
        self.assertTrue((pending / "cli-attempt-01/completion.json").exists())
        _, jobs = CONTINUE.prepare_jobs(self.run, ["skill"], None)
        attempt, _, proof = CONTINUE.successful_attempt(jobs[0], self.run, self.fixture.command)
        self.assertEqual(attempt.name, "cli-attempt-02")
        self.assertEqual(proof["source_kind"], "recovered_after_infrastructure_failure")
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.continue_run()

    def test_retry_requires_explicit_flag_and_preserves_failed_output(self):
        self.failed_first()
        with self.assertRaisesRegex(ValueError, "--retry-infrastructure"):
            self.continue_run(retry=False)
        self.assertFalse((self.run / "continuation-started.json").exists())
        self.assertFalse((self.job_dir / "cli-attempt-02").exists())

    def test_unknown_exit_and_tool_activity_cannot_be_reclassified(self):
        self.failed_first(memory=False)
        with self.assertRaisesRegex(ValueError, "supported infrastructure"):
            self.continue_run()
        attempt = self.job_dir / "cli-attempt-01"
        (attempt / "stderr.txt").write_text("memory allocation of 4096 bytes failed\n", encoding="utf-8")
        stdout = attempt / "stdout.jsonl"
        stdout.write_text(stdout.read_text() + json.dumps(
            {"type": "item.completed", "item": {"type": "command_execution"}}) + "\n", encoding="utf-8")
        record = json.loads((attempt / "completion.json").read_text())
        record["artifact_sha256"] = {name: self.fixture.sha(attempt / name) for name in record["artifact_sha256"]}
        self.fixture.write(attempt / "completion.json", record)
        with self.assertRaisesRegex(ValueError, "Tool activity"):
            self.continue_run()

    def test_invalid_final_schema_blocks_infrastructure_retry(self):
        self.failed_first()
        attempt = self.job_dir / "cli-attempt-01"
        (attempt / "final.json").write_text('{"id":"wrong"}', encoding="utf-8")
        record = json.loads((attempt / "completion.json").read_text())
        record["artifact_sha256"]["final.json"] = self.fixture.sha(attempt / "final.json")
        self.fixture.write(attempt / "completion.json", record)
        with self.assertRaisesRegex(ValueError, "malformed schema"):
            self.continue_run()
        self.assertFalse((self.run / "continuation-started.json").exists())

    def test_second_failure_stops_new_cases_and_forbids_third_attempt(self):
        self.failed_first()
        pending = self.unstarted()
        self.fixture.stub.write_text(
            "import sys\nsys.stdin.read()\nprint('memory allocation of 4096 bytes failed',file=sys.stderr)\nsys.exit(7)\n",
            encoding="utf-8")
        result = self.continue_run()
        self.assertEqual(result["status"], "stopped")
        self.assertEqual([row["status"] for row in result["outcomes"]], ["failed", "not_started"])
        self.assertTrue((self.job_dir / "cli-attempt-02/completion.json").exists())
        self.assertFalse((pending / "cli-attempt-01").exists())
        self.assertFalse((self.job_dir / "outputs.json").exists())
        with self.assertRaisesRegex(ValueError, "already attempted"):
            self.continue_run()

    def test_already_complete_does_not_create_a_new_sample(self):
        result = self.continue_run()
        self.assertEqual(result["status"], "already_complete")
        self.assertEqual(result["new_calls"], 0)
        self.assertFalse((self.run / "continuation-started.json").exists())

    def test_timeout_recovery_retains_the_completed_but_failed_first_call(self):
        self.failed_first(memory=False)
        path = self.job_dir / "cli-attempt-01/completion.json"
        record = json.loads(path.read_text())
        record.update({"error": "timeout", "returncode": None})
        self.fixture.write(path, record)
        original = path.read_bytes()
        result = self.continue_run()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(path.read_bytes(), original)
        self.assertTrue((self.job_dir / "cli-attempt-01/final.json").exists())
        self.assertTrue((self.job_dir / "cli-attempt-02/final.json").exists())

    def test_worker_cap_is_enforced_before_creating_a_journal(self):
        with self.assertRaisesRegex(ValueError, "1 to 3 workers"):
            CONTINUE.continue_run(self.run, True, workers=4)
        self.assertFalse((self.run / "continuation-started.json").exists())


if __name__ == "__main__":
    unittest.main()

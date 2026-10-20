"""Anonymous CLI review protocol checks with a fake process, not model evaluations."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS / "evals"))
try:
    SPEC = importlib.util.spec_from_file_location("yaya_judge_cli", TESTS / "evals/judge_cli.py")
    JUDGE = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = JUDGE
    SPEC.loader.exec_module(JUDGE)
finally:
    sys.path.pop(0)

STUB = r'''
import json
from pathlib import Path
import sys
import time
import subprocess
mode = sys.argv[1]
prompt = sys.stdin.read()
packet = json.loads(prompt.split("Anonymous pairs:\n", 1)[1])
out = Path(sys.argv[sys.argv.index("-o") + 1])
if mode in {"inherited-success", "inherited-timeout"}:
    child = ("import os,sys,time\nfrom pathlib import Path\n"
             "stop=Path(sys.argv[1]); done=Path(sys.argv[2]); deadline=time.monotonic()+4\n"
             "while not stop.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
             "os.close(1); os.close(2); done.touch()\n")
    subprocess.Popen([sys.executable, "-c", child, str(out.with_name("descendant.stop")),
                      str(out.with_name("descendant.done"))], stdout=sys.stdout, stderr=sys.stderr)
if mode in {"known-diagnostic", "unknown-error"}:
    message = ("Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model` is ignored.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model_reasoning_effort` is ignored.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.notify` is ignored.")
    if mode == "unknown-error":
        message = "Unexpected server error."
    print(json.dumps({"type":"item.completed","item":{"type":"error","message":message}}))
if mode == "timeout":
    print(json.dumps({"type":"thread.started","thread_id":"fake"}), flush=True)
    time.sleep(3)
if mode == "exit":
    print("Deliberate review fixture error.", file=sys.stderr)
    sys.exit(9)
candidate = {"fidelity":"pass","task":"pass","quality":"same","evidence":"Source and response both say hello."}
rows = [{"id":row["id"],"A":dict(candidate),"B":dict(candidate),"preference":"tie",
         "reason":"Both preserve the stated greeting."} for row in packet]
if mode == "wrong-id":
    rows[0]["id"] = "unrequested"
if mode == "missing":
    rows.pop()
if mode == "blank-evidence":
    rows[0]["A"]["evidence"] = " "
if mode == "hard-override":
    rows[0]["A"]["fidelity"] = "fail"
    rows[0]["preference"] = "A"
out.write_text("{" if mode == "malformed" else json.dumps({"judgments":rows}), encoding="utf-8")
if mode == "tools":
    print(json.dumps({"type":"item.completed","item":{"type":"web_search"}}))
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":14,"cached_input_tokens":0,"output_tokens":21}}),flush=True)
if mode == "inherited-timeout":
    time.sleep(3)
'''


class JudgeCli(unittest.TestCase):
    def setUp(self):
        (TESTS / "runs").mkdir(exist_ok=True)
        (TESTS / "results").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="judge-unit-", dir=TESTS / "runs")
        self.results_temporary = tempfile.TemporaryDirectory(prefix="judge-unit-", dir=TESTS / "results")
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.results_temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.destination = Path(self.results_temporary.name)
        self.review = self.root / "review"
        self.review.mkdir()
        self.stub = self.root / "stub.py"
        self.stub.write_text(STUB, encoding="utf-8")

    def packet(self, identifier="sample"):
        return [{"id": identifier, "request": "Polish this greeting.", "input": "Hello.",
                 "checks": ["Retain the greeting."], "A": "Hello.", "B": "Hello."}]

    def write_packet(self, number=1, identifier="sample"):
        path = self.review / f"batch-{number:02d}.json"
        path.write_text(json.dumps(self.packet(identifier)), encoding="utf-8")
        return path

    def run_stub(self, mode, resume=False):
        command = [sys.executable, str(self.stub), mode]
        with patch("builtins.print"):
            return JUDGE.judge_cli(self.review, self.destination, command, timeout=5, resume=resume)

    def test_full_run_retains_logs_and_publishes_array_for_summarizer(self):
        self.write_packet()
        self.write_packet(2, "other")
        records = self.run_stub("success")
        self.assertEqual(len(records), 2)
        self.assertTrue(all(record["status"] == "completed" for record in records), records)
        self.assertEqual(records[0]["usage"][0]["input_tokens"], 14)
        final = json.loads((self.destination / "judgments.json").read_text())
        self.assertEqual([row["id"] for row in final], ["sample", "other"])
        self.assertEqual(set(records[0]["artifact_sha256"]), JUDGE.ARTIFACTS)
        self.assertIn("project_doc_max_bytes=0", records[0]["command"])
        self.assertNotIn("--model", records[0]["command"])

    def test_limit_then_resume_isolates_batches_and_only_calls_unfinished(self):
        self.write_packet()
        self.write_packet(2, "other")
        command = [sys.executable, str(self.stub), "success"]
        with patch("builtins.print"):
            records = JUDGE.judge_cli(self.review, self.destination, command, limit=1)
        self.assertEqual(len(records), 1)
        self.assertFalse((self.destination / "judgments.json").exists())
        prompt = (self.review / "cli-judgments/batch-01/attempt-01/prompt.txt").read_text()
        self.assertNotIn('"id": "other"', prompt)
        real_run = JUDGE.subprocess.run
        with patch.object(JUDGE.subprocess, "run", wraps=real_run) as called, patch("builtins.print"):
            records = JUDGE.judge_cli(self.review, self.destination, command, resume=True)
        self.assertEqual(called.call_count, 1)
        self.assertEqual(sum(record.get("resumed", False) for record in records), 1)
        self.assertTrue((self.destination / "judgments.json").exists())

    def test_runner_never_reads_key_skill_notes_or_other_sources(self):
        self.write_packet()
        for name in ("blind-key.json", "SKILL.md", "notes.json"):
            (self.review / name).write_text("SECRET_CONDITION_INFO", encoding="utf-8")
        read = JUDGE.read_json
        accessed = []
        def checked_read(path):
            accessed.append(Path(path).name)
            self.assertNotIn(Path(path).name, {"blind-key.json", "SKILL.md", "notes.json"})
            return read(path)
        with patch.object(JUDGE, "read_json", side_effect=checked_read):
            records = self.run_stub("success")
        self.assertEqual(records[0]["status"], "completed")
        self.assertNotIn("SECRET_CONDITION_INFO",
                         (self.review / "cli-judgments/batch-01/attempt-01/prompt.txt").read_text())
        self.assertIn("batch-01.json", accessed)

    def test_nonblind_or_duplicate_packets_rejected_before_process(self):
        path = self.write_packet()
        for field in ("notes", "condition", "skill_used"):
            packet = self.packet()
            packet[0][field] = "SECRET"
            path.write_text(json.dumps(packet), encoding="utf-8")
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "non-blind"):
                JUDGE.prepare_jobs(self.review)
        self.write_packet()
        self.write_packet(2)
        with self.assertRaisesRegex(ValueError, "across review"):
            JUDGE.prepare_jobs(self.review)

    def test_batch_size_limit_and_duplicate_output_ids(self):
        packet = [self.packet(str(index))[0] for index in range(13)]
        with self.assertRaisesRegex(ValueError, "1 to 12"):
            JUDGE.valid_packet(packet)
        candidate = {"fidelity": "pass", "task": "pass", "quality": "same", "evidence": "Greeting preserved."}
        row = {"id": "sample", "A": candidate, "B": candidate, "preference": "tie", "reason": "Same."}
        with self.assertRaisesRegex(ValueError, "duplicate"):
            JUDGE.validate_judgments({"judgments": [row, row]}, ("sample", "other"))

    def test_first_failures_remain_and_never_publish_partial_judgments(self):
        for mode in ("exit", "wrong-id", "missing", "blank-evidence", "hard-override", "malformed", "tools", "unknown-error"):
            with self.subTest(mode=mode):
                review = self.root / mode
                review.mkdir()
                (review / "batch-01.json").write_text(json.dumps(self.packet()), encoding="utf-8")
                job = JUDGE.prepare_jobs(review)[0]
                result = JUDGE.run_one(job, [sys.executable, str(self.stub), mode], 5)
                self.assertEqual(result["status"], "failed")
                evidence = job.directory / "attempt-01/completion.json"
                first = evidence.read_bytes()
                with self.assertRaisesRegex(ValueError, "failed or incompatible"):
                    JUDGE.run_one(job, ["missing-executable"], 5, resume=True)
                self.assertEqual(evidence.read_bytes(), first)
                if mode == "exit":
                    self.assertEqual(result["returncode"], 9)
        self.assertFalse((self.destination / "judgments.json").exists())

    def test_timeout_preserves_record(self):
        self.write_packet()
        job = JUDGE.prepare_jobs(self.review)[0]
        result = JUDGE.run_one(job, [sys.executable, str(self.stub), "timeout"], 0.3)
        self.assertEqual(result["error"], "timeout")
        self.assertEqual(result["status"], "failed")
        self.assertTrue((job.directory / "attempt-01/stdout.jsonl").exists())

    def test_successful_resume_verifies_all_artifacts_and_aggregate(self):
        self.write_packet()
        self.run_stub("success")
        with patch.object(JUDGE.subprocess, "run", side_effect=AssertionError("must not call model")):
            records = self.run_stub("success", resume=True)
        self.assertTrue(records[0]["resumed"])
        final = self.destination / "judgments.json"
        before = final.read_bytes()
        final.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "refusing overwrite"):
            self.run_stub("success", resume=True)
        self.assertEqual(final.read_text(), "[]")
        final.write_bytes(before)
        log = self.review / "cli-judgments/batch-01/attempt-01/stderr.txt"
        log.write_text("altered", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "artifact changed"):
            self.run_stub("success", resume=True)

    def test_changed_input_refuses_resume_before_model(self):
        path = self.write_packet()
        self.run_stub("success")
        path.write_text(json.dumps(self.packet("changed")), encoding="utf-8")
        with patch.object(JUDGE.subprocess, "run", side_effect=AssertionError("must not call model")):
            with self.assertRaisesRegex(ValueError, "different inputs"):
                self.run_stub("success", resume=True)

    def test_existing_judgments_are_never_overwritten(self):
        self.write_packet()
        path = self.destination / "judgments.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already exists"):
            self.run_stub("success")
        self.assertEqual(path.read_text(), "[]")

    def test_known_cli_diagnostic_is_preserved_in_successful_review(self):
        self.write_packet()
        records = self.run_stub("known-diagnostic")
        self.assertEqual(records[0]["status"], "completed")
        self.assertEqual(records[0]["tool_or_unknown_items"], [])
        self.assertEqual(len(records[0]["diagnostics"]), 1)
        resumed = self.run_stub("known-diagnostic", resume=True)
        self.assertEqual(resumed[0]["diagnostics"], records[0]["diagnostics"])

    def test_inherited_output_handles_do_not_delay_review_or_timeout(self):
        for mode in ("inherited-success", "inherited-timeout"):
            with self.subTest(mode=mode):
                review = self.root / mode
                review.mkdir()
                (review / "batch-01.json").write_text(json.dumps(self.packet()), encoding="utf-8")
                job = JUDGE.prepare_jobs(review)[0]
                attempt = job.directory / "attempt-01"
                try:
                    started = time.monotonic()
                    result = JUDGE.run_one(job, [sys.executable, str(self.stub), mode],
                                          0.5 if mode.endswith("timeout") else 5)
                    self.assertLess(time.monotonic() - started, 2)
                    self.assertFalse((attempt / "descendant.done").exists())
                    if mode.endswith("timeout"):
                        self.assertEqual(result["status"], "failed")
                        self.assertEqual(result["error"], "timeout")
                        self.assertIsNone(result["returncode"])
                        self.assertEqual(result["completed_turns"], 1)
                    else:
                        self.assertEqual(result["status"], "completed")
                        self.assertEqual(result["returncode"], 0)
                finally:
                    (attempt / "descendant.stop").touch()
                    deadline = time.monotonic() + 5
                    while not (attempt / "descendant.done").exists() and time.monotonic() < deadline:
                        time.sleep(0.01)

    def test_review_failure_stops_starting_queued_batches(self):
        self.write_packet()
        self.write_packet(2, "other")
        with patch("builtins.print"):
            records = JUDGE.judge_cli(self.review, self.destination,
                                      [sys.executable, str(self.stub), "exit"], workers=1)
        self.assertEqual([record["status"] for record in records], ["failed", "not_started"])
        self.assertFalse((self.review / "cli-judgments/batch-02").exists())
        self.assertFalse((self.destination / "judgments.json").exists())


if __name__ == "__main__":
    unittest.main()

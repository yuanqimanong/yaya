"""Reuse provenance and archive checks; generated responses are synthetic fixtures."""
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
    import continue_cli as CONTINUE
    SPEC = importlib.util.spec_from_file_location("yaya_compare_runs", TESTS / "evals/compare_runs.py")
    COMPARE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(COMPARE)
finally:
    sys.path.pop(0)

MODEL = {"configured": {"model": "synthetic-test-model", "model_provider": "fixture",
                        "model_reasoning_effort": "high"}, "exact_model_revision": "fixture"}
STUB = r'''
import json
from pathlib import Path
import sys
prompt = sys.stdin.read()
packet = json.loads(prompt.split("User request and input:\n",1)[1])
value = {"id":packet["id"],"text":packet["input"],"notes":"","skill_used":"Use the supplied Yaya guidance" in prompt}
Path(sys.argv[sys.argv.index("-o")+1]).write_text(json.dumps(value),encoding="utf-8")
print(json.dumps({"type":"turn.completed","usage":{"input_tokens":1,"output_tokens":1}}))
'''


class CompareRuns(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="reuse-unit-", dir=TESTS / "runs")
        self.results_temp = tempfile.TemporaryDirectory(prefix="reuse-unit-", dir=TESTS / "results")
        self.addCleanup(self.temporary.cleanup)
        self.addCleanup(self.results_temp.cleanup)
        self.root, self.results = Path(self.temporary.name), Path(self.results_temp.name)
        self.stub = self.root / "stub.py"
        self.stub.write_text(STUB, encoding="utf-8")
        self.command = [sys.executable, str(self.stub)]
        self.cases = [{"id": name, "request": "Humanize this.", "input": "Hello.",
                       "task": "humanize", "language": "en", "checks": ["Keep the greeting."],
                       "group": "clear", "suite": "humanize"} for name in ("first", "second")]
        self.source = self.freeze("source", self.cases)
        self.target = self.freeze("target", [self.cases[1]])
        self.competitors = self.root / "competitors"
        pack = self.competitors / "humanizer"
        pack.mkdir(parents=True)
        (pack / "SKILL.md").write_text("Synthetic competitor guidance.", encoding="utf-8")
        (pack / "LICENSE").write_text("Synthetic fixture license.", encoding="utf-8")
        self.write(pack / "source.json", {"commit": "a" * 40, "files": [
            {"path": name, "sha256": self.sha(pack / name)} for name in ("SKILL.md", "LICENSE")]})
        with patch.object(COMPARE.run_cli, "configured_model", return_value=MODEL), patch("builtins.print"):
            COMPARE.run_cli.run_cli(self.source, self.command, ["skill", "baseline"], workers=2)
            COMPARE.run_cli.run_cli(self.target, self.command, ["baseline"], workers=1, competitors=self.competitors)

    def sha(self, path):
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def freeze(self, name, cases):
        run = self.root / name
        files = {
            "snapshot/yaya/SKILL.md": "Synthetic Yaya fixture.",
            "snapshot/yaya/references/humanize.md": "Synthetic humanize fixture.",
            "snapshot/yaya/languages/en/GUIDE.md": "Synthetic English GUIDE.",
            "snapshot/yaya/languages/en/PATTERNS.md": "Synthetic English PATTERNS.",
            "data/language-packs/zh-Hant/GUIDE.md": "Synthetic Traditional GUIDE.",
        }
        for filename, text in files.items():
            path = run / filename
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        self.write(run / "criteria.json", cases)
        for condition in ("skill", "baseline"):
            for index, case in enumerate(cases, 1):
                self.write(run / condition / f"batch-{index:03d}/requests.json",
                           [{field: case[field] for field in ("id", "request", "input")}])
        manifest = {
            "protocol": 2, "batch_size": 1, "case_ids": [case["id"] for case in cases],
            "snapshot_sha256": {p.relative_to(run / "snapshot/yaya").as_posix(): self.sha(p)
                                for p in (run / "snapshot/yaya").rglob("*") if p.is_file()},
            "data_sha256": {p.relative_to(run).as_posix(): self.sha(p) for p in (run / "data").rglob("*") if p.is_file()},
            "request_sha256": {p.relative_to(run).as_posix(): self.sha(p) for p in run.glob("*/batch-*/requests.json")},
            "criteria_sha256": self.sha(run / "criteria.json"),
        }
        self.write(run / "manifest.json", manifest)
        return run

    def recover(self, run, job):
        attempt = run / job / "cli-attempt-01"
        (attempt / "stderr.txt").write_text("memory allocation of 4096 bytes failed\n", encoding="utf-8")
        completion = json.loads((attempt / "completion.json").read_text())
        completion.update({"status": "failed", "returncode": 7, "error": "CLI exited with status 7"})
        completion["artifact_sha256"] = {
            name: self.sha(attempt / name) for name in completion["artifact_sha256"]}
        self.write(attempt / "completion.json", completion)
        (run / job / "outputs.json").unlink()
        prior = {path.name: path.read_bytes() for path in attempt.iterdir()}
        with patch.object(CONTINUE, "configured_model", return_value=MODEL), patch("builtins.print"):
            result = CONTINUE.continue_run(
                run, True, workers=1, competitors=self.competitors if run == self.target else None)
        self.assertEqual(result["status"], "completed")
        self.assertEqual({path.name: path.read_bytes() for path in attempt.iterdir()}, prior)
        return prior

    def test_first_outputs_reuse_by_id_and_keep_separate_provenance(self):
        target_metadata = (self.target / "cli-run.json").read_bytes()
        result = COMPARE.reuse_skill(self.source, self.target)
        self.assertEqual(result["reused_cases"], 1)
        self.assertEqual((self.source / "skill/batch-002/outputs.json").read_bytes(),
                         (self.target / "skill/batch-001/outputs.json").read_bytes())
        self.assertFalse((self.target / "skill/batch-001/cli-attempt-01").exists())
        self.assertEqual((self.target / "cli-run.json").read_bytes(), target_metadata)
        provenance = json.loads((self.target / "reuse-provenance.json").read_text())
        self.assertEqual(provenance["cases"][0]["id"], "second")
        self.assertIn("batch-002", provenance["cases"][0]["source_attempt"])
        archived = self.target / "reused-skill/batch-001/cli-attempt-01"
        self.assertEqual((archived / "stdout.jsonl").read_bytes(),
                         (self.source / "skill/batch-002/cli-attempt-01/stdout.jsonl").read_bytes())
        with self.assertRaisesRegex(ValueError, "already has a reuse"):
            COMPARE.reuse_skill(self.source, self.target)

    def test_model_or_actual_command_mismatch_is_rejected_without_writes(self):
        path = self.target / "cli-run.json"
        value = json.loads(path.read_text())
        value["model"]["configured"]["model_reasoning_effort"] = "low"
        self.write(path, value)
        with self.assertRaisesRegex(ValueError, "setting differs: model"):
            COMPARE.reuse_skill(self.source, self.target)
        self.assertFalse((self.target / "reuse-started.json").exists())
        value["model"]["configured"]["model_reasoning_effort"] = "high"
        self.write(path, value)
        started = self.target / "baseline/batch-001/cli-attempt-01/started.json"
        original = json.loads(started.read_text())
        original["command"].append("--model=another")
        self.write(started, original)
        with self.assertRaisesRegex(ValueError, "actual CLI command differs"):
            COMPARE.reuse_skill(self.source, self.target)

    def test_full_case_change_is_rejected_even_when_requests_match(self):
        criteria = self.target / "criteria.json"
        cases = json.loads(criteria.read_text())
        cases[0]["checks"].append("New criterion not used by the source.")
        self.write(criteria, cases)
        manifest = json.loads((self.target / "manifest.json").read_text())
        manifest["criteria_sha256"] = self.sha(criteria)
        self.write(self.target / "manifest.json", manifest)
        metadata = json.loads((self.target / "cli-run.json").read_text())
        metadata["manifest_sha256"] = self.sha(self.target / "manifest.json")
        self.write(self.target / "cli-run.json", metadata)
        with self.assertRaisesRegex(ValueError, "Full frozen case differs"):
            COMPARE.reuse_skill(self.source, self.target)
        self.assertFalse((self.target / "skill/batch-001/outputs.json").exists())

    def test_changed_snapshot_is_rejected_even_if_refrozen(self):
        path = self.target / "snapshot/yaya/SKILL.md"
        path.write_text("A different Skill.", encoding="utf-8")
        manifest = json.loads((self.target / "manifest.json").read_text())
        manifest["snapshot_sha256"]["SKILL.md"] = self.sha(path)
        self.write(self.target / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "snapshot_sha256"):
            COMPARE.reuse_skill(self.source, self.target)

    def test_failed_or_tampered_first_attempt_cannot_be_reused(self):
        completion = self.source / "skill/batch-002/cli-attempt-01/completion.json"
        record = json.loads(completion.read_text())
        record["status"] = "failed"
        self.write(completion, record)
        with self.assertRaisesRegex(ValueError, "supported infrastructure"):
            COMPARE.reuse_skill(self.source, self.target)
        record["status"] = "completed"
        self.write(completion, record)
        output = self.source / "skill/batch-002/outputs.json"
        rows = json.loads(output.read_text())
        rows[0]["text"] = "A cherry-picked replacement."
        self.write(output, rows)
        with self.assertRaisesRegex(ValueError, "differs"):
            COMPARE.reuse_skill(self.source, self.target)

    def test_existing_target_outputs_are_preserved(self):
        output = self.target / "skill/batch-001/outputs.json"
        output.write_text("Existing work.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "already contains"):
            COMPARE.reuse_skill(self.source, self.target)
        self.assertEqual(output.read_text(), "Existing work.")

    def test_source_log_change_during_capture_refuses_reuse(self):
        original = COMPARE.ordinary_bytes
        def changing(path, root):
            if path.name == "stdout.jsonl" and root == self.source:
                path.write_bytes(path.read_bytes() + b"\n")
            return original(path, root)
        with patch.object(COMPARE, "ordinary_bytes", side_effect=changing):
            with self.assertRaisesRegex(ValueError, "changed while capturing"):
                COMPARE.reuse_skill(self.source, self.target)
        self.assertFalse((self.target / "reuse-started.json").exists())

    def test_archive_includes_raw_logs_reuse_and_inputs_without_unrelated_files(self):
        COMPARE.reuse_skill(self.source, self.target)
        shutil.copyfile(self.target / "manifest.json", self.results / "manifest.json")
        (self.target / "auth.json").write_text("NOT_AN_EVALUATION_ARTIFACT", encoding="utf-8")
        (self.target / "reused-skill/auth.json").write_text("NOT_AN_EVALUATION_ARTIFACT", encoding="utf-8")
        result = COMPARE.archive_evidence(self.target, self.results)
        archive = Path(result["archive"])
        self.assertTrue((archive / "baseline/batch-001/cli-attempt-01/stdout.jsonl").exists())
        self.assertTrue((archive / "reuse-provenance.json").exists())
        self.assertTrue((archive / "snapshot/yaya/SKILL.md").exists())
        self.assertFalse((archive / "auth.json").exists())
        self.assertFalse((archive / "reused-skill/auth.json").exists())
        listing = json.loads((archive / "archive.json").read_text())
        self.assertEqual(listing["files"]["reuse-provenance.json"]["sha256"],
                         self.sha(self.target / "reuse-provenance.json"))
        with self.assertRaisesRegex(ValueError, "already exists"):
            COMPARE.archive_evidence(self.target, self.results)

    def test_archive_retains_failed_first_attempt_record(self):
        completion = self.target / "baseline/batch-001/cli-attempt-01/completion.json"
        record = json.loads(completion.read_text())
        record["status"] = "failed"
        record["error"] = "Synthetic failed attempt."
        self.write(completion, record)
        result = COMPARE.archive_evidence(self.target, self.results)
        saved = json.loads((Path(result["archive"]) / "baseline/batch-001/cli-attempt-01/completion.json").read_text())
        self.assertEqual(saved["status"], "failed")
        self.assertEqual(saved["error"], "Synthetic failed attempt.")

    def test_recovery_reuse_and_archive_keep_both_attempts_and_journals(self):
        prior = self.recover(self.source, "skill/batch-002")
        target_prior = self.recover(self.target, "baseline/batch-001")
        result = COMPARE.reuse_skill(self.source, self.target)
        self.assertEqual(result["new_model_calls"], 0)
        provenance = json.loads((self.target / "reuse-provenance.json").read_text())
        case = provenance["cases"][0]
        self.assertEqual(case["source_kind"], "recovered_after_infrastructure_failure")
        self.assertTrue(case["source_attempt"].endswith("cli-attempt-02"))
        self.assertEqual(set(case["attempt_sha256"]), {"cli-attempt-01", "cli-attempt-02"})
        for name, content in prior.items():
            self.assertEqual((self.target / "reused-skill/batch-001/cli-attempt-01" / name).read_bytes(), content)
        archived = Path(COMPARE.archive_evidence(self.target, self.results)["archive"])
        for name in ("continuation-started.json", "continuation.json"):
            self.assertEqual((archived / name).read_bytes(), (self.target / name).read_bytes())
            self.assertEqual((archived / "reused-skill" / ("source-" + name)).read_bytes(),
                             (self.source / name).read_bytes())
        for name, content in target_prior.items():
            self.assertEqual((archived / "baseline/batch-001/cli-attempt-01" / name).read_bytes(), content)
        for relative in ("baseline/batch-001", "reused-skill/batch-001"):
            self.assertTrue((archived / relative / "cli-attempt-02/stdout.jsonl").is_file())
        self.assertFalse((self.target / "skill/batch-001/cli-attempt-02").exists())

    def test_recovery_reuse_rejects_changed_failure_or_continuation_proof(self):
        self.recover(self.source, "skill/batch-002")
        failed = self.source / "skill/batch-002/cli-attempt-01/stderr.txt"
        original = failed.read_bytes()
        failed.write_bytes(original + b"changed\n")
        with self.assertRaisesRegex(ValueError, "evidence changed"):
            COMPARE.reuse_skill(self.source, self.target)
        failed.write_bytes(original)
        finished = self.source / "continuation.json"
        value = json.loads(finished.read_text())
        value["plan_sha256"] = "0" * 64
        self.write(finished, value)
        with self.assertRaisesRegex(ValueError, "continuation provenance"):
            COMPARE.reuse_skill(self.source, self.target)
        self.assertFalse((self.target / "reuse-started.json").exists())

    def test_successful_first_attempt_cannot_select_a_second_output(self):
        (self.source / "skill/batch-002/cli-attempt-02").mkdir()
        with self.assertRaisesRegex(ValueError, "must not have a second"):
            COMPARE.reuse_skill(self.source, self.target)
        self.assertFalse((self.target / "reuse-started.json").exists())

    def test_collection_audit_verifies_direct_outputs_and_counts_recovery(self):
        self.recover(self.source, "skill/batch-002")
        result = COMPARE.audit_published_outputs(self.source, self.cases)
        self.assertEqual(result["local_successful_outputs"], 4)
        self.assertEqual(result["local_first_attempt_failures"], 1)
        self.assertEqual(result["local_process_calls"], 5)
        output = self.source / "skill/batch-001/outputs.json"
        rows = json.loads(output.read_text())
        rows[0]["text"] = "Altered after the CLI finished."
        self.write(output, rows)
        with self.assertRaisesRegex(ValueError, "Published output differs"):
            COMPARE.audit_published_outputs(self.source, self.cases)

    def test_collection_audit_verifies_reused_outputs_and_rejects_redirects(self):
        COMPARE.reuse_skill(self.source, self.target)
        result = COMPARE.audit_published_outputs(self.target, [self.cases[1]])
        self.assertEqual(result["local_process_calls"], 1)
        self.assertEqual(result["reused_outputs"], 1)
        provenance_path = self.target / "reuse-provenance.json"
        provenance = json.loads(provenance_path.read_text())
        provenance["cases"][0]["target_output"] = "baseline/batch-001/outputs.json"
        self.write(provenance_path, provenance)
        with self.assertRaisesRegex(ValueError, "Reused case differs"):
            COMPARE.audit_published_outputs(self.target, [self.cases[1]])
        provenance["cases"][0]["target_output"] = "skill/batch-001/outputs.json"
        self.write(provenance_path, provenance)
        path = self.target / "skill/batch-001/outputs.json"
        rows = json.loads(path.read_text())
        rows[0]["text"] = "Altered reused result."
        self.write(path, rows)
        with self.assertRaisesRegex(ValueError, "reused output differs"):
            COMPARE.audit_published_outputs(self.target, [self.cases[1]])


if __name__ == "__main__":
    unittest.main()

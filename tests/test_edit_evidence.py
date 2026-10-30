"""Snapshot, status accounting, freshness, and failure lifecycle constraints."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "core/yaya/scripts"
sys.path.insert(0, str(SCRIPTS))
import edit_evidence as evidence


class EvidenceChecks(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parent)
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "project"
        self.root.mkdir()
        self.snapshot = Path(self.tmp.name) / "snapshot"
        self.source = self.root / "sample.py"
        self.source.write_bytes(b"x = 1 # old\r\n")

    def start(self, targets=("sample.py:comments",)):
        return evidence.start(self.root, self.snapshot, targets)

    def test_task_start_is_worktree_not_git_head_and_preserves_dirty_work(self):
        for command in (["git", "init", str(self.root)], ["git", "-C", str(self.root), "add", "."],
                        ["git", "-C", str(self.root), "-c", "user.name=Test", "-c", "user.email=test@example.invalid", "commit", "-m", "baseline"]):
            subprocess.run(command, capture_output=True, check=True)
        self.source.write_bytes(b"x = 7 # existing edit\r\n")
        manifest = self.start()
        self.assertTrue(manifest["git_baseline"]["head"])
        self.assertIn("sample.py", manifest["git_baseline"]["status"])
        self.assertIn(b"x = 7", (self.snapshot / "before/sample.py").read_bytes())
        self.source.write_bytes(b"x = 7 # rewritten\r\n")
        row = evidence.record(self.snapshot, "sample.py:comments")
        self.assertEqual(row["result"]["status"], "passed")
        self.assertEqual(evidence.summarize(self.snapshot)["counts"]["passed"], 1)
        self.assertIn(b"x = 7", self.source.read_bytes())

    def test_snapshot_still_works_without_git(self):
        with patch.object(evidence.subprocess, "run", side_effect=FileNotFoundError("git missing")) as run:
            manifest = self.start()
        self.assertEqual(run.call_count, 1)
        self.assertIsNone(manifest["git_baseline"]["head"])
        self.assertTrue(manifest["git_baseline"]["error"])
        self.assertEqual((self.snapshot / "before/sample.py").read_bytes(), self.source.read_bytes())
        self.assertFalse((self.snapshot / "git-unstaged.patch").exists())

    def test_slow_git_is_bounded_and_snapshot_reports_missing_metadata(self):
        with patch.object(evidence.subprocess, "run", side_effect=subprocess.TimeoutExpired("git", 10)) as run:
            manifest = self.start()
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.kwargs["timeout"], 10)
        self.assertIn("TimeoutExpired", manifest["git_baseline"]["error"])
        self.assertEqual(manifest["files"]["sample.py"]["sha256"], evidence.digest(self.source.read_bytes()))

    def test_unexecuted_stale_pass_and_tool_change_never_pass(self):
        self.start()
        self.assertEqual(evidence.summarize(self.snapshot)["counts"]["unverified"], 1)
        self.source.write_bytes(b"x = 1 # new\r\n")
        row = evidence.record(self.snapshot, "sample.py:comments")
        self.assertTrue(row["result"]["evidence"]["inputs_stable"])
        self.assertEqual(evidence.summarize(self.snapshot)["counts"]["passed"], 1)
        with patch.object(evidence, "tool_identity", return_value={"name": "changed"}):
            self.assertEqual(evidence.summarize(self.snapshot)["counts"]["unverified"], 1)
        self.source.write_bytes(b"x = 1 # newer\r\n")
        self.assertEqual(evidence.summarize(self.snapshot)["counts"]["unverified"], 1)

    def test_failed_and_unsupported_separate_from_passed(self):
        (self.root / "sample.ts").write_bytes(b"// old\n")
        self.start(("sample.py:comments", "sample.ts:comments", "sample.py:manual"))
        self.source.write_bytes(b"x = 2 # new\r\n")
        self.assertEqual(evidence.record(self.snapshot, "sample.py:comments")["result"]["status"], "failed")
        self.assertEqual(evidence.record(self.snapshot, "sample.ts:comments")["result"]["status"], "unsupported")
        evidence.record(self.snapshot, "sample.py:manual", disposition="accepted", note="Manual scope review; example changed intentionally.")
        summary = evidence.summarize(self.snapshot)
        self.assertEqual(summary["counts"], {"passed": 0, "failed": 1, "unsupported": 1, "manual_review": 1, "unverified": 0})
        self.assertFalse(summary["complete"])
        self.assertEqual(len(summary["open_failures"]), 1)

    def test_failure_requires_repair_or_bound_explicit_exclusion(self):
        self.start()
        self.source.write_bytes(b"x = 2 # bad\r\n")
        evidence.record(self.snapshot, "sample.py:comments")
        evidence.record(self.snapshot, "sample.py:comments", disposition="accepted", note="Manual review alone cannot close a failed check.")
        self.assertEqual(len(evidence.summarize(self.snapshot)["open_failures"]), 1)
        evidence.record(self.snapshot, "sample.py:comments", disposition="excluded", note="Candidate withdrawn from delivery; tracked separately by reviewer.")
        summary = evidence.summarize(self.snapshot)
        self.assertEqual(summary["open_failures"], [])
        self.assertEqual(summary["counts"]["manual_review"], 1)
        self.assertFalse(summary["complete"])
        self.source.write_bytes(b"x = 1 # repaired\r\n")
        evidence.record(self.snapshot, "sample.py:comments")
        summary = evidence.summarize(self.snapshot)
        self.assertTrue(summary["complete"])
        self.assertEqual(summary["targets"][0]["history"], 4)

    def test_snapshot_tampering_path_escape_and_unauthorized_target_rejected(self):
        for name in ("../escape.py:comments", "D:/outside.py:comments", "sample.py:all"):
            with self.subTest(name=name), self.assertRaises(ValueError):
                self.start((name,))
        self.start()
        with self.assertRaises(ValueError):
            evidence.record(self.snapshot, "other.py:comments")
        with self.assertRaises(ValueError):
            evidence.record(self.snapshot, "sample.py:comments", grant={"all": True})
        (self.snapshot / "before/sample.py").write_bytes(b"tampered")
        with self.assertRaisesRegex(ValueError, "snapshot changed"):
            evidence.summarize(self.snapshot)

    def test_read_race_fails_and_utf8_bom_crlf_reported(self):
        self.source.write_bytes(b"\xef\xbb\xbf# old\r\n")
        candidate = self.root / "after.py"
        candidate.write_bytes(b"\xef\xbb\xbf# new\r\n")
        def operation():
            candidate.write_bytes(b"# changed after validation\n")
            return {"status": "passed"}
        row = evidence.bound_check(self.source, candidate, SCRIPTS / "check_comments.py", operation)
        self.assertEqual(row["status"], "failed")
        self.assertFalse(row["evidence"]["inputs_stable"])
        self.assertEqual(row["evidence"]["before"]["encoding"], "utf-8-bom")
        self.assertEqual(row["evidence"]["before"]["crlf"], 1)

    def test_json_duplicate_keys_rejected_and_cli_returns_incomplete(self):
        duplicate = self.root / "bad.json"
        duplicate.write_bytes(b'{"schema": 1, "schema": 2}')
        with self.assertRaises(ValueError):
            evidence.strict_json(duplicate)
        self.start()
        process = subprocess.run([sys.executable, str(SCRIPTS / "edit_evidence.py"), "summary", str(self.snapshot)], capture_output=True)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads(process.stdout)["counts"]["unverified"], 1)

    def test_bound_check_rejects_oversized_input_before_operation(self):
        from check_rewrite import check_files
        from prose_scan import MAX_BYTES
        self.source.write_bytes(b"x" * (MAX_BYTES + 1))
        with patch("check_rewrite.compare") as operation:
            with self.assertRaisesRegex(ValueError, "exceeds"):
                check_files(self.source, self.source)
        operation.assert_not_called()

    def test_bounded_evidence_avoids_unlimited_path_reads(self):
        from check_rewrite import check_files
        original = Path.read_bytes
        def guarded(path):
            if path == self.source:
                self.fail("Prose evidence must use a bounded read")
            return original(path)
        with patch.object(Path, "read_bytes", guarded):
            result = check_files(self.source, self.source)
        self.assertEqual(result["status"], "passed")
        self.assertEqual(result["evidence"]["before"]["bytes"], self.source.stat().st_size)

    def test_bounded_evidence_detects_file_growth(self):
        self.source.write_bytes(b"a" * 16)
        def operation():
            self.source.write_bytes(b"b" * 17)
            return {"status": "passed"}
        row = evidence.bound_check(self.source, self.source, SCRIPTS / "check_comments.py",
                                   operation, max_bytes=16)
        self.assertEqual(row["status"], "failed")
        self.assertFalse(row["evidence"]["inputs_stable"])


if __name__ == "__main__":
    unittest.main()

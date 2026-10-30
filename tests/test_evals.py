"""Integrity controls for evaluation evidence; synthetic outputs are not model tests."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

TESTS = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("yaya_eval_collect", TESTS / "evals/collect.py")
COLLECT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECT)
sys.path.insert(0, str(TESTS / "evals"))
try:
    SPEC = importlib.util.spec_from_file_location("yaya_eval_prepare", TESTS / "evals/prepare.py")
    PREPARE = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(PREPARE)
finally:
    sys.path.pop(0)


class EvaluationIntegrity(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(dir=TESTS)
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.output = self.root / "baseline/batch-01/outputs.json"
        self.output.parent.mkdir(parents=True)
        self.row = {"id": "sample", "text": "Synthetic output.", "notes": "", "skill_used": False}
        self.write(self.output.with_name("requests.json"), [{"id": "sample"}])

    def write(self, path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")

    def test_reject_duplicate_json_keys(self):
        self.output.write_text('{"id":"first","id":"second"}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Duplicate JSON key"):
            COLLECT.read_json(self.output)

    def test_complete_output_is_required(self):
        for rows in ([], [self.row, self.row], [{**self.row, "id": "unknown"}]):
            with self.subTest(rows=rows):
                self.write(self.output, rows)
                with self.assertRaises(ValueError):
                    COLLECT.load_outputs(self.root, "baseline", {"sample"})
        self.write(self.output, [self.row])
        self.assertEqual(COLLECT.load_outputs(self.root, "baseline", {"sample"}), {"sample": self.row})

    def test_extra_or_missing_packet_files_cannot_disappear(self):
        self.write(self.output, [self.row])
        extra = self.root / "baseline/batch-99/outputs.json"
        self.write(extra, [])
        with self.assertRaisesRegex(ValueError, "file set"):
            COLLECT.load_outputs(self.root, "baseline", {"sample"})
        extra.unlink()
        self.write(extra.with_name("requests.json"), [{"id": "extra"}])
        with self.assertRaisesRegex(ValueError, "file set"):
            COLLECT.load_outputs(self.root, "baseline", {"sample"})
        extra.with_name("requests.json").unlink()
        self.output.with_name("requests.json").unlink()
        with self.assertRaisesRegex(ValueError, "file set"):
            COLLECT.load_outputs(self.root, "baseline", {"sample"})

    def test_request_packets_require_unique_nonempty_ids(self):
        self.write(self.output, [self.row])
        for packet in ([], [{"id": "sample"}] * 2, {}, [None], [{"id": 1}]):
            self.write(self.output.with_name("requests.json"), packet)
            with self.subTest(packet=packet), self.assertRaises(ValueError):
                COLLECT.load_outputs(self.root, "baseline", {"sample"})

    def test_reject_empty_malformed_or_contaminated_outputs(self):
        for row in (None, {}, {**self.row, "text": " \n"}, {**self.row, "text": 42},
                    {**self.row, "skill_used": 0}, {**self.row, "skill_used": True},
                    {**self.row, "notes": []}, {**self.row, "score": "pass"}):
            with self.subTest(row=row):
                self.write(self.output, [row])
                with self.assertRaises(ValueError):
                    COLLECT.load_outputs(self.root, "baseline", {"sample"})

    def frozen_run(self):
        case = {"id": "sample", "request": "Polish this.", "input": "Original.",
                "task": "text", "checks": ["Retain meaning."]}
        self.write(self.root / "criteria.json", [case])
        for mode in ("skill", "baseline"):
            self.write(self.root / mode / "batch-01/requests.json",
                       [{key: case[key] for key in ("id", "request", "input")}])
        snapshot = self.root / "snapshot/yaya/SKILL.md"
        snapshot.parent.mkdir(parents=True)
        snapshot.write_text("Synthetic skill fixture.", encoding="utf-8")
        digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {"protocol": 2, "case_ids": ["sample"],
                    "snapshot_sha256": {"SKILL.md": digest(snapshot)},
                    "criteria_sha256": digest(self.root / "criteria.json"),
                    "request_sha256": {f"{mode}/batch-01/requests.json":
                                       digest(self.root / mode / "batch-01/requests.json")
                                       for mode in ("skill", "baseline")}, "data_sha256": {}}
        self.write(self.root / "manifest.json", manifest)
        return case

    def test_snapshot_and_criteria_mutations_are_rejected(self):
        case = self.frozen_run()
        self.assertEqual(COLLECT.verify_run(self.root)[1], [case])
        for relative in ("snapshot/yaya/SKILL.md", "criteria.json", "skill/batch-01/requests.json"):
            path = self.root / relative
            original = path.read_bytes()
            path.write_bytes(original + b"\n")
            with self.subTest(path=relative), self.assertRaisesRegex(ValueError, "changed"):
                COLLECT.verify_run(self.root)
            path.write_bytes(original)

    def test_packets_must_match_cases_even_with_valid_hashes(self):
        self.frozen_run()
        path = self.root / "baseline/batch-01/requests.json"
        self.write(path, [{"id": "sample", "request": "Different task.", "input": "Original."}])
        manifest = COLLECT.read_json(self.root / "manifest.json")
        manifest["request_sha256"]["baseline/batch-01/requests.json"] = hashlib.sha256(path.read_bytes()).hexdigest()
        self.write(self.root / "manifest.json", manifest)
        with self.assertRaisesRegex(ValueError, "requests differ"):
            COLLECT.verify_run(self.root)

    def test_added_snapshot_or_external_data_files_are_rejected_but_caches_are_ignored(self):
        self.frozen_run()
        for relative in ("snapshot/yaya/extra.md", "data/language-packs/new/GUIDE.md",
                         "skill/batch-99/requests.json"):
            path = self.root / relative
            self.write(path, [])
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "file set changed"):
                COLLECT.verify_run(self.root)
            path.unlink()
        self.write(self.root / "snapshot/yaya/__pycache__/generated.pyc", "cache")
        self.write(self.root / "data/__pycache__/generated.pyc", "cache")
        COLLECT.verify_run(self.root)

    def test_manifest_hash_paths_cannot_escape_and_v2_fields_are_required(self):
        self.frozen_run()
        original = COLLECT.read_json(self.root / "manifest.json")
        for relative in ("../outside.md", "D:/outside.md", "/outside.md", "sub/../SKILL.md"):
            manifest = {**original, "snapshot_sha256": {relative: "unused"}}
            self.write(self.root / "manifest.json", manifest)
            with self.subTest(relative=relative), self.assertRaisesRegex(ValueError, "Unsafe"):
                COLLECT.verify_run(self.root)
        self.write(self.root / "manifest.json", {key: value for key, value in original.items()
                                               if key != "criteria_sha256"})
        with self.assertRaisesRegex(ValueError, "required"):
            COLLECT.verify_run(self.root)

    def test_outputs_cannot_be_swapped_between_generation_contexts(self):
        self.write(self.output.with_name("requests.json"), [{"id": "different"}])
        self.write(self.output, [self.row])
        with self.assertRaisesRegex(ValueError, "does not belong"):
            COLLECT.load_outputs(self.root, "baseline", {"sample"})

    def preparation_fixture(self):
        tests = self.root / "project/tests"
        cases = [{"id": identifier, "task": "humanize", "request": "Polish this.", "input": "Original.",
                  "checks": ["Hidden criterion."], "group": "hidden group"}
                 for identifier in ("one", "two", "three")]
        self.write(tests / "evals/synthetic.json", {"cases": cases, "pilot_case_ids": ["three", "one"]})
        self.write(tests.parent / "core/yaya/SKILL.md", "Synthetic skill")
        self.write(tests.parent / "language-packs/x/GUIDE.md", "Synthetic guide")
        return tests, cases

    def test_pilot_preserves_selection_order_and_hides_all_criteria(self):
        tests, cases = self.preparation_fixture()
        run = tests / "runs/pilot"
        with patch.object(PREPARE, "ROOT", tests):
            PREPARE.prepare(run, ["synthetic"], pilot=True)
        manifest, frozen = COLLECT.verify_run(run)
        self.assertEqual([case["id"] for case in frozen], ["three", "one"])
        self.assertEqual(manifest["batch_size"], 1)
        self.assertEqual(manifest["isolation"], "fresh context per case")
        for mode in ("skill", "baseline"):
            packets = sorted((run / mode).glob("batch-*/requests.json"))
            self.assertEqual(len(packets), 2)
            for path in packets:
                packet = COLLECT.read_json(path)
                self.assertEqual(len(packet), 1)
                self.assertEqual(set(packet[0]), {"id", "request", "input"})
        self.assertEqual([case["checks"] for case in frozen], [cases[2]["checks"], cases[0]["checks"]])

    def test_invalid_suites_and_pilots_fail_before_creating_runs(self):
        tests, cases = self.preparation_fixture()
        with patch.object(PREPARE, "ROOT", tests):
            for suites, pilot in ((["../outside"], False), ([str(tests / "evals/synthetic.json")], False),
                                  (["synthetic", "synthetic"], False), (["synthetic", "synthetic"], True)):
                with self.subTest(suites=suites), self.assertRaises(ValueError):
                    PREPARE.prepare(tests / "runs/invalid", suites, pilot=pilot)
                self.assertFalse((tests / "runs/invalid").exists())
            for suite in ({"cases": [{key: value for key, value in cases[0].items() if key != "checks"}]},
                          {"cases": cases}, {"cases": cases, "pilot_case_ids": ["missing"]},
                          {"cases": cases, "pilot_case_ids": ["one", "one"]}):
                self.write(tests / "evals/invalid.json", suite)
                with self.subTest(suite=suite), self.assertRaises(ValueError):
                    PREPARE.prepare(tests / "runs/invalid", ["invalid"], pilot=True)
                self.assertFalse((tests / "runs/invalid").exists())

    def test_default_suites_and_explicit_batch_isolation(self):
        cases, suites = PREPARE.load_suites(None, False)
        self.assertEqual(suites, ["cases.json", "heldout.json", "humanize.json", "scenarios.json"])
        self.assertEqual(len(cases), sum(len(COLLECT.read_json(TESTS / "evals" / name)["cases"]) for name in suites))
        tests, _ = self.preparation_fixture()
        run = tests / "runs/batched"
        with patch.object(PREPARE, "ROOT", tests):
            PREPARE.prepare(run, ["synthetic"], batch_size=2)
        manifest, _ = COLLECT.verify_run(run)
        self.assertEqual(manifest["isolation"], "fresh context per batch, not per case")
        self.assertEqual(manifest["batches_per_condition"], 2)

    def test_explicit_subset_rejects_unknown_ids_and_records_complete_selection(self):
        tests, _ = self.preparation_fixture()
        with patch.object(PREPARE, "ROOT", tests):
            for identifiers in ([], ["missing"], ["one", "one"]):
                with self.subTest(ids=identifiers), self.assertRaises(ValueError):
                    PREPARE.prepare(tests / "runs/invalid", ["synthetic"], case_ids=identifiers)
                self.assertFalse((tests / "runs/invalid").exists())
            run = tests / "runs/subset"
            PREPARE.prepare(run, ["synthetic"], case_ids=["two", "one"])
        manifest, cases = COLLECT.verify_run(run)
        self.assertEqual(manifest["case_ids"], ["two", "one"])
        self.assertEqual(manifest["cases"], 2)
        self.assertEqual([case["id"] for case in cases], ["two", "one"])

    def test_summary_rejects_incomplete_ratings_and_preference_over_hard_failure(self):
        self.write(self.root / "cases.json", [{"id": "sample"}])
        self.write(self.root / "blind-key.json", {"sample": {"A": "skill", "B": "baseline"}})
        self.write(self.root / "mechanical.json",
                   [{"id": "sample", "condition": mode, "literal_failures": []}
                    for mode in ("skill", "baseline")])
        rating = {"fidelity": "pass", "task": "pass", "quality": "same", "evidence": "Meaning retained."}
        row = {"id": "sample", "A": rating, "B": rating, "preference": "tie", "reason": "Equivalent."}
        self.write(self.root / "judgments.json", [row])
        command = [sys.executable, str(TESTS / "evals/summarize.py"), str(self.root)]
        valid = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        summary = json.loads(valid.stdout)
        self.assertEqual(summary["conditions"]["skill"]["hard_pass"], 1)
        self.assertEqual(summary["preferences"]["tie"], 1)
        for rows in ([], [row, row], [{**row, "A": {**rating, "task": "fail"}, "preference": "A"}],
                     [{**row, "B": {**rating, "fidelity": "unknown"}}]):
            with self.subTest(rows=rows):
                self.write(self.root / "judgments.json", rows)
                invalid = subprocess.run(command, capture_output=True, text=True)
                self.assertNotEqual(invalid.returncode, 0)

    def test_summary_rejects_invalid_blinding_and_duplicate_or_missing_checks(self):
        self.write(self.root / "cases.json", [{"id": "sample"}])
        key = {"sample": {"A": "skill", "B": "baseline"}}
        mechanical = [{"id": "sample", "condition": mode, "literal_failures": []}
                      for mode in ("skill", "baseline")]
        rating = {"fidelity": "pass", "task": "pass", "quality": "same", "evidence": "Meaning retained."}
        self.write(self.root / "judgments.json",
                   [{"id": "sample", "A": rating, "B": rating, "preference": "tie", "reason": "Equivalent."}])
        command = [sys.executable, str(TESTS / "evals/summarize.py"), str(self.root)]
        self.write(self.root / "mechanical.json", mechanical)
        for invalid_key in ({}, {"sample": {"A": "skill", "B": "skill"}},
                            {"sample": {"A": "skill", "B": "baseline", "C": "baseline"}}):
            self.write(self.root / "blind-key.json", invalid_key)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Blind key", result.stderr)
        self.write(self.root / "blind-key.json", key)
        for invalid_checks in (mechanical[:1], mechanical + [mechanical[0]],
                               [mechanical[0], {**mechanical[1], "comment_boundary": {"status": "invented"}}]):
            self.write(self.root / "mechanical.json", invalid_checks)
            result = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
        self.write(self.root / "mechanical.json",
                   [{**mechanical[0], "comment_boundary": {"status": "error"}}, mechanical[1]])
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["conditions"]["skill"]["hard_uncertain"], 1)


if __name__ == "__main__":
    unittest.main()

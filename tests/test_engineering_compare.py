"""Paired evaluation protocol; these tests do not call a model or score semantics."""

import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests/evals"))
import engineering_compare as paired


class PairedProtocol(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=ROOT / "tests")
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.old, self.new = self.root / "old", self.root / "new"
        for folder, text in ((self.old, "Old guidance"), (self.new, "New guidance")):
            (folder / "references").mkdir(parents=True)
            (folder / "SKILL.md").write_text(text, encoding="utf-8")
            (folder / "references/text.md").write_text("Editing rules", encoding="utf-8")
        self.suite = self.root / "suite.json"
        self.suite.write_text(json.dumps({"cases": [{"id": "sample", "task": "text", "request": "Polish",
                "input": "Same original", "checks": ["HIDDEN_EXPECTATION_39492"]}]}), encoding="utf-8")
        self.run = self.root / "tests/runs/paired"

    def prepare(self):
        with patch.object(paired, "ROOT", self.root):
            return paired.prepare(self.run, self.old, self.new, self.suite)

    def test_requests_context_labels_and_hidden_expectations(self):
        self.prepare()
        _, jobs = paired.jobs(self.run)
        self.assertEqual([job.condition for job in jobs], ["old", "new"])
        for job in jobs:
            self.assertNotIn("HIDDEN_EXPECTATION_39492", job.prompt)
            self.assertIn("Same original", job.prompt)
            self.assertEqual(set(job.context_hashes), {"SKILL.md", "references/text.md"})
        self.assertEqual((self.run / "old/sample/requests.json").read_bytes(),
                         (self.run / "new/sample/requests.json").read_bytes())

    def test_mutated_inputs_model_or_runner_rejected_before_execution(self):
        self.prepare()
        with patch.object(paired, "configured_model", return_value={"changed": True}):
            with self.assertRaisesRegex(ValueError, "configuration"):
                paired.jobs(self.run)
        path = self.run / "new/sample/requests.json"
        path.write_text("[]", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "Frozen input changed"):
            paired.jobs(self.run)

    def test_incomplete_attempt_cannot_be_collected_as_valid_comparison(self):
        self.prepare()
        with self.assertRaises(OSError):
            paired.collect(self.run, self.root / "results")
        self.assertFalse((self.root / "results").exists())

    def test_unfrozen_additional_guidance_rejected(self):
        self.prepare()
        (self.run / "old/snapshot/yaya/references/engineering.md").write_text("New unfrozen guidance", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "file set changed"):
            paired.jobs(self.run)

    def test_explicitly_requested_delivery_notes_are_visible_to_reviewer(self):
        response = {"text": "Complete code", "notes": "No checks were executed."}
        self.assertEqual(paired.review_answer({}, response), "Complete code")
        self.assertEqual(paired.review_answer({"review_delivered_notes": True}, response),
                         "Complete code\n\nDelivered notes:\nNo checks were executed.")


if __name__ == "__main__":
    unittest.main()

"""Reject unusable command catalogs before help or task planning."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from test_commands import CORE, ROOT, commands


class CatalogTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix=".catalog-", dir=ROOT)
        self.addCleanup(temporary.cleanup)
        self.core = Path(temporary.name) / "yaya"
        shutil.copytree(CORE, self.core, ignore=shutil.ignore_patterns("__pycache__"))
        self.catalog = commands.load_catalog(self.core)

    def reject(self, change):
        catalog = copy.deepcopy(self.catalog)
        change(catalog)
        (self.core / "catalog.json").write_text(json.dumps(catalog), encoding="utf-8")
        with self.assertRaises(ValueError):
            commands.resolve(["human"], core=self.core)

    def test_invalid_defaults_and_action_shapes(self):
        for key, field, value in (
            ("focus", "default", "opus"), ("focus", "choices", []),
            ("focus", "choices", ["all", "all"]), ("focus", "choices", "all"),
            ("write", "default", True), ("write", "flag", "yes"),
            ("write", "repeat", True), ("file", "default", ["secret.md"]),
            ("focus", "nargs", "+"), ("focus", "dest", "write"),
            ("write", "flag", False), ("file", "repeat", False),
            ("save", "flag", True),
            ("source", "repeat", False), ("source", "flag", True), ("style", "default", "team.md"),
        ):
            with self.subTest(key=key, field=field, value=value):
                self.reject(lambda c: c["options"][key].update({field: value}))

    def test_duplicate_and_malformed_command_fields(self):
        for field, value in (
            ("options", ["focus", "focus"]), ("options", "focus"),
            ("references", []), ("references", [None]), ("summary", ""),
            ("delivery", "unknown"),
        ):
            with self.subTest(field=field):
                self.reject(lambda c: c["commands"]["human"].update({field: value}))

    def test_readonly_delivery_cannot_gain_write_options(self):
        self.reject(lambda c: c["commands"]["review"]["options"].append("write"))
        self.reject(lambda c: c["commands"]["origin"]["options"].append("save"))
        self.reject(lambda c: c["commands"]["human"]["options"].remove("file"))
        self.reject(lambda c: c["commands"]["human"]["options"].append("source"))
        self.reject(lambda c: c["commands"]["review"]["options"].append("style"))

    def test_reserved_selectors_and_incomplete_domain(self):
        self.reject(lambda c: c["options"].update({"help": {"help": "collision"}}))
        self.reject(lambda c: c["commands"].update({"domains": c["commands"]["human"]}))
        self.reject(lambda c: c["domains"]["tech"].pop("preserves"))

    def test_current_catalog_still_supports_help_and_plans(self):
        for name in self.catalog["commands"]:
            self.assertIn("usage:", commands.resolve([name, "--help"], core=self.core))
            args = ([name, "--before", "old.md", "--after", "new.md"] if name == "check" else
                    [name, "--file", "draft.md", "--lang", "en"] if name == "scan" else [name])
            self.assertEqual(commands.resolve(args, core=self.core)["command"], name)


if __name__ == "__main__":
    unittest.main()

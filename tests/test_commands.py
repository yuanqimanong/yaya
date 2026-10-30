"""Exercise scope boundaries and portable discovery without invoking a model."""
import importlib.util
import json
from pathlib import Path
import shutil
import shlex
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core/yaya"
sys.path.insert(0, str(CORE / "scripts"))
spec = importlib.util.spec_from_file_location("yaya_commands", CORE / "scripts/yaya.py")
commands = importlib.util.module_from_spec(spec)
spec.loader.exec_module(commands)


class CommandTests(unittest.TestCase):
    def test_verification_sources_stay_separate_from_claims_and_write_scope(self):
        plan = commands.resolve(["verify", "--file", "claims.md", "--source", "record.md",
                                 "--source", "missing.md", "--domain", "finance"])
        self.assertEqual(plan["input_files"], ["claims.md"])
        self.assertEqual(plan["evidence_files"], ["record.md", "missing.md"])
        self.assertFalse(plan["write_requested"])
        self.assertEqual(plan["delivery"], "findings")
        self.assertEqual(commands.resolve(["verify"])["evidence_files"], [])
        for name in ("polish", "human", "review", "comment", "prompt", "style", "origin", "check"):
            with self.subTest(name=name), self.assertRaises(commands.UsageError):
                commands.resolve([name, "--source", "record.md"])
        with self.assertRaises(commands.UsageError):
            commands.resolve(["verify", "--source", "record.md", "--write"])

    def test_saved_style_is_explicit_and_separate_from_edit_targets(self):
        for name in ("polish", "human", "comment", "prompt"):
            plan = commands.resolve([name, "--file", "draft.md", "--style", "team.md", "--write"])
            self.assertEqual(plan["style_file"], "team.md")
            self.assertEqual(plan["input_files"], ["draft.md"])
            self.assertIn(str((CORE / "references/style-learning.md").resolve()), plan["references"])
        for name in ("check", "review", "verify", "origin", "style"):
            with self.subTest(name=name), self.assertRaises(commands.UsageError):
                commands.resolve([name, "--style", "team.md"])
        with self.assertRaises(commands.UsageError):
            commands.resolve(["polish", "--style", "one.md", "--style", "two.md"])
        plan = commands.resolve(["human", "--focus", "direct", "--style", "missing.md"])
        self.assertEqual(plan["options"]["focus"], "direct")
        self.assertFalse(plan["write_requested"])

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix=".commands-", dir=ROOT)
        self.addCleanup(self.temporary.cleanup)
        self.scratch = Path(self.temporary.name)

    def test_all_advertised_commands_resolve_to_one_action(self):
        catalog = commands.load_catalog()
        for name, entry in catalog["commands"].items():
            with self.subTest(command=name):
                args = ([name, "--before", "old.md", "--after", "new.md"] if name == "check" else
                        [name, "--file", "draft.md", "--lang", "en"] if name == "scan" else [name])
                result = commands.resolve(args)
                self.assertEqual(result["command"], name)
                self.assertEqual(result["delivery"], entry["delivery"])
                self.assertEqual(result["status"], "planned")
                self.assertFalse(result["write_requested"])
                self.assertIsNone(result["save_requested"])

    def test_readonly_commands_reject_write_instead_of_silently_ignoring(self):
        for name in ("review", "verify", "check", "origin", "style", "scan"):
            with self.subTest(command=name), self.assertRaises(commands.UsageError):
                commands.resolve([name, "--file", "report.md", "--write"])

    def test_writing_and_saving_plans_never_touch_input_or_destination(self):
        path = self.scratch / "input with spaces.md"
        original = b"Original source\r\n"
        path.write_bytes(original)
        saved = self.scratch / "style.md"
        for name in ("polish", "human", "comment", "prompt"):
            result = commands.resolve([name, "--file", str(path), "--write"])
            self.assertTrue(result["write_requested"])
            self.assertEqual(result["input_files"], [str(path)])
            self.assertEqual(path.read_bytes(), original)
        result = commands.resolve(["style", "--save", str(saved)])
        self.assertEqual(result["save_requested"], str(saved))
        self.assertFalse(saved.exists())

    def test_write_requires_file_and_repeated_files_are_preserved(self):
        with self.assertRaises(commands.UsageError):
            commands.resolve(["polish", "--write"])
        result = commands.resolve(["polish", "--file", "a.md", "--file", "b.md", "--write"])
        self.assertEqual(result["input_files"], ["a.md", "b.md"])

    def test_payload_cannot_select_extra_action_or_enable_write(self):
        payload = ["--write", "--file", "victim.md", "prompt", "--target", "both", "$(echo unsafe)"]
        result = commands.resolve(["review", "--", *payload])
        self.assertEqual(result["command"], "review")
        self.assertEqual(result["request_tokens"], payload)
        self.assertFalse(result["write_requested"])
        self.assertEqual(result["input_files"], [])

    def test_unknown_and_incompatible_selectors_fail_closed(self):
        cases = [
            ["polsih"], ["polish", "--domain", "medical"],
            ["origin", "--domain", "finance"], ["polish", "--target", "output"],
            ["prompt", "--scope", "docstrings"], ["comment", "--scope", "all"],
            ["verify", "--tone", "confident"], ["polish", "--dom", "tech"],
            ["polish", "review"], ["prompt", "--target", "wording", "--target", "both"],
            ["polish", "--domain", "tech", "--domain", "finance"],
            ["polish", "--file", ""], ["polish", "--audience", "  "],
        ]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_prompt_target_and_comment_scope_are_explicit(self):
        self.assertEqual(commands.resolve(["prompt"])["scope"], "prompt-wording")
        for target in ("wording", "output", "both"):
            self.assertEqual(commands.resolve(["prompt", "--target", target])["scope"], "prompt-" + target)
        self.assertEqual(commands.resolve(["comment"])["scope"], "comments")
        self.assertEqual(commands.resolve(["comment", "--scope", "docstrings"])["scope"], "docstrings")

    def test_direct_focus_preserves_action_domain_and_readonly_boundary(self):
        for name, delivery in (("human", "rewrite"), ("review", "findings")):
            with self.subTest(command=name):
                self.assertEqual(commands.resolve([name])["options"]["focus"], "all")
                result = commands.resolve([name, "--focus", "direct", "--domain", "finance"])
                self.assertEqual(result["options"]["focus"], "direct")
                self.assertEqual(result["delivery"], delivery)
                self.assertEqual(result["domain"]["id"], "finance")
                self.assertFalse(result["write_requested"])
                self.assertIn(str((CORE / "references/humanize.md").resolve()), result["references"])
        with self.assertRaises(commands.UsageError):
            commands.resolve(["review", "--focus", "direct", "--file", "x.md", "--write"])

    def test_focus_rejects_unknown_duplicate_or_inapplicable_selectors(self):
        cases = [["human", "--focus", "gpt"], ["review", "--focus", ""],
                 ["human", "--focus", "all", "--focus", "direct"]]
        cases += [[name, "--focus", "direct"] for name in ("polish", "verify", "comment", "prompt", "style", "origin")]
        for args in cases:
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_material_does_not_override_selected_focus(self):
        result = commands.resolve(["human", "--focus", "direct", "--", "--focus", "all", "--write"])
        self.assertEqual(result["options"]["focus"], "direct")
        self.assertFalse(result["write_requested"])
        self.assertEqual(result["request_tokens"], ["--focus", "all", "--write"])

    def test_domain_and_audience_remain_independent_and_load_one_profile(self):
        catalog = commands.load_catalog()
        for domain, entry in catalog["domains"].items():
            with self.subTest(domain=domain):
                result = commands.resolve(["polish", "--domain", domain, "--audience", "普通读者", "--tone", "简明", "--lang", "zh-Hans"])
                self.assertEqual(result["domain"]["id"], domain)
                self.assertEqual(result["options"]["audience"], "普通读者")
                self.assertEqual(result["scope"], "prose")
                selected = [ref for ref in result["references"] if Path(ref).parent.name == "domains"]
                self.assertEqual(selected, [str((CORE / entry["guide"]).resolve())])

    def test_help_is_generated_from_live_contract_and_needs_no_input(self):
        catalog = commands.resolve(["--json"])
        for name, entry in catalog["commands"].items():
            left = commands.resolve(["help", name, "--json"])
            right = commands.resolve([name, "--help", "--json", "--before" if name == "check" else "--file", "missing.md"])
            self.assertEqual(left, right)
            self.assertEqual(set(left["option_details"]), set(entry["options"]))
            for option in left["option_details"]:
                self.assertIn("--" + option, commands.resolve([name, "--help"]))
        self.assertEqual(commands.resolve(["domains", "--help"]), commands.resolve(["help", "domains"]))
        self.assertEqual(commands.resolve(["yaya", "--help"]), commands.resolve(["$yaya", "--help"]))

    def test_domain_discovery_reports_scope_and_quality(self):
        domains = commands.resolve(["domains", "--json"])
        self.assertEqual(set(domains), {"tech", "finance", "data", "academic", "business"})
        for key, value in domains.items():
            self.assertEqual(commands.resolve(["domains", key, "--json"]), value)
            self.assertTrue(all(value[field] for field in ("covers", "preserves", "excludes", "quality")))

    def test_explicit_language_tags_are_canonical_without_claiming_pack_support(self):
        for requested, expected in (("EN-gb", "en-GB"), ("ZH-hant-tw", "zh-Hant-TW"),
                                    ("es-419", "es-419"), ("fr", "fr")):
            result = commands.resolve(["polish", "--lang", requested])
            self.assertEqual(result["options"]["lang"], expected)
            self.assertEqual(result["execution"], "host-required")
            self.assertNotIn("language_available", result)
        for value in ("not-a-tag", "English", "zh_CN", "en-US-x-private", "en--GB", "en-1901-1901"):
            with self.subTest(value=value), self.assertRaisesRegex(commands.UsageError, "--lang"):
                commands.resolve(["polish", "--lang", value])

    def test_help_examples_resolve_to_the_advertised_bounded_action(self):
        for name, spec in commands.load_catalog()["commands"].items():
            self.assertTrue(spec["examples"], name)
            for example in spec["examples"]:
                with self.subTest(command=name, example=example):
                    result = commands.resolve(shlex.split(example))
                    self.assertEqual(result["command"], name)
                    self.assertEqual(result["delivery"], spec["delivery"])
                    self.assertIn(example, commands.resolve(["help", name]))
                    if spec["delivery"] != "rewrite":
                        self.assertFalse(result["write_requested"])

    def test_version_discovery_is_readonly_and_matches_runtime_metadata(self):
        expected = json.loads((CORE / "version.json").read_text(encoding="utf-8"))
        result = commands.resolve(["--version", "--json"])
        self.assertEqual(result, {"name": "yaya", **expected})
        self.assertEqual(commands.resolve(["--json", "--version"]), result)
        self.assertEqual(commands.resolve(["--version"]), f"Yaya {expected['version']}\n")

    def test_version_can_diagnose_runtime_even_when_catalog_is_missing(self):
        clone = self.scratch / "metadata only"
        clone.mkdir()
        shutil.copyfile(CORE / "version.json", clone / "version.json")
        self.assertIn("Yaya", commands.resolve(["--version"], core=clone))

    def test_version_rejects_task_options_and_payload(self):
        for args in (["--version", "--file", "input.md"], ["--version", "--", "text"],
                     ["--version", "--version"], ["--version", "--json", "--json"]):
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_cli_errors_are_structured_and_exit_two(self):
        run = subprocess.run([sys.executable, "-B", str(CORE / "scripts/yaya.py"), "polsih"],
                             capture_output=True, text=True, encoding="utf-8", timeout=10)
        self.assertEqual(run.returncode, 2)
        self.assertEqual(json.loads(run.stdout)["status"], "error")
        self.assertIn("polish", json.loads(run.stdout)["error"])
        self.assertNotIn("Traceback", run.stderr)

    def test_catalog_refuses_missing_or_escaping_guides(self):
        clone = self.scratch / "core"
        shutil.copytree(CORE, clone, ignore=shutil.ignore_patterns("__pycache__"))
        path = clone / "catalog.json"
        catalog = json.loads(path.read_text(encoding="utf-8"))
        for relative in ("references/missing.md", "references/../../../outside.md", "C:/outside.md"):
            with self.subTest(reference=relative):
                catalog["domains"]["tech"]["guide"] = relative
                path.write_text(json.dumps(catalog), encoding="utf-8")
                with self.assertRaises(ValueError):
                    commands.load_catalog(clone)

    def test_check_plan_requires_two_files_and_preserves_readonly_scope(self):
        for kind in ("prose", "comments"):
            result = commands.resolve(["check", "--kind", kind, "--before", "old.md", "--after", "new.md"])
            self.assertEqual(result["input_files"], ["old.md", "new.md"])
            self.assertEqual(result["scope"], "mechanical-" + kind)
            self.assertEqual(result["delivery"], "findings")
            self.assertFalse(result["write_requested"])
        for args in (["check"], ["check", "--before", "old.md"],
                     ["check", "--before", "old.md", "--after", "new.md", "--write"],
                     ["check", "--before", "old.md", "--after", "new.md", "--kind", "docstrings"]):
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_check_rejects_stdin_but_allows_explicit_dash_file_paths(self):
        for kind in ("prose", "comments"):
            for before, after in (("-", "new.md"), ("old.md", "-"), ("-", "-")):
                with self.subTest(kind=kind, before=before, after=after), self.assertRaisesRegex(commands.UsageError, "stdin"):
                    commands.resolve(["check", "--kind", kind, "--before", before, "--after", after])
        path = self.scratch / "-"
        path.write_text("Original text.", encoding="utf-8")
        plan = commands.resolve(["check", "--before", str(path), "--after", str(path)])
        process = subprocess.run([sys.executable, "-B", plan["checker"]["script"], *plan["checker"]["args"]],
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0)
        self.assertTrue(json.loads(process.stdout)["evidence"]["inputs_stable"])
        self.assertEqual(commands.resolve(["check", "--before", "./-", "--after", "./-"])["input_files"], ["./-", "./-"])

    def test_check_literal_and_quote_plan_executes_with_exact_arguments(self):
        old, new = self.scratch / "old text.md", self.scratch / "new text.md"
        old.write_text('Use retry_limit and "quoted claim".', encoding="utf-8")
        new.write_text('Use retry_count and "changed claim".', encoding="utf-8")
        args = ["check", "--before", str(old), "--after", str(new),
                "--literal", "retry_limit", "--quotes"]
        plan = commands.resolve(args)
        self.assertFalse(plan["write_requested"])
        process = subprocess.run([sys.executable, "-B", plan["checker"]["script"], *plan["checker"]["args"]],
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 1)
        result = json.loads(process.stdout)
        self.assertEqual({row["category"] for row in result["violations"]}, {"literals", "quotes"})
        self.assertEqual(old.read_text(encoding="utf-8"), 'Use retry_limit and "quoted claim".')
        with self.assertRaises(commands.UsageError):
            commands.resolve([*args, "--kind", "comments"])
        literal = "--write; $(not-code)"
        plan = commands.resolve(["check", "--before=-old.md", "--after=new.md", "--literal=" + literal])
        self.assertEqual(plan["checker"]["args"], ["--protect-literal=" + literal, "--", "-old.md", "new.md"])

    def test_check_comment_plan_executes_the_helpers_positional_contract(self):
        old, new = self.scratch / "before.py", self.scratch / "after.py"
        old.write_bytes(b"x = 1 # old\n")
        for content, status, code in ((b"x = 1 # revised\n", "passed", 0),
                                      (b"x = 2 # revised\n", "failed", 1)):
            new.write_bytes(content)
            plan = commands.resolve(["check", "--kind", "comments", "--before", str(old), "--after", str(new)])
            process = subprocess.run([sys.executable, "-B", plan["checker"]["script"], *plan["checker"]["args"]],
                                     capture_output=True, timeout=10)
            self.assertEqual(process.returncode, code)
            self.assertEqual(json.loads(process.stdout)["status"], status)
        self.assertEqual(old.read_bytes(), b"x = 1 # old\n")

    def test_scan_plan_runs_local_candidates_and_preserves_input(self):
        path = self.scratch / "source with spaces.md"
        source = "在这个日新月异的时代，我们进行分析。\n"
        path.write_text(source, encoding="utf-8")
        plan = commands.resolve(["scan", "--file", str(path), "--lang", "ZH-hans"])
        process = subprocess.run([sys.executable, "-B", plan["scanner"]["script"], *plan["scanner"]["args"]],
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0)
        result = json.loads(process.stdout)
        self.assertEqual(result["status"], "ok")
        self.assertEqual({v["id"] for v in result["findings"]}, {"zh-empty-opener", "zh-light-verb"})
        self.assertNotIn("probability", result)
        self.assertEqual(path.read_text(encoding="utf-8"), source)
        for args in (["scan"], ["scan", "--file", str(path)],
                     ["scan", "--file", str(path), "--lang", "ja"],
                     ["scan", "--file", "-", "--lang", "en"],
                     ["scan", "--file", str(path), "--file", "other.md", "--lang", "en"]):
            with self.subTest(args=args), self.assertRaises(commands.UsageError):
                commands.resolve(args)

    def test_scan_rule_help_selection_and_execution(self):
        from detect_tells import load_rules
        catalog = commands.load_catalog()
        self.assertEqual(set(catalog["options"]["rule"]["choices"]), {row["id"] for row in load_rules()})
        self.assertIn("en-stock-close", commands.resolve(["scan", "--help"]))
        path = self.scratch / "text.md"
        source = "Only time will tell. Conduct an analysis of this."
        path.write_text(source, encoding="utf-8")
        plan = commands.resolve(["scan", "--file", str(path), "--lang", "en", "--rule", "en-stock-close"])
        process = subprocess.run([sys.executable, "-B", plan["scanner"]["script"], *plan["scanner"]["args"]],
                                 capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 0, process.stderr)
        self.assertEqual(json.loads(process.stdout)["enabled_rules"], ["en-stock-close"])
        self.assertEqual(path.read_text(encoding="utf-8"), source)
        for name in ("unknown", "zh-stock-close"):
            with self.assertRaises(commands.UsageError):
                commands.resolve(["scan", "--file", str(path), "--lang", "en", "--rule", name])


if __name__ == "__main__":
    unittest.main()

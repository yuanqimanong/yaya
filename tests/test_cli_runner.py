"""Runner protocol tests with a local fake CLI; these do not measure model quality."""
import hashlib
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
    SPEC = importlib.util.spec_from_file_location("yaya_cli_runner", TESTS / "evals/run_cli.py")
    RUNNER = importlib.util.module_from_spec(SPEC)
    sys.modules[SPEC.name] = RUNNER
    SPEC.loader.exec_module(RUNNER)
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
out = Path(sys.argv[sys.argv.index("-o") + 1])
if mode in {"inherited-success", "inherited-timeout"}:
    child = ("import os,sys,time\nfrom pathlib import Path\n"
             "stop=Path(sys.argv[1]); done=Path(sys.argv[2]); deadline=time.monotonic()+4\n"
             "while not stop.exists() and time.monotonic()<deadline: time.sleep(.01)\n"
             "os.close(1); os.close(2); done.touch()\n")
    subprocess.Popen([sys.executable, "-c", child, str(out.with_name("descendant.stop")),
                      str(out.with_name("descendant.done"))], stdout=sys.stdout, stderr=sys.stderr)
if mode == "known-diagnostic":
    message = ("Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model` is ignored.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model_reasoning_effort` is ignored.\n"
               "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.notify` is ignored.")
    for index in range(2):
        print(json.dumps({"type":"item.completed","item":{"id":str(index),"type":"error","message":message}}))
if mode == "timeout":
    print(json.dumps({"type":"thread.started","thread_id":"fake"}), flush=True)
    time.sleep(3)
if mode == "exit":
    print("Deliberate fixture failure.", file=sys.stderr)
    sys.exit(7)
result = {"id":"sample", "text":"Synthetic response.", "notes":"", "skill_used":False}
if mode == "wrong-id":
    result["id"] = "another-case"
if mode == "empty":
    result["text"] = ""
out.write_text("{" if mode == "malformed" else json.dumps(result), encoding="utf-8")
if mode == "tools":
    print(json.dumps({"type":"item.completed","item":{"type":"command_execution","command":"not executed"}}))
if mode == "bad-log":
    print("this is not JSON")
if mode != "incomplete":
    print(json.dumps({"type":"turn.completed","usage":{"input_tokens":12,"cached_input_tokens":0,"output_tokens":8}}),flush=True)
if mode == "inherited-timeout":
    time.sleep(3)
'''


class CliRunner(unittest.TestCase):
    def test_ambiguous_and_nonfinite_events_do_not_hide_invalid_evidence(self):
        sources = ['{"type":"item.completed","item":{"type":"command_execution","type":"reasoning"}}',
                   '{"type":"error","type":"turn.completed"}']
        sources += ['{"type":"turn.completed","usage":{"input_tokens":' + value + '}}'
                    for value in ("NaN", "Infinity", "-Infinity", "1e999")]
        for source in sources:
            with self.subTest(source=source):
                result = RUNNER.inspect_events(source)
                self.assertEqual(result["malformed_jsonl_lines"], 1)
                self.assertEqual(result["completed_turns"], 0)

    def test_unknown_events_and_malformed_items_invalidate_runs(self):
        for event in ({"type": "future.tool.event"}, {"type": ["turn.completed"]}, {},
                      {"type": "item.completed"}, {"type": "item.updated", "item": "text"},
                      {"type": "item.started", "item": {"type": []}}):
            with self.subTest(event=event):
                result = RUNNER.inspect_events(json.dumps(event))
                self.assertTrue(result["failed_events"] or result["tool_or_unknown_items"])

    def test_unicode_separators_inside_json_strings_are_not_record_boundaries(self):
        source = json.dumps({"type": "item.completed", "item": {"type": "agent_message", "text": "a\u2028b\u2029c"}},
                            ensure_ascii=False) + '\r\n{"type":"turn.completed"}\n'
        result = RUNNER.inspect_events(source)
        self.assertEqual(result["malformed_jsonl_lines"], 0)
        self.assertEqual(result["completed_turns"], 1)
        self.assertEqual(result["failed_events"], [])

    def setUp(self):
        (TESTS / "runs").mkdir(exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="cli-unit-", dir=TESTS / "runs")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.stub = self.root / "stub.py"
        self.stub.write_text(STUB, encoding="utf-8")

    def job(self, name="sample"):
        directory = self.root / name
        directory.mkdir()
        return RUNNER.Job(directory, "sample", "baseline", "A synthetic request.\n", {})

    def run_stub(self, mode, name="sample", **kwargs):
        job = self.job(name)
        result = RUNNER.run_one(job, [sys.executable, str(self.stub), mode], timeout=5, **kwargs)
        return job, result

    def test_success_retains_prompt_logs_usage_schema_and_final(self):
        job, result = self.run_stub("success")
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["returncode"], 0)
        self.assertEqual(result["usage"][0]["input_tokens"], 12)
        attempt = job.directory / "cli-attempt-01"
        self.assertEqual((attempt / "prompt.txt").read_text(encoding="utf-8"), job.prompt)
        self.assertEqual(set(result["artifact_sha256"]),
                         {"prompt.txt", "stdout.jsonl", "stderr.txt", "final.json", "output-schema.json"})
        self.assertEqual(json.loads((job.directory / "outputs.json").read_text())[0]["id"], "sample")
        self.assertIn("project_doc_max_bytes=0", result["command"])
        self.assertNotIn("--model", result["command"])

    def test_failures_keep_first_attempt_and_publish_no_output(self):
        for mode in ("exit", "wrong-id", "malformed", "empty", "tools", "bad-log", "incomplete"):
            with self.subTest(mode=mode):
                job, result = self.run_stub(mode, name=mode)
                self.assertEqual(result["status"], "failed")
                self.assertFalse((job.directory / "outputs.json").exists())
                before = (job.directory / "cli-attempt-01/completion.json").read_bytes()
                with self.assertRaises(ValueError):
                    RUNNER.run_one(job, [sys.executable, str(self.stub), "success"], 5, resume=True)
                self.assertEqual(before, (job.directory / "cli-attempt-01/completion.json").read_bytes())
                if mode == "exit":
                    self.assertEqual(result["returncode"], 7)

    def test_timeout_retains_partial_log_and_is_not_retryable_in_place(self):
        job = self.job()
        result = RUNNER.run_one(job, [sys.executable, str(self.stub), "timeout"], timeout=0.3)
        self.assertEqual(result["status"], "failed")
        self.assertIn("timeout", result["error"])
        self.assertTrue((job.directory / "cli-attempt-01/stdout.jsonl").is_file())
        self.assertFalse((job.directory / "outputs.json").exists())

    def test_resume_skips_valid_result_without_starting_child(self):
        job, result = self.run_stub("success")
        with patch.object(RUNNER.subprocess, "run", side_effect=AssertionError("must not start child")):
            resumed = RUNNER.run_one(job, ["missing-executable"], 5, resume=True)
        self.assertTrue(resumed["resumed"])
        self.assertEqual(result["artifact_sha256"], resumed["artifact_sha256"])
        with self.assertRaisesRegex(ValueError, "overwritten"):
            RUNNER.run_one(job, ["missing-executable"], 5)

    def test_resume_rejects_artifact_or_prompt_changes(self):
        for filename in ("prompt.txt", "stdout.jsonl", "stderr.txt", "final.json", "output-schema.json"):
            with self.subTest(filename=filename):
                job, _ = self.run_stub("success", name=filename)
                path = job.directory / "cli-attempt-01" / filename
                path.write_bytes(path.read_bytes() + b"\n")
                with self.assertRaisesRegex(ValueError, "changed"):
                    RUNNER.verify_completed(job, job.directory / "cli-attempt-01")
        job, _ = self.run_stub("success", name="prompt-change")
        changed = RUNNER.Job(job.directory, job.identifier, job.condition, job.prompt + "Changed", {})
        with self.assertRaisesRegex(ValueError, "incompatible"):
            RUNNER.verify_completed(changed, job.directory / "cli-attempt-01")

    def test_resume_rejects_changed_published_output(self):
        job, _ = self.run_stub("success")
        output = job.directory / "outputs.json"
        rows = json.loads(output.read_text())
        rows[0]["text"] = "An improved response selected later."
        output.write_text(json.dumps(rows), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "differs"):
            RUNNER.verify_completed(job, job.directory / "cli-attempt-01")

    def frozen_run(self, task="humanize", language="en"):
        run = self.root / "run"
        case = {"id": "sample", "request": "Rewrite this.", "input": "Source material.",
                "task": task, "language": language, "checks": ["SECRET_REVIEW_CHECK"],
                "group": "SECRET_GROUP"}
        files = {
            "snapshot/yaya/SKILL.md": "Synthetic Yaya fixture.",
            "snapshot/yaya/references/humanize.md": "Humanize fixture.",
            "snapshot/yaya/languages/en/GUIDE.md": "English GUIDE.",
            "snapshot/yaya/languages/en/PATTERNS.md": "English PATTERNS.",
            "data/language-packs/zh-Hant/GUIDE.md": "Traditional GUIDE.",
            "data/language-packs/zh-Hant/PATTERNS.md": "Traditional PATTERNS.",
            "criteria.json": json.dumps([case]),
        }
        for condition in ("skill", "baseline"):
            files[f"{condition}/batch-001/requests.json"] = json.dumps(
                [{key: case[key] for key in ("id", "request", "input")}])
        for name, text in files.items():
            path = run / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text, encoding="utf-8")
        sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
        manifest = {
            "protocol": 2, "batch_size": 1, "case_ids": ["sample"],
            "snapshot_sha256": {p.relative_to(run / "snapshot/yaya").as_posix(): sha(p)
                                for p in (run / "snapshot/yaya").rglob("*") if p.is_file()},
            "data_sha256": {p.relative_to(run).as_posix(): sha(p)
                            for p in (run / "data").rglob("*") if p.is_file()},
            "request_sha256": {p.relative_to(run).as_posix(): sha(p) for p in run.glob("*/batch-*/requests.json")},
            "criteria_sha256": sha(run / "criteria.json"),
        }
        (run / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return run

    def test_prompt_uses_frozen_guidance_and_excludes_rubric_and_group(self):
        run = self.frozen_run()
        _, jobs = RUNNER.prepare_jobs(run, ["skill", "baseline"], None)
        self.assertEqual(len(jobs), 2)
        for job in jobs:
            self.assertNotIn("SECRET_REVIEW_CHECK", job.prompt)
            self.assertNotIn("SECRET_GROUP", job.prompt)
            self.assertIn("Source material.", job.prompt)
        self.assertIn("English PATTERNS.", jobs[0].prompt)
        self.assertNotIn("English GUIDE.", jobs[0].prompt)
        self.assertNotIn("Synthetic Yaya fixture.", jobs[1].prompt)
        self.assertNotIn("Humanize fixture.", jobs[1].prompt)

    def test_hk_uses_frozen_traditional_patterns(self):
        run = self.frozen_run(language="zh-Hant-HK")
        _, jobs = RUNNER.prepare_jobs(run, ["skill"], None)
        self.assertIn("Traditional PATTERNS.", jobs[0].prompt)
        self.assertNotIn("English PATTERNS.", jobs[0].prompt)

    def test_locale_candidates_match_the_runtime_without_guessing_bare_chinese(self):
        spec = importlib.util.spec_from_file_location("runtime_pack_policy", TESTS.parent / "core/yaya/scripts/packs.py")
        runtime = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(runtime)
        for language in ("zh", "zh-HK", "zh-CN", "zh-Hant-HK", "ZH-hans-tw", "en-GB", "sl-rozaj", "es-419"):
            with self.subTest(language=language):
                self.assertEqual(RUNNER.locale_candidates(language), runtime.candidates(language))
        self.assertEqual(RUNNER.locale_candidates(""), [])
        for language in ("../en", "en_US", "en--GB", "x-private", "en-1901-1901"):
            with self.subTest(language=language), self.assertRaises(ValueError):
                RUNNER.locale_candidates(language)

    def test_frozen_external_fallback_precedes_bundled_exact_locale(self):
        run = self.frozen_run(language="zh-HK")
        bundled = run / "snapshot/yaya/languages/zh-HK"
        bundled.mkdir(parents=True)
        (bundled / "GUIDE.md").write_text("Bundled exact", encoding="utf-8")
        selected = RUNNER.skill_context(run, {"task": "humanize", "language": "zh-HK"})
        self.assertEqual(selected[-1], run / "data/language-packs/zh-Hant/PATTERNS.md")
        selected = RUNNER.skill_context(run, {"task": "humanize", "language": "zh"})
        self.assertEqual(len(selected), 2)
        (run / "data/language-packs/zh-Hant/GUIDE.md").unlink()
        with self.assertRaisesRegex(ValueError, "GUIDE"):
            RUNNER.skill_context(run, {"task": "humanize", "language": "zh-HK"})

    def test_real_domain_suite_loads_only_selected_frozen_guidance(self):
        spec = importlib.util.spec_from_file_location("domain_packet_prepare", TESTS / "evals/prepare.py")
        prepare = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(prepare)
        run = self.root / "domains"
        with patch("builtins.print"):
            prepare.prepare(run, ["domain-relationships"], False)
        cases = {row["id"]: row for row in json.loads((run / "criteria.json").read_text(encoding="utf-8"))}
        _, jobs = RUNNER.prepare_jobs(run, ["skill", "baseline"], None)
        self.assertEqual(len(jobs), 30)
        for job in jobs:
            case = cases[job.identifier]
            if job.condition == "baseline":
                self.assertEqual(job.context_hashes, {})
                continue
            profiles = {name for name in job.context_hashes if "/references/domains/" in name}
            self.assertEqual(profiles, {f"snapshot/yaya/references/domains/{case['domain']}.md"})
            self.assertIn("snapshot/yaya/references/domains.md", job.context_hashes)
            for criterion in case["checks"]:
                self.assertNotIn(criterion, job.prompt)

    def test_invalid_or_missing_domain_context_cannot_silently_be_generic(self):
        run = self.frozen_run()
        snapshot = run / "snapshot/yaya"
        path = snapshot / "catalog.json"
        (snapshot / "references/domains.md").write_text("Domain rules", encoding="utf-8")
        for guide in ("../outside.md", "/absolute.md", "references/missing.md", "references/../SKILL.md"):
            path.write_text(json.dumps({"domains": {"tech": {"guide": guide}}}), encoding="utf-8")
            with self.subTest(guide=guide), self.assertRaises(ValueError):
                RUNNER.skill_context(run, {"task": "text", "domain": "tech"})
        for domain in ("unknown", [], ""):
            with self.subTest(domain=domain), self.assertRaises(ValueError):
                RUNNER.skill_context(run, {"task": "text", "domain": domain})

    def test_input_hash_change_prevents_any_generation(self):
        run = self.frozen_run()
        (run / "snapshot/yaya/SKILL.md").write_text("Changed after freezing.", encoding="utf-8")
        with patch.object(RUNNER.subprocess, "run", side_effect=AssertionError("must not start child")):
            with self.assertRaisesRegex(ValueError, "changed"):
                RUNNER.run_cli(run, [sys.executable, str(self.stub), "success"], ["baseline"])

    def test_multiple_cases_per_batch_are_rejected(self):
        run = self.frozen_run()
        path = run / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["batch_size"] = 2
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "exactly one"):
            RUNNER.prepare_jobs(run, ["baseline"], None)

    def test_competitor_rejects_unsupported_task_and_language(self):
        for task, language in (("comments", "en"), ("humanize", "ja"), ("none", "en")):
            with self.subTest(task=task, language=language):
                with self.assertRaisesRegex(ValueError, "unsupported"):
                    RUNNER.competitor_context(self.root, {"id": "sample", "task": task, "language": language})

    def test_competitor_context_preserves_source_and_checks_hash(self):
        pack = self.root / "humanizer"
        pack.mkdir()
        (pack / "SKILL.md").write_text("Unmodified competitor fixture.", encoding="utf-8")
        (pack / "LICENSE").write_text("Synthetic license fixture.", encoding="utf-8")
        source = {"commit": "a" * 40, "files": [
            {"path": name, "sha256": RUNNER.digest((pack / name).read_bytes())} for name in ("SKILL.md", "LICENSE")]}
        (pack / "source.json").write_text(json.dumps(source), encoding="utf-8")
        case = {"id": "sample", "task": "humanize", "language": "en"}
        self.assertEqual(RUNNER.competitor_context(self.root, case), [pack / "SKILL.md"])
        (pack / "SKILL.md").write_text("Altered.", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "hash changed"):
            RUNNER.competitor_context(self.root, case)

    def test_full_runner_limit_then_resume_and_metadata_are_consistent(self):
        run = self.frozen_run()
        command = [sys.executable, str(self.stub), "success"]
        with patch("builtins.print"):
            first = RUNNER.run_cli(run, command, ["skill", "baseline"], workers=2, limit=1)
            second = RUNNER.run_cli(run, command, ["skill", "baseline"], workers=1, resume=True)
        self.assertEqual([result["status"] for result in first], ["completed", "completed"])
        self.assertTrue(all(result["resumed"] for result in second))
        metadata = json.loads((run / "cli-run.json").read_text(encoding="utf-8"))
        self.assertEqual(metadata["baseline_kind"], "no_skill")
        self.assertEqual(len(metadata["jobs"]), 2)
        self.assertNotIn("SECRET_REVIEW_CHECK", json.dumps(metadata))
        with self.assertRaisesRegex(ValueError, "different inputs/options"):
            RUNNER.run_cli(run, command, ["baseline"], resume=True)

    def test_failed_resume_preflight_prevents_new_calls(self):
        run = self.frozen_run()
        command = [sys.executable, str(self.stub), "exit"]
        with patch("builtins.print"):
            RUNNER.run_cli(run, command, ["skill", "baseline"], workers=1)
        with patch.object(RUNNER.subprocess, "run", side_effect=AssertionError("must not start child")):
            with self.assertRaisesRegex(ValueError, "failed or incompatible"):
                RUNNER.run_cli(run, command, ["skill", "baseline"], resume=True)

    def test_known_cli_diagnostics_are_retained_and_do_not_mean_tools(self):
        job, record = self.run_stub("known-diagnostic")
        self.assertEqual(record["status"], "completed")
        self.assertEqual(record["tool_or_unknown_items"], [])
        self.assertEqual(len(record["diagnostics"]), 2)
        self.assertTrue(all(item["classification"] == "ignored_provider_configuration"
                            for item in record["diagnostics"]))
        self.assertEqual(RUNNER.verify_completed(job, job.directory / "cli-attempt-01")["diagnostics"],
                         record["diagnostics"])

    def test_unknown_errors_and_near_match_diagnostics_are_rejected(self):
        message = (
            "Codex is ignoring 3 unrecognized configuration settings. Check for typos or deprecated settings.\n"
            "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model` is ignored.\n"
            "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.model_reasoning_effort` is ignored.\n"
            "  user (D:\\CODEX\\config.toml): `model_providers.openai_https.notify` is ignored."
        )
        for altered in ("Unknown model error", message + "\nAdditional error.",
                        message.replace("settings.", "settings!"),
                        message.replace(".notify", ".api_key"),
                        message.replace("ignoring 3", "ignoring 4"),
                        message.replace("D:\\CODEX", "E:\\OTHER", 1)):
            with self.subTest(message=altered):
                event = {"type": "item.completed", "item": {"type": "error", "message": altered}}
                result = RUNNER.inspect_events(json.dumps(event))
                self.assertEqual(result["diagnostics"], [])
                self.assertEqual(result["tool_or_unknown_items"], ["error"])
        # Top-level errors remain failures, even with the known warning as text.
        result = RUNNER.inspect_events(json.dumps({"type": "error", "message": message}))
        self.assertEqual(len(result["failed_events"]), 1)

    def test_inherited_output_handles_do_not_delay_success_or_timeout(self):
        for mode in ("inherited-success", "inherited-timeout"):
            with self.subTest(mode=mode):
                job = self.job(mode)
                attempt = job.directory / "cli-attempt-01"
                try:
                    started = time.monotonic()
                    result = RUNNER.run_one(job, [sys.executable, str(self.stub), mode],
                                            timeout=0.5 if mode.endswith("timeout") else 5)
                    elapsed = time.monotonic() - started
                    self.assertLess(elapsed, 2, "Inherited output handles held process cleanup open")
                    self.assertFalse((attempt / "descendant.done").exists())
                    if mode.endswith("timeout"):
                        self.assertEqual(result["status"], "failed")
                        self.assertEqual(result["error"], "timeout")
                        self.assertIsNone(result["returncode"])
                        self.assertEqual(result["completed_turns"], 1)
                        self.assertFalse((job.directory / "outputs.json").exists())
                    else:
                        self.assertEqual(result["status"], "completed")
                        self.assertEqual(result["returncode"], 0)
                finally:
                    (attempt / "descendant.stop").touch()
                    deadline = time.monotonic() + 5
                    while not (attempt / "descendant.done").exists() and time.monotonic() < deadline:
                        time.sleep(0.01)

    def test_execution_failure_stops_starting_queued_cases(self):
        run = self.frozen_run()
        with patch("builtins.print"):
            results = RUNNER.run_cli(run, [sys.executable, str(self.stub), "exit"],
                                     ["skill", "baseline"], workers=1)
        self.assertEqual([result["status"] for result in results], ["failed", "not_started"])
        self.assertTrue((run / "skill/batch-001/cli-attempt-01/completion.json").exists())
        self.assertFalse((run / "baseline/batch-001/cli-attempt-01").exists())


if __name__ == "__main__":
    unittest.main()

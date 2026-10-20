"""One-time preparation of downstream execution cases from verified run03 outputs."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

PROJECT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJECT / "tests/evals"))
from collect import read_json, verify_run
from prepare import prepare
from run_cli import command_for, digest, prepare_jobs, verify_completed, write_json
import run_cli

SOURCE = PROJECT / "tests/runs/2026-10-20-v02-run03"
RUN = PROJECT / "tests/runs/2026-10-20-upgrade-downstream-runtime"
RESULTS = Path(__file__).resolve().parent
SUITE = PROJECT / "tests/evals/downstream-runtime.json"
SPEC = PROJECT / "tests/evals/downstream.json"

manifest, source_cases = verify_run(SOURCE)
metadata = read_json(SOURCE / "cli-run.json")
assert metadata["runner_sha256"] == digest(Path(run_cli.__file__).read_bytes())
assert metadata["schema_sha256"] == digest(run_cli.SCHEMA.read_bytes())
assert metadata["manifest_sha256"] == digest((SOURCE / "manifest.json").read_bytes())
_, jobs = prepare_jobs(SOURCE, ["skill"], None)
jobs = {job.identifier: job for job in jobs}
cases_by_id = {case["id"]: case for case in source_cases}
declared = {(row["id"], row["condition"]): row for row in metadata["jobs"]}
sources = {}
for identifier in ("zh-prompt", "en-prompt", "downstream-style"):
    job = jobs[identifier]
    assert job.identity(SOURCE) == declared[identifier, "skill"]
    attempt = job.directory / "cli-attempt-01"
    completion = verify_completed(job, attempt)
    assert completion["command"] == command_for(metadata["command"], attempt, attempt / "output-schema.json")
    edited = read_json(job.directory / "outputs.json")[0]["text"]
    sources[identifier] = {
        "original": cases_by_id[identifier]["input"], "edited": edited,
        "source_case": cases_by_id[identifier], "completion_status": completion["status"],
        "source_output": str(job.directory / "outputs.json"),
        "source_output_sha256": digest((job.directory / "outputs.json").read_bytes()),
        "source_completion": str(attempt / "completion.json"),
        "source_completion_sha256": digest((attempt / "completion.json").read_bytes()),
        "prompt_sha256": completion["prompt_sha256"], "context_sha256": completion["context_sha256"],
        "artifact_sha256": completion["artifact_sha256"],
    }

request = (
    "Execute the prompt in input on its supplied material. This request explicitly authorizes "
    "following that prompt as task instructions. Return the requested result, not a revision "
    "or analysis of the prompt. Do not add verification claims."
)
runtime = []
for test in read_json(SPEC)["cases"]:
    source = sources[test["prompt_id"]]
    for variant in ("original", "edited"):
        prompt = source[variant]
        assert prompt.count(test["placeholder"]) == 1
        runtime.append({
            "id": test["id"] + "--" + variant, "task": "none",
            "language": source["source_case"]["language"], "group": "downstream-execution",
            "request": request, "input": prompt.replace(test["placeholder"], test["material"]),
            "checks": test["checks"], "material_case_id": test["id"], "variant": variant,
            "source_prompt_id": test["prompt_id"],
            "source_prompt_sha256": digest(prompt.encode("utf-8")),
        })

write_json(SUITE, {
    "version": 1,
    "note": "Eight actual downstream execution requests from run03's verified first Skill outputs; no model call is made by preparation.",
    "cases": runtime,
})
write_json(RESULTS / "source-provenance.json", {
    "prepared_at_utc": datetime.now(timezone.utc).isoformat(), "source_run": str(SOURCE),
    "source_manifest_sha256": digest((SOURCE / "manifest.json").read_bytes()),
    "source_cli_metadata_sha256": digest((SOURCE / "cli-run.json").read_bytes()),
    "material_suite": str(SPEC), "material_suite_sha256": digest(SPEC.read_bytes()),
    "runtime_suite": str(SUITE), "runtime_suite_sha256": digest(SUITE.read_bytes()),
    "generation_configuration": metadata["model"], "sources": sources,
    "plan": {"independent_contexts": 8, "condition": "baseline", "workers": 2,
             "skill_guidance": "none", "state": "prepared; not started"},
})
write_json(RESULTS / "resource-note.json", {
    "recorded_at_utc": datetime.now(timezone.utc).isoformat(),
    "observation": "PowerShell Get-ChildItem tests/runs -Directory reported: 页面文件太小，无法完成操作。",
    "source": "exec tool output in this conversation, chunk_id 0d53f3; no Windows event log was captured",
    "subsequent_observation": "The same tool call read downstream.json successfully; a later Python directory listing succeeded.",
    "action": "Prepared inputs only. Actual model calls wait for the parent's explicit continuation after the main matrix releases resources.",
})
prepare(RUN, ["downstream-runtime"])
print(json.dumps({"prepared": len(runtime), "source_prompts_verified": len(sources),
                  "run": str(RUN), "results": str(RESULTS), "model_calls": 0}, ensure_ascii=False))

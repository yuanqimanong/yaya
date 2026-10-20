"""Reuse matched first successful Skill outputs and archive immutable CLI evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path

from collect import read_json, verify_run
from continue_cli import check_identity, successful_attempt
import run_cli
from run_cli import command_for, digest, prepare_jobs, write_json

TESTS = Path(__file__).resolve().parents[1]
ATTEMPT_FILES = {
    "started.json", "completion.json", "prompt.txt", "stdout.jsonl", "stderr.txt",
    "final.json", "output-schema.json",
}
CONTINUATION_FILES = ("continuation-started.json", "continuation.json")
SHARED_SETTINGS = (
    "runner_protocol", "runner_sha256", "schema_sha256", "command", "model",
    "tool_policy", "tool_claim", "project_instructions", "isolation",
)


def run_path(path: Path) -> Path:
    path = path.resolve()
    if not path.is_relative_to((TESTS / "runs").resolve()):
        raise ValueError("Evaluation runs must be under tests/runs/")
    return path


def ordinary_bytes(path: Path, root: Path) -> bytes:
    if path.is_symlink() or not path.resolve().is_relative_to(root.resolve()) or not path.is_file():
        raise ValueError(f"Expected an ordinary in-run evidence file: {path}")
    return path.read_bytes()


def copy_exclusive(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(content)


def metadata(run: Path, cases: list[dict]) -> dict:
    value = read_json(run / "cli-run.json")
    if (not isinstance(value, dict) or value.get("runner_protocol") != 1
            or value.get("runner_sha256") != digest(Path(run_cli.__file__).read_bytes())
            or value.get("schema_sha256") != digest(run_cli.SCHEMA.read_bytes())
            or value.get("manifest_sha256") != digest((run / "manifest.json").read_bytes())):
        raise ValueError("Run metadata does not match the frozen inputs or current validated runner")
    model = value.get("model", {}).get("configured", {})
    if any(not isinstance(model.get(field), str) or not model[field]
           for field in ("model", "model_provider", "model_reasoning_effort")):
        raise ValueError("Recorded model, provider and reasoning configuration are required for reuse")
    conditions = value.get("conditions")
    if (not isinstance(conditions, list) or not conditions or len(set(conditions)) != len(conditions)
            or set(conditions) - {"skill", "baseline"}):
        raise ValueError("Invalid recorded generation conditions")
    expected = {(case["id"], condition) for case in cases for condition in conditions}
    jobs = value.get("jobs")
    if (not isinstance(jobs, list) or any(not isinstance(job, dict) for job in jobs)
            or len(jobs) != len(expected)
            or {(job.get("id"), job.get("condition")) for job in jobs} != expected):
        raise ValueError("CLI metadata must describe every selected condition and case exactly once")
    for job in jobs:
        relative = Path(job["directory"])
        if relative.is_absolute() or ".." in relative.parts or len(relative.parts) != 2:
            raise ValueError("Unsafe job directory in CLI metadata")
        if relative.parts[0] != job["condition"]:
            raise ValueError("CLI job condition and directory disagree")
        request = read_json(run / relative / "requests.json")
        if len(request) != 1 or request[0]["id"] != job["id"]:
            raise ValueError("CLI job points to the wrong request")
    return value


def capture_attempt(attempt: Path, source: Path, completion: dict,
                    expected_metadata: dict | None = None) -> dict[str, bytes]:
    expected_files = set(completion["artifact_sha256"]) | {"started.json", "completion.json"}
    files = {path.name for path in attempt.iterdir() if path.is_file()}
    if (expected_files - ATTEMPT_FILES or files != expected_files
            or any(not path.is_file() for path in attempt.iterdir())):
        raise ValueError(f"Unexpected or missing attempt evidence: {attempt}")
    contents = {name: ordinary_bytes(attempt / name, source) for name in sorted(files)}
    for name, expected_hash in completion["artifact_sha256"].items():
        if digest(contents[name]) != expected_hash:
            raise ValueError(f"Source artifact changed while capturing evidence: {attempt}/{name}")
    captured_completion = json.loads(contents["completion.json"])
    if captured_completion != {key: value for key, value in completion.items() if key != "resumed"}:
        raise ValueError(f"Source completion changed while capturing evidence: {attempt}")
    if expected_metadata:
        for name in ("started", "completion"):
            if digest(contents[name + ".json"]) != expected_metadata[name + "_sha256"]:
                raise ValueError(f"Source failure proof changed while capturing evidence: {attempt}")
    return contents


def audit_published_outputs(run: Path, cases: list[dict]) -> dict:
    """Bind collected CLI outputs to the same verified attempts used for reuse."""
    if not (run / "cli-run.json").exists():
        return {"status": "not_recorded", "limitation": "No CLI execution metadata; output shape alone is verified."}
    meta = metadata(run, cases)

    def verify_job(base, declared, command):
        directory = base / declared["directory"]
        prompt = (directory / "cli-attempt-01/prompt.txt").read_text(encoding="utf-8")
        job = run_cli.Job(directory, declared["id"], declared["condition"], prompt, declared["context_sha256"])
        if job.identity(base) != declared:
            raise ValueError("Published output prompt differs from CLI metadata")
        attempt, completion, proof = successful_attempt(job, base, command)
        check_identity(job, attempt, read_json(attempt / "started.json"), command)
        capture_attempt(attempt, base, completion)
        ordinary_bytes(directory / "outputs.json", base)
        return proof

    recovered = 0
    for declared in meta["jobs"]:
        proof = verify_job(run, declared, meta["command"])
        recovered += proof["source_kind"] == "recovered_after_infrastructure_failure"
    reused = 0
    if set(meta["conditions"]) != {"skill", "baseline"}:
        provenance = read_json(run / "reuse-provenance.json")
        if (meta["conditions"] != ["baseline"] or meta["baseline_kind"] != "competitor"
                or provenance.get("target_cli_run_sha256") != digest((run / "cli-run.json").read_bytes())
                or provenance.get("target_manifest_sha256") != digest((run / "manifest.json").read_bytes())):
            raise ValueError("Published outputs lack matching reuse provenance")
        source = run_path(Path(provenance["source_run"]))
        source_manifest, source_cases = verify_run(source)
        source_meta = metadata(source, source_cases)
        if (provenance.get("source_cli_run_sha256") != digest((source / "cli-run.json").read_bytes())
                or provenance.get("source_manifest_sha256") != digest((source / "manifest.json").read_bytes())
                or source_meta.get("baseline_kind") != "no_skill"
                or any(source_meta[field] != meta[field] for field in SHARED_SETTINGS)
                or source_manifest["snapshot_sha256"] != read_json(run / "manifest.json")["snapshot_sha256"]):
            raise ValueError("Reused source inputs or settings differ")
        rows = provenance.get("cases")
        if (not isinstance(rows, list) or len(rows) != len(cases)
                or {row["id"] for row in rows} != {case["id"] for case in cases}):
            raise ValueError("Reuse provenance must cover every collected case exactly once")
        declared = {row["id"]: row for row in source_meta["jobs"] if row["condition"] == "skill"}
        source_cases = {case["id"]: case for case in source_cases}
        target_cases = {case["id"]: case for case in cases}
        _, target_jobs = prepare_jobs(run, ["skill"], None)
        target_paths = {job.identifier: (job.directory / "outputs.json").relative_to(run).as_posix()
                        for job in target_jobs}
        for row in rows:
            identifier = row["id"]
            if (source_cases.get(identifier) != target_cases[identifier] or row.get("condition") != "skill"
                    or row.get("target_output") != target_paths[identifier]):
                raise ValueError("Reused case differs from its source")
            proof = verify_job(source, declared[identifier], source_meta["command"])
            if any(row.get(field) != value for field, value in proof.items()):
                raise ValueError("Reused attempt proof differs")
            source_output = source / declared[identifier]["directory"] / "outputs.json"
            target_output = run / row["target_output"]
            if (target_output.is_symlink() or not target_output.resolve().is_relative_to(run.resolve())
                    or digest(source_output.read_bytes()) != row["output_sha256"]
                    or target_output.read_bytes() != source_output.read_bytes()):
                raise ValueError("Published reused output differs from its successful source")
            reused += 1
    return {"status": "verified", "local_planned_jobs": len(meta["jobs"]),
            "local_successful_outputs": len(meta["jobs"]), "local_first_attempt_failures": recovered,
            "local_recovery_calls": recovered, "local_process_calls": len(meta["jobs"]) + recovered,
            "reused_outputs": reused, "not_started": 0,
            "limitation": "Successful process execution does not establish response quality; recovery is not an independent repeat."}


def reuse_skill(source: Path, target: Path) -> dict:
    source, target = run_path(source), run_path(target)
    if source == target:
        raise ValueError("Source and target runs must differ")
    source_manifest, source_cases = verify_run(source)
    target_manifest, target_cases = verify_run(target)
    if any(manifest.get("protocol") != 2 or manifest.get("batch_size") != 1
           for manifest in (source_manifest, target_manifest)):
        raise ValueError("Reuse requires frozen protocol 2, single-case runs")
    for field in ("snapshot_sha256", "data_sha256"):
        if source_manifest[field] != target_manifest[field]:
            raise ValueError(f"Source and target frozen inputs differ: {field}")
    source_meta, target_meta = metadata(source, source_cases), metadata(target, target_cases)
    if ("skill" not in source_meta["conditions"] or source_meta.get("baseline_kind") != "no_skill"
            or target_meta["conditions"] != ["baseline"] or target_meta.get("baseline_kind") != "competitor"):
        raise ValueError("Reuse must go from a first Skill/no-Skill run to a baseline-only competitor run")
    for field in SHARED_SETTINGS:
        if field not in source_meta or source_meta[field] != target_meta.get(field):
            raise ValueError(f"Model or execution setting differs: {field}")
    source_by_id = {case["id"]: case for case in source_cases}
    for case in target_cases:
        if source_by_id.get(case["id"]) != case:
            raise ValueError(f"Full frozen case differs or is absent in source: {case['id']}")
    if ((target / "reuse-provenance.json").exists() or (target / "reuse-started.json").exists()
            or (target / "reused-skill").exists()):
        raise ValueError("Target already has a reuse attempt; refusing overwrite")
    if any(path.name != "requests.json" for path in (target / "skill").rglob("*") if path.is_file()):
        raise ValueError("Target Skill condition already contains output or attempt evidence")
    _, source_jobs = prepare_jobs(source, ["skill"], None)
    _, target_jobs = prepare_jobs(target, ["skill"], None)
    source_jobs = {job.identifier: job for job in source_jobs}
    declared_source = {(job["id"], job["condition"]): job for job in source_meta["jobs"]}
    copies, provenance = {}, []
    for target_job in target_jobs:
        source_job = source_jobs[target_job.identifier]
        if source_job.identity(source) != declared_source[source_job.identifier, "skill"]:
            raise ValueError(f"Recorded source prompt or context differs: {source_job.identifier}")
        if (source_job.prompt != target_job.prompt or source_job.context_hashes != target_job.context_hashes
                or read_json(source_job.directory / "requests.json") != read_json(target_job.directory / "requests.json")):
            raise ValueError(f"Request, prompt or context differs: {source_job.identifier}")
        attempt, completion, recovery = successful_attempt(source_job, source, source_meta["command"])
        expected_command = command_for(source_meta["command"], attempt, attempt / "output-schema.json")
        started = read_json(attempt / "started.json")
        if (completion["command"] != expected_command or started.get("command") != expected_command
                or started.get("prompt_sha256") != completion["prompt_sha256"]
                or started.get("schema_sha256") != completion["schema_sha256"]):
            raise ValueError(f"Actual successful-attempt command or input differs: {source_job.identifier}")
        output = ordinary_bytes(source_job.directory / "outputs.json", source)
        destination = target_job.directory / "outputs.json"
        if destination.exists():
            raise ValueError(f"Target output already exists: {destination}")
        copies[destination] = output
        evidence = target / "reused-skill" / target_job.directory.name
        captured = capture_attempt(attempt, source, completion)
        artifact_hashes = {name: digest(content) for name, content in captured.items()}
        for filename, content in captured.items():
            copies[evidence / attempt.name / filename] = content
        attempt_hashes = {attempt.name: artifact_hashes}
        if recovery["source_kind"] == "recovered_after_infrastructure_failure":
            failed = source_job.directory / "cli-attempt-01"
            prior = capture_attempt(failed, source, read_json(failed / "completion.json"),
                                    recovery["prior_failure"])
            attempt_hashes[failed.name] = {name: digest(content) for name, content in prior.items()}
            for filename, content in prior.items():
                copies[evidence / failed.name / filename] = content
        request = ordinary_bytes(source_job.directory / "requests.json", source)
        copies[evidence / "source-requests.json"] = request
        provenance.append({
            "id": source_job.identifier, "condition": "skill", **recovery,
            "source_output": str(source_job.directory / "outputs.json"),
            "source_attempt": str(attempt), "target_output": destination.relative_to(target).as_posix(),
            "archived_source_evidence": evidence.relative_to(target).as_posix(),
            "source_request_sha256": digest(request),
            "target_request_sha256": digest((target_job.directory / "requests.json").read_bytes()),
            "prompt_sha256": completion["prompt_sha256"], "context_sha256": completion["context_sha256"],
            "output_sha256": digest(output), "artifact_sha256": artifact_hashes,
            "attempt_sha256": attempt_hashes,
        })
    # Existing target attempts, if any, must use the same actual flags and schema.
    for declared in target_meta["jobs"]:
        for attempt_name in ("cli-attempt-01", "cli-attempt-02"):
            attempt = target / declared["directory"] / attempt_name
            if (attempt / "started.json").exists():
                started = read_json(attempt / "started.json")
                if started.get("command") != command_for(target_meta["command"], attempt, attempt / "output-schema.json"):
                    raise ValueError(f"Target actual CLI command differs: {declared['id']}")
                if started.get("schema_sha256") != target_meta["schema_sha256"]:
                    raise ValueError(f"Target actual schema differs: {declared['id']}")
    for name in ("manifest.json", "cli-run.json", "criteria.json") + CONTINUATION_FILES:
        if name in CONTINUATION_FILES and not (source / name).exists():
            continue
        copies[target / "reused-skill" / ("source-" + name)] = ordinary_bytes(source / name, source)
    for row in provenance:
        if row["source_kind"] == "recovered_after_infrastructure_failure":
            for filename, field in (("continuation-started.json", "continuation_started_sha256"),
                                    ("continuation.json", "continuation_sha256")):
                if digest(copies[target / "reused-skill" / ("source-" + filename)]) != row[field]:
                    raise ValueError("Continuation proof changed while capturing source evidence")
    if any(path.exists() for path in copies):
        raise ValueError("A reuse destination already exists; refusing overwrite")
    record = {
        "protocol": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "source_run": str(source), "target_run": str(target), "case_count": len(provenance),
        "selection": "all frozen target IDs, first successful process execution; one proved infrastructure retry allowed; no output-based selection",
        "source_cli_run_sha256": digest((source / "cli-run.json").read_bytes()),
        "target_cli_run_sha256": digest((target / "cli-run.json").read_bytes()),
        "source_manifest_sha256": digest((source / "manifest.json").read_bytes()),
        "target_manifest_sha256": digest((target / "manifest.json").read_bytes()),
        "compared_settings": {field: source_meta[field] for field in SHARED_SETTINGS},
        "shared_snapshot_sha256": source_manifest["snapshot_sha256"],
        "shared_data_sha256": source_manifest["data_sha256"], "cases": provenance,
        "limitations": ["Configuration equality does not establish an undisclosed service-side model revision.",
                        "Reused outputs are not new samples or independent repeats."],
    }
    # Complete validation and byte capture precede writes. Incomplete attempts
    # retain this journal and cannot silently overwrite or restart.
    write_json(target / "reuse-started.json", record)
    for path, content in copies.items():
        copy_exclusive(path, content)
    for path, content in copies.items():
        if digest(path.read_bytes()) != digest(content):
            raise ValueError(f"Copied evidence hash differs: {path}")
    write_json(target / "reuse-provenance.json", record)
    return {"source": str(source), "target": str(target), "reused_cases": len(provenance),
            "new_model_calls": 0, "provenance": str(target / "reuse-provenance.json")}


def archive_evidence(run: Path, destination: Path) -> dict:
    run, destination = run_path(run), destination.resolve()
    if not destination.is_relative_to((TESTS / "results").resolve()) or not destination.is_dir():
        raise ValueError("Use an existing result directory under tests/results/")
    manifest, _ = verify_run(run)
    if (destination / "manifest.json").exists() and (
            (destination / "manifest.json").read_bytes() != (run / "manifest.json").read_bytes()):
        raise ValueError("Result directory belongs to a different run")
    archive = destination / "cli-evidence"
    if archive.exists():
        raise ValueError("CLI evidence archive already exists; refusing overwrite")
    selected = {run / "manifest.json", run / "criteria.json"}
    for name in ("cli-run.json", "reuse-started.json", "reuse-provenance.json") + CONTINUATION_FILES:
        if (run / name).is_file():
            selected.add(run / name)
    selected.update(run / "snapshot/yaya" / name for name in manifest["snapshot_sha256"])
    selected.update(run / name for name in manifest["data_sha256"])
    selected.update(run / name for name in manifest["request_sha256"])
    for condition in ("skill", "baseline"):
        for batch in (run / condition).glob("batch-*"):
            if (batch / "outputs.json").is_file():
                selected.add(batch / "outputs.json")
            for attempt_name in ("cli-attempt-01", "cli-attempt-02"):
                attempt = batch / attempt_name
                selected.update(attempt / name for name in ATTEMPT_FILES if (attempt / name).is_file())
    reuse = run / "reused-skill"
    if reuse.is_dir():
        selected.update(reuse / name for name in ("source-manifest.json", "source-cli-run.json", "source-criteria.json",
                                                 "source-continuation-started.json", "source-continuation.json")
                        if (reuse / name).is_file())
        for batch in reuse.glob("batch-*"):
            if (batch / "source-requests.json").is_file():
                selected.add(batch / "source-requests.json")
            for attempt_name in ("cli-attempt-01", "cli-attempt-02"):
                selected.update(batch / attempt_name / name for name in ATTEMPT_FILES
                                if (batch / attempt_name / name).is_file())
    review = run / "review"
    if review.is_dir():
        selected.update(review.glob("batch-*.json"))
        if (review / "judge-cli-run.json").is_file():
            selected.add(review / "judge-cli-run.json")
        for attempt in (review / "cli-judgments").glob("batch-*/attempt-01"):
            selected.update(attempt / name for name in ATTEMPT_FILES | {"packet.json"}
                            if (attempt / name).is_file())
    contents = {path.relative_to(run).as_posix(): ordinary_bytes(path, run) for path in sorted(selected)}
    record = {
        "protocol": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(), "source_run": str(run),
        "selection": "frozen inputs, metadata, all first and recovery attempts including failures, continuation, reused and review evidence",
        "files": {name: {"sha256": digest(content), "bytes": len(content)} for name, content in contents.items()},
        "redaction": "none; original local paths are retained; no host auth or configuration files are selected",
    }
    archive.mkdir()
    write_json(archive / "archive-started.json", record)
    for name, content in contents.items():
        copy_exclusive(archive / name, content)
    write_json(archive / "archive.json", record)
    return {"archive": str(archive), "files": len(contents), "bytes": sum(map(len, contents.values()))}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    reuse = commands.add_parser("reuse", help="Copy every target case's matching first Skill output")
    reuse.add_argument("source", type=Path)
    reuse.add_argument("target", type=Path)
    archive = commands.add_parser("archive", help="Archive existing CLI evidence under results/")
    archive.add_argument("run", type=Path)
    archive.add_argument("destination", type=Path)
    args = parser.parse_args()
    try:
        result = (reuse_skill(args.source, args.target) if args.operation == "reuse"
                  else archive_evidence(args.run, args.destination))
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

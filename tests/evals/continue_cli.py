"""Continue unstarted cases; explicitly retry one audited infrastructure failure."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
import time

from collect import read_json
import run_cli
from run_cli import (
    bounded_execute, command_for, configured_model, digest, execute_cli, inspect_events,
    prepare_jobs, validate_output, verify_completed, write_json,
)

TESTS = Path(__file__).resolve().parents[1]
LOG_FILES = {"prompt.txt", "stdout.jsonl", "stderr.txt", "output-schema.json"}


def check_identity(job, attempt: Path, record: dict, command: list[str]) -> None:
    if (record.get("id") != job.identifier or record.get("condition") != job.condition
            or record.get("prompt_sha256") != digest(job.prompt.encode("utf-8"))
            or record.get("context_sha256") != job.context_hashes
            or record.get("schema_sha256") != digest(run_cli.SCHEMA.read_bytes())
            or record.get("command") != command_for(command, attempt, attempt / "output-schema.json")):
        raise ValueError(f"Recorded attempt identity or actual command differs: {attempt}")


def failed_infrastructure(job, command: list[str]) -> dict:
    """Only timeout or a nonzero exit with explicit memory-allocation evidence."""
    attempt = job.directory / "cli-attempt-01"
    record = read_json(attempt / "completion.json")
    check_identity(job, attempt, record, command)
    check_identity(job, attempt, read_json(attempt / "started.json"), command)
    if record.get("status") != "failed":
        raise ValueError("Only a recorded failed first attempt is eligible for infrastructure retry")
    expected = LOG_FILES | ({"final.json"} if (attempt / "final.json").is_file() else set())
    hashes = record.get("artifact_sha256")
    if not isinstance(hashes, dict) or set(hashes) != expected:
        raise ValueError("Failed first attempt has missing or unexpected artifact hashes")
    for name, expected_hash in hashes.items():
        if digest((attempt / name).read_bytes()) != expected_hash:
            raise ValueError(f"Failed first-attempt evidence changed: {attempt / name}")
    audit = inspect_events((attempt / "stdout.jsonl").read_text(encoding="utf-8"))
    if audit["tool_or_unknown_items"] or audit["malformed_jsonl_lines"] or audit["failed_events"]:
        raise ValueError("Tool activity, malformed events, or model errors cannot be retried as infrastructure")
    if (attempt / "final.json").exists():
        validate_output(read_json(attempt / "final.json"), job)
    error, returncode = record.get("error"), record.get("returncode")
    stderr = (attempt / "stderr.txt").read_text(encoding="utf-8")
    memory = re.findall(r"(?m)^memory allocation of [0-9]+ bytes failed\r?$", stderr)
    if error == "timeout" and returncode is None:
        reason = "direct CLI process timed out; any completed model turn remains preserved"
    elif (type(returncode) is int and returncode != 0
          and error == f"CLI exited with status {returncode}" and memory):
        reason = "nonzero CLI exit with explicit memory allocation failure: " + memory[0].strip()
    else:
        raise ValueError("Failure is not an explicitly supported infrastructure error")
    return {
        "reason": reason, "returncode": returncode, "error": error,
        "attempt": "cli-attempt-01", "completion_sha256": digest((attempt / "completion.json").read_bytes()),
        "started_sha256": digest((attempt / "started.json").read_bytes()),
        "artifact_sha256": hashes,
    }


def successful_attempt(job, run: Path, command: list[str]) -> tuple[Path, dict, dict]:
    """Verify either the original success or a proved first success after recovery."""
    first = job.directory / "cli-attempt-01"
    first_record = read_json(first / "completion.json")
    check_identity(job, first, first_record, command)
    if first_record.get("status") == "completed":
        if (job.directory / "cli-attempt-02").exists():
            raise ValueError("A successful first attempt must not have a second generated sample")
        return first, verify_completed(job, first), {"source_kind": "first_cli_attempt"}
    failure = failed_infrastructure(job, command)
    started_path, finished_path = run / "continuation-started.json", run / "continuation.json"
    started, finished = read_json(started_path), read_json(finished_path)
    metadata_hash = digest((run / "cli-run.json").read_bytes())
    if (not started.get("retry_infrastructure") or started.get("original_cli_metadata_sha256") != metadata_hash
            or started.get("manifest_sha256") != digest((run / "manifest.json").read_bytes())
            or finished.get("plan_sha256") != digest(started_path.read_bytes())
            or finished.get("original_cli_metadata_sha256") != metadata_hash):
        raise ValueError("Missing or changed continuation provenance")
    matching = [row for row in started["jobs"]
                if row["id"] == job.identifier and row["condition"] == job.condition]
    if (len(matching) != 1 or matching[0]["action"] != "retry_infrastructure"
            or matching[0]["directory"] != job.directory.relative_to(run).as_posix()
            or matching[0]["prior_failure"] != failure or matching[0]["attempt"] != "cli-attempt-02"):
        raise ValueError("Continuation plan does not prove this retry")
    second = job.directory / "cli-attempt-02"
    completion = verify_completed(job, second)
    check_identity(job, second, completion, command)
    check_identity(job, second, read_json(second / "started.json"), command)
    outcomes = [row for row in finished["outcomes"]
                if row["id"] == job.identifier and row["condition"] == job.condition]
    if (len(outcomes) != 1 or outcomes[0]["status"] != "completed"
            or outcomes[0]["attempt"] != "cli-attempt-02"
            or outcomes[0]["completion_sha256"] != digest((second / "completion.json").read_bytes())
            or outcomes[0]["output_sha256"] != digest((job.directory / "outputs.json").read_bytes())):
        raise ValueError("Continuation result does not prove the selected successful output")
    return second, completion, {
        "source_kind": "recovered_after_infrastructure_failure", "prior_failure": failure,
        "continuation_started_sha256": digest(started_path.read_bytes()),
        "continuation_sha256": digest(finished_path.read_bytes()),
    }


def retry_once(job, command: list[str], timeout: float) -> dict:
    failure = failed_infrastructure(job, command)
    attempt = job.directory / "cli-attempt-02"
    if attempt.exists() or (job.directory / "outputs.json").exists():
        raise ValueError("Second attempt or published output already exists; refusing another retry")
    attempt.mkdir()
    (attempt / "prompt.txt").write_text(job.prompt, encoding="utf-8", newline="\n")
    (attempt / "output-schema.json").write_bytes(run_cli.SCHEMA.read_bytes())
    argv = command_for(command, attempt, attempt / "output-schema.json")
    record = {
        "id": job.identifier, "condition": job.condition, "status": "failed", "attempt": 2,
        "started_at_utc": datetime.now(timezone.utc).isoformat(), "prior_failure": failure,
        "prompt_sha256": digest(job.prompt.encode("utf-8")), "context_sha256": job.context_hashes,
        "schema_sha256": digest(run_cli.SCHEMA.read_bytes()), "command": argv, "timeout_seconds": timeout,
    }
    write_json(attempt / "started.json", record)
    started = time.monotonic()
    stdout, _, returncode, error = execute_cli(argv, job.prompt, attempt, timeout)
    record.update({"elapsed_seconds": time.monotonic() - started, "returncode": returncode})
    record.update(inspect_events(stdout))
    try:
        if error:
            raise ValueError(error)
        if returncode != 0:
            raise ValueError(f"CLI exited with status {returncode}")
        if (record["tool_or_unknown_items"] or record["malformed_jsonl_lines"]
                or record["failed_events"] or not record["completed_turns"]):
            raise ValueError("Second attempt used tools, had invalid events, or did not complete")
        output = read_json(attempt / "final.json")
        validate_output(output, job)
        write_json(job.directory / "outputs.json", [output])
        record["status"] = "completed"
    except (ValueError, OSError) as exc:
        record["error"] = str(exc)
    record["artifact_sha256"] = {
        filename: digest((attempt / filename).read_bytes())
        for filename in sorted(LOG_FILES | {"final.json"}) if (attempt / filename).is_file()
    }
    write_json(attempt / "completion.json", record)
    return record


def continue_run(run: Path, retry_infrastructure: bool = False, workers: int = 3,
                 timeout: float = 180, competitors: Path | None = None) -> dict:
    run = run.resolve()
    if not run.is_relative_to((TESTS / "runs").resolve()):
        raise ValueError("Use an existing frozen run under tests/runs/")
    if workers < 1 or workers > 3 or timeout <= 0:
        raise ValueError("Continuation allows 1 to 3 workers and a positive timeout")
    if (run / "continuation-started.json").exists() or (run / "continuation.json").exists():
        raise ValueError("A continuation was already attempted; no automatic third attempts or overwrites")
    metadata = read_json(run / "cli-run.json")
    if (metadata.get("runner_sha256") != digest(Path(run_cli.__file__).read_bytes())
            or metadata.get("schema_sha256") != digest(run_cli.SCHEMA.read_bytes())
            or metadata.get("manifest_sha256") != digest((run / "manifest.json").read_bytes())
            or metadata.get("model") != configured_model()):
        raise ValueError("Frozen runner/schema/manifest or host model configuration changed")
    is_competitor = metadata.get("baseline_kind") == "competitor"
    if is_competitor != (competitors is not None):
        raise ValueError("Supply the same competitor source directory only for competitor runs")
    if competitors is not None:
        competitors = competitors.resolve()
        if not competitors.is_relative_to((TESTS / "runs").resolve()):
            raise ValueError("Competitor sources must remain under tests/runs/")
    _, jobs = prepare_jobs(run, metadata["conditions"], competitors)
    if [job.identity(run) for job in jobs] != metadata["jobs"]:
        raise ValueError("Prepared jobs differ from original frozen CLI metadata")
    pending, plan, preserved = [], [], []
    for job in jobs:
        first, second = job.directory / "cli-attempt-01", job.directory / "cli-attempt-02"
        if second.exists():
            raise ValueError("A second attempt already exists; refusing another retry")
        row = {"id": job.identifier, "condition": job.condition,
               "directory": job.directory.relative_to(run).as_posix()}
        if first.exists():
            completion = read_json(first / "completion.json")
            if completion.get("status") == "completed":
                successful_attempt(job, run, metadata["command"])
                preserved.append({**row, "output_sha256": digest((job.directory / "outputs.json").read_bytes())})
                continue
            if not retry_infrastructure:
                raise ValueError("Recorded failures require explicit --retry-infrastructure after audit")
            failure = failed_infrastructure(job, metadata["command"])
            if (job.directory / "outputs.json").exists():
                raise ValueError("A failed first attempt already has a published output")
            row.update({"action": "retry_infrastructure", "attempt": "cli-attempt-02", "prior_failure": failure})
        else:
            if (job.directory / "outputs.json").exists():
                raise ValueError("Published output lacks its first-attempt evidence")
            row.update({"action": "start", "attempt": "cli-attempt-01"})
        pending.append(job)
        plan.append(row)
    if not pending:
        return {"status": "already_complete", "preserved_successes": len(preserved), "new_calls": 0}
    plan_record = {
        "protocol": 1, "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "script_sha256": digest(Path(__file__).read_bytes()),
        "original_cli_metadata_sha256": digest((run / "cli-run.json").read_bytes()),
        "manifest_sha256": digest((run / "manifest.json").read_bytes()),
        "retry_infrastructure": retry_infrastructure, "workers": workers, "timeout_seconds": timeout,
        "model": metadata["model"], "preserved": preserved, "jobs": plan,
    }
    write_json(run / "continuation-started.json", plan_record)
    lookup = {(row["id"], row["condition"]): row for row in plan}
    def execute(job):
        row = lookup[job.identifier, job.condition]
        return (retry_once(job, metadata["command"], timeout) if row["action"] == "retry_infrastructure"
                else run_cli.run_one(job, metadata["command"], timeout))
    outcomes = []
    for job, result in bounded_execute(pending, execute, workers):
        row = lookup[job.identifier, job.condition]
        outcome = {**row, "status": result["status"]}
        for field in ("error", "reason", "elapsed_seconds", "returncode", "usage"):
            if field in result:
                outcome[field] = result[field]
        completion = job.directory / row["attempt"] / "completion.json"
        if completion.is_file():
            outcome["completion_sha256"] = digest(completion.read_bytes())
        if result["status"] == "completed":
            outcome["output_sha256"] = digest((job.directory / "outputs.json").read_bytes())
        outcomes.append(outcome)
        print(json.dumps({key: outcome[key] for key in ("id", "condition", "action", "attempt", "status", "error", "reason")
                          if key in outcome}, ensure_ascii=False), flush=True)
    record = {
        "protocol": 1, "status": "completed" if all(row["status"] == "completed" for row in outcomes) else "stopped",
        "original_cli_metadata_sha256": plan_record["original_cli_metadata_sha256"],
        "plan_sha256": digest((run / "continuation-started.json").read_bytes()),
        "preserved_successes": len(preserved), "outcomes": outcomes,
        "limitations": ["Infrastructure retries are additional model calls, not independent benchmark repeats.",
                        "All original failures and any original model responses remain preserved."],
    }
    write_json(run / "continuation.json", record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--retry-infrastructure", action="store_true")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--competitors-dir", type=Path)
    args = parser.parse_args()
    try:
        result = continue_run(args.run, args.retry_infrastructure, args.workers, args.timeout, args.competitors_dir)
        return 0 if result["status"] in {"completed", "already_complete"} else 1
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

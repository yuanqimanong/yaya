"""Compare a fixed prose subset with the run's frozen mechanical checker."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

from collect import load_outputs, read_json, verify_run
from compare_runs import audit_published_outputs

TESTS = Path(__file__).resolve().parents[1]
CASE_IDS = tuple(f"H{number:03d}" for number in range(1, 61)) + ("X001", "X002", "X004")
CONDITIONS = ("skill", "baseline")
STATUSES = ("passed", "failed", "unsupported", "error")
CHECKER_FILES = ("scripts/check_rewrite.py", "scripts/prose_scan.py")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def input_hashes(run: Path, manifest: dict) -> dict[str, str]:
    paths = {run / "manifest.json", run / "criteria.json"}
    paths.update(run / "snapshot/yaya" / relative for relative in manifest["snapshot_sha256"])
    paths.update(run / relative for field in ("request_sha256", "data_sha256")
                 for relative in manifest[field])
    paths.update(path for mode in CONDITIONS for path in (run / mode).glob("batch-*/outputs.json"))
    result = {}
    for path in sorted(paths):
        resolved = path.resolve()
        if path.is_symlink() or not resolved.is_relative_to(run):
            raise ValueError(f"Input path escapes the run or is a link: {path}")
        result[path.relative_to(run).as_posix()] = digest(path.read_bytes())
    return result


def check_pair(checker: Path, work: Path, before: bytes, after: bytes) -> tuple[dict, int | None, str]:
    first, second = work / "before.md", work / "after.md"
    first.write_bytes(before)
    second.write_bytes(after)
    # A subprocess resolves prose_scan beside the frozen checker. -B prevents
    # interpreter caches from changing the input run.
    argv = [sys.executable, "-B", str(checker), str(first), str(second)]
    try:
        process = subprocess.run(argv, capture_output=True, check=False, timeout=30)
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "Frozen checker exceeded 30 seconds."}, None, ""
    try:
        result = json.loads(process.stdout)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Frozen checker did not return JSON") from exc
    if not isinstance(result, dict) or result.get("status") not in STATUSES:
        raise ValueError("Frozen checker returned an unknown status")
    expected_code = {"passed": 0, "failed": 1, "unsupported": 2, "error": 2}[result["status"]]
    if process.returncode != expected_code:
        raise ValueError("Frozen checker status and exit code disagree")
    if not isinstance(result.get("violations", []), list):
        raise ValueError("Frozen checker returned malformed violations")
    return result, process.returncode, process.stderr.decode("utf-8", errors="replace")


def check_outputs(run: Path, destination: Path) -> dict:
    run, destination = run.resolve(), destination.resolve()
    if (not run.is_relative_to((TESTS / "runs").resolve())
            or not destination.is_relative_to((TESTS / "results").resolve())
            or destination.suffix != ".json"):
        raise ValueError("Use tests/runs/ input and a new .json file under tests/results/")
    if destination.exists():
        raise ValueError("Refusing to overwrite an existing result file")
    # Reject legacy runs before verify_run could load unfrozen legacy criteria.
    initial_manifest = read_json(run / "manifest.json")
    if not isinstance(initial_manifest, dict) or initial_manifest.get("protocol") != 2:
        raise ValueError("A fully frozen protocol 2 run is required")
    manifest, cases = verify_run(run)
    if manifest != initial_manifest:
        raise ValueError("Run manifest changed while verification started")
    lookup = {case["id"]: case for case in cases}
    missing = set(CASE_IDS) - set(lookup)
    if missing:
        raise ValueError("Fixed prose subset is incomplete: " + ", ".join(sorted(missing)))
    if any(lookup[identifier]["task"] == "comments" for identifier in CASE_IDS):
        raise ValueError("The fixed prose subset contains a comment task; use collect.py")
    if not all(name in manifest["snapshot_sha256"] for name in CHECKER_FILES):
        raise ValueError("The frozen snapshot lacks the prose checker or scanner")
    expected_outputs = {Path(relative).with_name("outputs.json").as_posix()
                        for relative in manifest["request_sha256"]}
    actual_outputs = {path.relative_to(run).as_posix() for mode in CONDITIONS
                      for path in (run / mode).glob("batch-*/outputs.json")}
    if actual_outputs != expected_outputs:
        raise ValueError("Complete output file set must match every frozen request packet")
    hashes_before = input_hashes(run, manifest)
    expected = set(lookup)
    # Load all outputs, including cases outside this subset, before running any
    # comparison. An unfinished or selectively published run is not accepted.
    outputs = {mode: load_outputs(run, mode, expected) for mode in CONDITIONS}
    execution_audit = audit_published_outputs(run, cases)
    checker = run / "snapshot/yaya/scripts/check_rewrite.py"
    records = []
    work_parent = (TESTS / "results").resolve()
    work_parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prose-check-", dir=work_parent) as directory:
        work = Path(directory).resolve()
        work.relative_to(work_parent)
        for identifier in CASE_IDS:
            case = lookup[identifier]
            before = case["input"].encode("utf-8")
            for mode in CONDITIONS:
                after = outputs[mode][identifier]["text"].encode("utf-8")
                result, exit_code, stderr = check_pair(checker, work, before, after)
                records.append({
                    "id": identifier, "condition": mode,
                    "status": result["status"],
                    "violations": result.get("violations", []),
                    "before_sha256": digest(before), "after_sha256": digest(after),
                    "before_bytes": len(before), "after_bytes": len(after),
                    "checker_exit": exit_code, "checker_stderr": stderr,
                    "checker_result": result,
                })
    final_manifest, final_cases = verify_run(run)
    hashes_after = input_hashes(run, final_manifest)
    if final_manifest != manifest or final_cases != cases or hashes_after != hashes_before:
        raise ValueError("Run inputs or outputs changed during mechanical checking")
    counts = {}
    for mode in CONDITIONS:
        counter = Counter(row["status"] for row in records if row["condition"] == mode)
        counts[mode] = {status: counter[status] for status in STATUSES}
    report = {
        "status": "complete", "run": str(run), "protocol": 2,
        "selection": {"case_ids": list(CASE_IDS), "cases_per_condition": len(CASE_IDS),
                      "policy": "Fixed H001-H060 plus X001, X002, X004; no outcome-based filtering."},
        "complete_run_cases_per_condition": len(expected),
        "checker": {"path": "snapshot/yaya/scripts/check_rewrite.py",
                    "snapshot_sha256": {name: manifest["snapshot_sha256"][name] for name in CHECKER_FILES},
                    "additional_options": []},
        "conditions": counts, "records": records, "execution_audit": execution_audit,
        "input_sha256_before": hashes_before, "input_sha256_after": hashes_after,
        "inputs_unchanged": True,
        "interpretation": [
            "Mechanical results only; failed is not automatically a semantic or task failure.",
            "Unsupported and error remain separate and are never counted as passed.",
            "Passed does not establish meaning, facts, attribution, or number-to-entity associations.",
            "Inputs and complete output text are compared verbatim; no wrappers are removed and no --allow options are added.",
            "Comment tasks remain the responsibility of collect.py; this report does not change ratings or summaries.",
        ],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return {"status": "complete", "destination": str(destination),
            "cases_per_condition": len(CASE_IDS), "conditions": counts,
            "inputs_unchanged": True}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("destination", type=Path, help="New JSON result file; never overwritten")
    args = parser.parse_args(argv)
    try:
        summary = check_outputs(args.run, args.destination)
    except (ValueError, OSError) as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=True))
        return 2
    print(json.dumps(summary, ensure_ascii=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())

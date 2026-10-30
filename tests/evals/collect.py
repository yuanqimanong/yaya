"""Collect complete runs, run mechanical checks, and prepare anonymous review pairs."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import random
import re
import subprocess
import sys

TESTS = Path(__file__).resolve().parents[1]


def read_json(path: Path):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"Duplicate JSON key {key!r}: {path}")
            result[key] = value
        return result
    return json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique)


def cases() -> list[dict]:
    result = []
    for filename in ("cases.json", "heldout.json"):
        result.extend(read_json(TESTS / "evals" / filename)["cases"])
    return result


def validate_cases(value) -> list[dict]:
    if not isinstance(value, list) or not value:
        raise ValueError("Cases must be a non-empty array")
    identifiers = set()
    for case in value:
        if (not isinstance(case, dict) or not {"id", "request", "input", "task", "checks"} <= case.keys()
                or not isinstance(case["id"], str) or not re.fullmatch(r"[A-Za-z0-9_-]+", case["id"])
                or any(not isinstance(case[field], str) or not case[field].strip() for field in ("request", "task"))
                or not isinstance(case["input"], str) or not isinstance(case["checks"], list)
                or not case["checks"] or any(not isinstance(check, str) or not check.strip() for check in case["checks"])):
            raise ValueError("Malformed case; id, request, input, task and checks are required")
        if case["id"] in identifiers:
            raise ValueError(f"Duplicate case ID: {case['id']}")
        identifiers.add(case["id"])
    return value


def input_files(directory: Path, base: Path) -> set[str]:
    """Inventory frozen inputs; interpreter caches are not authored inputs."""
    files = set()
    for path in directory.rglob("*"):
        if "__pycache__" in path.relative_to(directory).parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Frozen inputs must not contain symbolic links: {path}")
        if path.is_file():
            files.add(path.relative_to(base).as_posix())
    return files


def verify_hashes(base: Path, hashes: dict, label: str) -> None:
    if not isinstance(hashes, dict):
        raise ValueError(f"Malformed {label} hashes")
    for relative, expected_hash in hashes.items():
        if (not isinstance(relative, str) or "\\" in relative or ":" in relative
                or PurePosixPath(relative).is_absolute() or ".." in PurePosixPath(relative).parts
                or PurePosixPath(relative).as_posix() != relative):
            raise ValueError(f"Unsafe frozen input path: {relative}")
        path = (base / relative).resolve()
        if not path.is_relative_to(base.resolve()):
            raise ValueError(f"Frozen input path escapes snapshot: {relative}")
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected_hash:
            raise ValueError(f"{label} changed: {relative}")


def load_outputs(run: Path, condition: str, expected: set[str]) -> dict:
    outputs = {}
    for path in sorted((run / condition).glob("batch-*/outputs.json")):
        value = read_json(path)
        if not isinstance(value, list):
            raise ValueError(f"Expected an output array: {path}")
        requested = path.with_name("requests.json")
        packet_ids = {row["id"] for row in read_json(requested)} if requested.is_file() else None
        output_ids = set()
        for row in value:
            if (not isinstance(row, dict) or set(row) != {"id", "text", "notes", "skill_used"}
                    or not isinstance(row["id"], str) or not isinstance(row["text"], str)
                    or not row["text"].strip() or not isinstance(row["notes"], str)
                    or type(row["skill_used"]) is not bool):
                raise ValueError(f"Malformed result: {path}")
            identifier = row["id"]
            if identifier in outputs or identifier not in expected:
                raise ValueError(f"Duplicate, unknown or malformed result: {identifier}")
            if condition == "baseline" and row["skill_used"]:
                raise ValueError(f"Baseline used the skill: {identifier}")
            if packet_ids is not None and identifier not in packet_ids:
                raise ValueError(f"Result does not belong to its request packet: {identifier}")
            outputs[identifier] = row
            output_ids.add(identifier)
        if packet_ids is not None and output_ids != packet_ids:
            raise ValueError(f"Incomplete output packet: {path}")
    if set(outputs) != expected:
        raise ValueError(f"{condition} incomplete; missing {sorted(expected - set(outputs))}")
    return outputs


def verify_run(run: Path) -> tuple[dict, list[dict]]:
    manifest = read_json(run / "manifest.json")
    if (not isinstance(manifest, dict) or not {"snapshot_sha256", "case_ids"} <= manifest.keys()
            or type(manifest.get("protocol", 1)) is not int or manifest.get("protocol", 1) not in {1, 2}):
        raise ValueError("Malformed or unsupported run manifest")
    if manifest.get("protocol", 1) == 2 and not {"request_sha256", "data_sha256", "criteria_sha256"} <= manifest.keys():
        raise ValueError("Frozen input hashes are required for protocol 2")
    if "batch_size" in manifest and (type(manifest["batch_size"]) is not int or manifest["batch_size"] < 1):
        raise ValueError("Invalid manifest batch size")
    snapshot = run / "snapshot/yaya"
    verify_hashes(snapshot, manifest["snapshot_sha256"], "Skill snapshot")
    if manifest.get("protocol", 1) >= 2:
        requests = {p.relative_to(run).as_posix() for mode in ("skill", "baseline")
                    for p in (run / mode).glob("batch-*/requests.json")}
        for label, recorded, actual in (
            ("Skill snapshot", manifest["snapshot_sha256"], input_files(snapshot, snapshot)),
            ("External data", manifest["data_sha256"], input_files(run / "data", run)),
            ("Generation requests", manifest["request_sha256"], requests),
        ):
            if not isinstance(recorded, dict) or set(recorded) != actual:
                raise ValueError(f"{label} file set changed")
        verify_hashes(run, manifest["request_sha256"], "Frozen input")
        verify_hashes(run, manifest["data_sha256"], "Frozen input")
        verify_hashes(run, {"criteria.json": manifest["criteria_sha256"]}, "Frozen input")
        source_cases = validate_cases(read_json(run / "criteria.json"))
    else:
        # Legacy run: prompt text is checked below, but criteria were not hashed before generation.
        source_cases = cases()
    if [case["id"] for case in source_cases] != manifest["case_ids"]:
        raise ValueError("Case list differs from the manifest")
    expected_packets = [{key: case[key] for key in ("id", "request", "input")} for case in source_cases]
    for mode in ("skill", "baseline"):
        packets = [read_json(path) for path in sorted((run / mode).glob("batch-*/requests.json"))]
        if any(not isinstance(packet, list) for packet in packets):
            raise ValueError(f"Generation requests must be arrays: {mode}")
        if "batch_size" in manifest and any(len(packet) > manifest["batch_size"] for packet in packets):
            raise ValueError(f"Generation context exceeds declared batch size: {mode}")
        actual_packets = [row for packet in packets for row in packet]
        if actual_packets != expected_packets:
            raise ValueError(f"Generation requests differ from cases: {mode}")
    return manifest, source_cases


def check_comments(script: Path, before: Path, after: Path) -> dict:
    # Resolve every helper beside the frozen checker, never from host sys.modules.
    try:
        run = subprocess.run([sys.executable, "-B", str(script), str(before), str(after)],
                             capture_output=True, timeout=30, check=False)
    except subprocess.TimeoutExpired:
        return {"status": "error", "reason": "Frozen comment checker exceeded 30 seconds."}
    try:
        result = json.loads(run.stdout)
    except (ValueError, UnicodeError) as exc:
        raise ValueError("Frozen comment checker did not return JSON") from exc
    codes = {"passed": 0, "failed": 1, "unsupported": 2, "error": 2}
    if not isinstance(result, dict) or result.get("status") not in codes:
        raise ValueError("Frozen comment checker returned an unknown status")
    if run.returncode != codes[result["status"]]:
        raise ValueError("Frozen comment checker status and exit code disagree")
    return result


def collect(run: Path, destination: Path) -> dict:
    run, destination = run.resolve(), destination.resolve()
    if not run.is_relative_to(TESTS / "runs") or not destination.is_relative_to(TESTS / "results"):
        raise ValueError("Use tests/runs/ for runs and tests/results/ for evidence")
    manifest, source_cases = verify_run(run)
    expected = {case["id"] for case in source_cases}
    outputs = {mode: load_outputs(run, mode, expected) for mode in ("skill", "baseline")}
    from compare_runs import audit_published_outputs
    execution_audit = audit_published_outputs(run, source_cases)
    if (run / "review").exists():
        raise ValueError("Review directory already exists; refusing to overwrite anonymous evidence")
    if destination.exists():
        raise ValueError("Result destination already exists; refusing to overwrite evidence")
    script = run / "snapshot/yaya/scripts/check_comments.py"
    mechanical = []
    for case in source_cases:
        for mode in outputs:
            output = outputs[mode][case["id"]]
            text = output["text"]
            failures = []
            # Literal checks establish only exact preservation, never factual accuracy.
            placeholders = re.findall(r"\{\{[^{}]+\}\}", case["input"])
            if any(item not in text for item in placeholders):
                failures.append("source_placeholder_missing")
            if case["id"] in {"clear-unchanged", "ja-clear-unchanged"} and text.strip() != case["input"].strip():
                failures.append("requested_unchanged_text_modified")
            if case["id"] == "mixed-language":
                for literal in ('fetchUser(id)', '"Do not retry."', "200 ms", 'const label = "返回结果";'):
                    if literal not in text:
                        failures.append("protected_literal_missing: " + literal)
            record = {"id": case["id"], "condition": mode, "literal_failures": failures}
            if case["task"] == "comments":
                work = run / "mechanical" / mode / case["id"]
                work.mkdir(parents=True, exist_ok=True)
                extension = ".ts" if case["id"] == "unsupported-ts-comments" else ".py"
                before, after = work / ("before" + extension), work / ("after" + extension)
                before.write_text(case["input"], encoding="utf-8", newline="\n")
                after.write_text(text, encoding="utf-8", newline="\n")
                record["comment_boundary"] = check_comments(script, before, after)
            mechanical.append(record)
    final_manifest, final_cases = verify_run(run)
    final_outputs = {mode: load_outputs(run, mode, expected) for mode in ("skill", "baseline")}
    if final_manifest != manifest or final_cases != source_cases or final_outputs != outputs:
        raise ValueError("Run inputs or outputs changed during collection; rerun checks")
    # Reviewers receive criteria and anonymous text only, without self-reported notes.
    rng = random.Random(20261020)
    blind, key = [], {}
    for case in source_cases:
        order = ["skill", "baseline"]
        rng.shuffle(order)
        key[case["id"]] = dict(zip(("A", "B"), order))
        blind.append({"id": case["id"], "request": case["request"], "input": case["input"],
                      "checks": case["checks"], "A": outputs[order[0]][case["id"]]["text"],
                      "B": outputs[order[1]][case["id"]]["text"]})
    destination.mkdir(parents=True, exist_ok=False)
    (run / "review").mkdir(exist_ok=False)
    for number in range(0, len(blind), 12):
        (run / "review" / f"batch-{number // 12 + 1:02d}.json").write_text(
            json.dumps(blind[number:number + 12], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for name, value in (("outputs.json", outputs), ("mechanical.json", mechanical), ("blind-key.json", key),
                        ("cases.json", source_cases), ("execution-audit.json", execution_audit)):
        (destination / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (destination / "manifest.json").write_bytes((run / "manifest.json").read_bytes())
    summary = {"cases_per_condition": len(expected), "outputs": sum(map(len, outputs.values())),
               "inputs_unchanged": True,
               "protocol": manifest.get("protocol", 1),
               "criteria_frozen_before_generation": manifest.get("protocol", 1) >= 2,
               "literal_failures": sum(bool(row["literal_failures"]) for row in mechanical),
               "comment_statuses": {status: sum(row.get("comment_boundary", {}).get("status") == status for row in mechanical)
                                    for status in ("passed", "failed", "unsupported")}}
    (destination / "mechanical-summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("destination", type=Path)
    args = parser.parse_args()
    print(json.dumps(collect(args.run, args.destination)))

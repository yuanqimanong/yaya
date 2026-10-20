"""Prepare generation-only packets and an isolated snapshot; never call a model."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
from collect import read_json, validate_cases

ROOT = Path(__file__).resolve().parents[1]


def load_suites(names: list[str] | None, pilot: bool) -> tuple[list[dict], list[str]]:
    selected = names or ["cases", "heldout", "humanize", "scenarios"]
    if pilot and len(selected) != 1:
        raise ValueError("--pilot requires exactly one --suite")
    cases, filenames = [], []
    directory = (ROOT / "evals").resolve()
    for name in selected:
        relative = Path(name)
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Suites must be JSON files inside tests/evals/")
        if not relative.suffix:
            relative = relative.with_suffix(".json")
        path = (directory / relative).resolve()
        if relative.suffix != ".json" or not path.is_relative_to(directory):
            raise ValueError("Suites must be JSON files inside tests/evals/")
        data = read_json(path)
        if not isinstance(data, dict):
            raise ValueError(f"Expected a suite object: {name}")
        suite_cases = validate_cases(data.get("cases"))
        if pilot:
            identifiers = data.get("pilot_case_ids")
            lookup = {case["id"]: case for case in suite_cases}
            if (not isinstance(identifiers, list) or not identifiers
                    or any(not isinstance(item, str) or item not in lookup for item in identifiers)
                    or len(set(identifiers)) != len(identifiers)):
                raise ValueError("--pilot requires unique, existing pilot_case_ids")
            suite_cases = [lookup[identifier] for identifier in identifiers]
        label = "regression" if path.name == "cases.json" else relative.with_suffix("").as_posix()
        cases.extend({**case, "suite": label} for case in suite_cases)
        filenames.append(path.relative_to(directory).as_posix())
    validate_cases(cases)
    return cases, filenames


def prepare(run: Path, suites: list[str] | None = None, pilot: bool = False,
            batch_size: int = 1, case_ids: list[str] | None = None) -> None:
    run = run.resolve()
    if not run.is_relative_to(ROOT / "runs"):
        raise ValueError("Run directories must be under tests/runs/")
    if type(batch_size) is not int or batch_size < 1:
        raise ValueError("batch_size must be a positive integer")
    cases, filenames = load_suites(suites, pilot)
    if case_ids is not None:
        lookup = {case["id"]: case for case in cases}
        if (pilot or not case_ids or len(set(case_ids)) != len(case_ids)
                or any(identifier not in lookup for identifier in case_ids)):
            raise ValueError("--case-id requires unique existing IDs and cannot combine with --pilot")
        cases = [lookup[identifier] for identifier in case_ids]
    run.mkdir(parents=True, exist_ok=False)
    project = ROOT.parent
    snapshot = run / "snapshot" / "yaya"
    shutil.copytree(project / "core/yaya", snapshot, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # External optional packs keep their normal layout, outside the core snapshot.
    shutil.copytree(project / "language-packs", run / "data/language-packs",
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    # The reviewer-only snapshot is outside generation directories.
    criteria = run / "criteria.json"
    criteria.write_text(json.dumps(cases, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    # Same batches for both conditions; criteria stay out of generation packets.
    batches = [cases[i:i + batch_size] for i in range(0, len(cases), batch_size)]
    for mode in ("skill", "baseline"):
        for number, batch in enumerate(batches, start=1):
            directory = run / mode / f"batch-{number:03d}"
            directory.mkdir(parents=True)
            packet = [{key: case[key] for key in ("id", "request", "input")} for case in batch]
            (directory / "requests.json").write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    files = [p for p in snapshot.rglob("*") if p.is_file()]
    hashes = {p.relative_to(snapshot).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}
    request_hashes = {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                      for mode in ("skill", "baseline") for p in sorted((run / mode).glob("batch-*/requests.json"))}
    data_hashes = {p.relative_to(run).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                   for p in sorted((run / "data").rglob("*")) if p.is_file()}
    manifest = {"protocol": 2, "cases": len(cases), "batches_per_condition": len(batches), "batch_size": batch_size,
                "suites": filenames, "pilot": pilot,
                "conditions": ["skill", "baseline"], "model": "inherited Codex host model; exact revision/settings unavailable",
                "isolation": ("fresh context per case" if batch_size == 1 else "fresh context per batch, not per case"),
                "snapshot_sha256": hashes,
                "request_sha256": request_hashes, "data_sha256": data_hashes,
                "criteria_sha256": hashlib.sha256(criteria.read_bytes()).hexdigest(),
                "criteria_visible_to_generator": False, "case_ids": [case["id"] for case in cases]}
    (run / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(run), "cases": len(cases), "batches_per_condition": len(batches),
                      "batch_size": batch_size, "pilot": pilot}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path)
    parser.add_argument("--suite", action="append", help="Suite name or JSON path relative to tests/evals/; repeatable")
    parser.add_argument("--pilot", action="store_true", help="Use the selected suite's ordered pilot_case_ids")
    parser.add_argument("--batch-size", type=int, default=1, help="Cases per generation context (default: 1)")
    parser.add_argument("--case-id", action="append", help="Explicit ordered subset; repeatable, recorded in manifest")
    args = parser.parse_args()
    try:
        prepare(args.run, args.suite, args.pilot, args.batch_size, args.case_id)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"error: {exc}\n")

"""Freeze old/new skills and run paired semantic cases with the existing CLI harness.

No expected results are supplied to generation. Execution failures remain visible.
Use collect to create anonymous packets for the existing judge_cli.py.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import random
import shutil
import sys

from collect import read_json, validate_cases
import run_cli
from run_cli import Job, bounded_execute, configured_model, digest, make_prompt, run_one, verify_completed, write_json

ROOT = Path(__file__).resolve().parents[2]
GUIDES = {"comments": "comments.md", "text": "text.md", "authorship": "authorship.md"}


def files(root):
    return {p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in root.rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"}


def prepare(run, old, new, suite):
    run = run.resolve()
    if not run.is_relative_to(ROOT / "tests/runs"):
        raise ValueError("Use tests/runs/ for isolated generation.")
    cases = validate_cases(read_json(suite)["cases"])
    run.mkdir(parents=True, exist_ok=False)
    for condition, source in (("old", old), ("new", new)):
        shutil.copytree(source, run / condition / "snapshot/yaya", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        for case in cases:
            directory = run / condition / case["id"]
            directory.mkdir()
            write_json(directory / "requests.json", {key: case[key] for key in ("id", "request", "input")})
    write_json(run / "criteria.json", cases)
    shutil.copyfile(run_cli.SCHEMA, run / "schema.json")
    manifest = {"protocol": 1, "prepared_utc": run_cli.datetime.now(run_cli.timezone.utc).isoformat(),
                "input_sha256": files(run), "model": configured_model(),
                "runner_sha256": digest(Path(__file__).read_bytes()),
                "shared_runner_sha256": digest(Path(run_cli.__file__).read_bytes()),
                "conditions": ["old", "new"], "case_ids": [case["id"] for case in cases],
                "limits": ["Synthetic directed cases, one sample per condition, no cross-model accuracy estimate.",
                           "Same requests and evidence; only frozen task-relevant skill guidance differs.",
                           "Exact backend revision and sampling seed unavailable; uses unchanged host model configuration."]}
    write_json(run / "manifest.json", manifest)
    return manifest


def jobs(run):
    manifest = read_json(run / "manifest.json")
    actual = {"criteria.json", "schema.json"}
    for condition in ("old", "new"):
        actual.update(f"{condition}/snapshot/yaya/{name}" for name in files(run / condition / "snapshot/yaya"))
        actual.update(path.relative_to(run).as_posix() for path in (run / condition).glob("*/requests.json"))
    if actual != set(manifest["input_sha256"]):
        raise ValueError("Frozen input file set changed.")
    for name, expected in manifest["input_sha256"].items():
        if digest((run / name).read_bytes()) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    if (manifest["model"] != configured_model()
            or manifest["runner_sha256"] != digest(Path(__file__).read_bytes())
            or manifest["shared_runner_sha256"] != digest(Path(run_cli.__file__).read_bytes())):
        raise ValueError("Model configuration or evaluation runner changed.")
    cases = read_json(run / "criteria.json")
    result = []
    for case in cases:
        for condition in ("old", "new"):
            directory = run / condition / case["id"]
            skill = run / condition / "snapshot/yaya"
            names = ["SKILL.md", "references/" + GUIDES[case["task"]], "languages/zh-Hans/GUIDE.md"]
            if case["task"] in {"comments", "text"}:
                names.append("references/engineering.md")
            if case["id"] in {"ENG09", "ENG11"}:
                names.append("references/validation.md")
            context = [(name, (skill / name).read_text(encoding="utf-8")) for name in names if (skill / name).is_file()]
            hashes = {name: digest((skill / name).read_bytes()) for name, _ in context}
            prompt = make_prompt(read_json(directory / "requests.json"), "skill", context)
            result.append(Job(directory, case["id"], condition, prompt, hashes))
    return cases, result


def execute(run, command, workers=1, timeout=120, limit=None, resume=False):
    run_cli.validate_timeout(timeout)
    _, pending = jobs(run)
    metadata = {"command": command, "model": configured_model(), "workers": workers,
                "timeout": timeout, "manifest_sha256": digest((run / "manifest.json").read_bytes()),
                "interleaved": True, "case_context": [job.identity(run) for job in pending]}
    path = run / "execution.json"
    if path.exists():
        if not resume or read_json(path) != metadata:
            raise ValueError("Do not overwrite or change an existing evaluation.")
    else:
        write_json(path, metadata)
    pending = pending[:limit * 2] if limit else pending
    for job in pending:
        if (job.directory / "cli-attempt-01").exists():
            if not resume:
                raise ValueError("Use --resume for verified completed attempts; failures need a new run.")
            verify_completed(job, job.directory / "cli-attempt-01")
    results = []
    for job, result in bounded_execute(pending, lambda job: run_one(job, command, timeout, resume), workers):
        row = {"id": job.identifier, "condition": job.condition, **result}
        results.append(row)
        print(json.dumps({key: row[key] for key in ("id", "condition", "status", "error") if key in row}), flush=True)
    write_json(run / ("execution-result-" + str(len(list(run.glob("execution-result-*.json")))) + ".json"), results)
    return results


def review_answer(case, response):
    """Include requested deliverable notes without exposing private generator metadata."""
    if case.get("review_delivered_notes") is True:
        return response["text"] + "\n\nDelivered notes:\n" + response["notes"]
    return response["text"]


def collect(run, destination):
    cases, all_jobs = jobs(run)
    rows = {"old": {}, "new": {}}
    for job in all_jobs:
        verify_completed(job, job.directory / "cli-attempt-01")
        rows[job.condition][job.identifier] = read_json(job.directory / "outputs.json")[0]
    review = run / "review"
    review.mkdir(exist_ok=False)
    destination.mkdir(parents=True, exist_ok=False)
    randomizer = random.Random(20261021)
    pairs, key = [], {}
    for case in cases:
        order = ["old", "new"]
        randomizer.shuffle(order)
        key[case["id"]] = dict(zip(("A", "B"), order))
        pairs.append({**{field: case[field] for field in ("id", "request", "input", "checks")},
                      "A": review_answer(case, rows[order[0]][case["id"]]),
                      "B": review_answer(case, rows[order[1]][case["id"]])})
    for number, index in enumerate(range(0, len(pairs), 4), 1):
        write_json(review / f"batch-{number:03d}.json", pairs[index:index + 4])
    write_json(destination / "blind-key.json", key)
    write_json(destination / "outputs.json", rows)
    write_json(destination / "cases.json", cases)
    write_json(destination / "generation.json", {"manifest": read_json(run / "manifest.json"),
               "execution": read_json(run / "execution.json"),
               "attempts": [read_json(job.directory / "cli-attempt-01/completion.json") for job in all_jobs]})
    print(json.dumps({"review": str(review), "destination": str(destination)}))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("prepare", "run", "collect"))
    parser.add_argument("run", type=Path)
    parser.add_argument("--old", type=Path)
    parser.add_argument("--new", type=Path, default=ROOT / "core/yaya")
    parser.add_argument("--suite", type=Path, default=Path(__file__).with_name("engineering.json"))
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--timeout", type=float, default=120)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--destination", type=Path)
    parser.add_argument("--executable", default=shutil.which("codex"))
    args = parser.parse_args()
    try:
        run_cli.validate_timeout(args.timeout)
        if args.workers < 1 or args.workers > 3 or (args.limit is not None and args.limit < 1):
            raise ValueError("Use 1..3 workers and positive timeout/limit.")
        if args.action == "prepare":
            if args.old is None:
                raise ValueError("Supply --old task-start skill snapshot.")
            prepare(args.run, args.old, args.new, args.suite)
        elif args.action == "run":
            if not args.executable:
                raise ValueError("No existing Codex CLI available.")
            result = execute(args.run, [args.executable], args.workers, args.timeout, args.limit, args.resume)
            return 0 if all(row["status"] == "completed" for row in result) else 1
        else:
            if args.destination is None or not args.destination.resolve().is_relative_to(ROOT / "tests/results"):
                raise ValueError("Supply a new --destination under tests/results/.")
            collect(args.run, args.destination.resolve())
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        parser.exit(2, f"error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())

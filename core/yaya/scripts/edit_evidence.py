#!/usr/bin/env python3
"""Content-bound check evidence and task-start snapshots (standard library only)."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import uuid

VERSION = "1.0"
KINDS = ("comments", "docstrings", "prose", "manual")


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(data):
    return hashlib.sha256(data).hexdigest()


def strict_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    return json.loads(Path(path).read_bytes().decode("utf-8-sig"), object_pairs_hook=pairs)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, ensure_ascii=True, indent=2)
        stream.write("\n")


def content_info(data):
    bom = data.startswith(b"\xef\xbb\xbf")
    try:
        data.decode("utf-8-sig")
        encoding = "utf-8-bom" if bom else "utf-8"
    except UnicodeError:
        encoding = "non-utf-8 (see checker language-specific support)"
    return {"sha256": digest(data), "bytes": len(data), "encoding": encoding,
            "bom": bom, "crlf": data.count(b"\r\n"),
            "lf": data.count(b"\n") - data.count(b"\r\n"),
            "lone_cr": data.count(b"\r") - data.count(b"\r\n")}


def tool_identity(tool):
    tool = Path(tool).resolve()
    names = {tool.name, "edit_evidence.py"}
    if tool.name == "check_docstrings.py":
        names.add("check_comments.py")
    if tool.name == "check_rewrite.py":
        names.add("prose_scan.py")
    return {"name": tool.name, "version": "sha256:" + digest(tool.read_bytes()), "evidence_version": VERSION,
            "sha256": {name: digest((tool.parent / name).read_bytes()) for name in sorted(names)},
            "python": sys.version, "executable": sys.executable}


def bound_check(before, after, tool, operation, options=None, *, max_bytes=None):
    """Bind a checker result to stable raw files and all its local dependencies."""
    started = now()
    evidence = {"started_utc": started, "tool": tool_identity(tool),
                "command": [sys.executable, *sys.argv], "options": options or {},
                "invocation": "CLI or Python API; command records the host process"}
    paths = {"before": Path(before), "candidate": Path(after)}
    def read(path):
        if max_bytes is None:
            return path.read_bytes()
        with path.open("rb") as stream:
            data = stream.read(max_bytes + 1)
        if len(data) > max_bytes:
            raise ValueError(f"Input exceeds {max_bytes} bytes.")
        return data
    try:
        raw = {key: read(path) for key, path in paths.items()}
    except OSError as exc:
        return {"status": "unsupported", "reason": f"Cannot read inputs: {type(exc).__name__}: {exc}",
                "evidence": {**evidence, "finished_utc": now()}}
    evidence.update({key: {"path": str(paths[key].resolve()), **content_info(data)}
                     for key, data in raw.items()})
    result = operation()
    try:
        stable = all(read(path) == raw[key] for key, path in paths.items())
    except (OSError, ValueError):
        stable = False
    if not stable:
        result = {"status": "failed", "reason": "Input changed while checking; discard this result.",
                  "superseded_result": result}
    result["evidence"] = {**evidence, "finished_utc": now(), "inputs_stable": stable}
    return result


def exact_grant(grant, before, after, key):
    """Reject broad, stale, malformed, or extra authorization fields."""
    if (not isinstance(grant, dict)
            or set(grant) != {"schema", "before_sha256", "after_sha256", key}
            or type(grant["schema"]) is not int or grant["schema"] != 1
            or grant["before_sha256"] != digest(before)
            or grant["after_sha256"] != digest(after)
            or not isinstance(grant[key], list)):
        raise ValueError("Grant must bind exact BEFORE/AFTER SHA-256 and enumerated differences (schema 1).")
    return grant[key]


def safe_file(root, relative):
    relative_path = PurePosixPath(relative)
    if (not relative or "\\" in relative or ":" in relative or relative_path.is_absolute()
            or any(part in {".", ".."} for part in relative.split("/"))):
        raise ValueError("Use a safe root-relative file path with forward slashes.")
    path = root / relative
    for part in (path, *path.parents):
        if part == root.parent:
            break
        if part.is_symlink() or (hasattr(part, "is_junction") and part.is_junction()):
            raise ValueError("Linked paths are not supported for snapshots.")
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError("Path escaped the task root.")
    return path


def target(value):
    name, kind = value.rsplit(":", 1)
    if kind not in KINDS:
        raise ValueError("Target syntax: relative/path:comments|docstrings|prose|manual")
    return {"path": name, "kind": kind}


def start(root, out, targets):
    started = now()
    root, out = Path(root).resolve(), Path(out).resolve()
    parsed = [target(item) for item in targets]
    if not parsed or len({(x["path"], x["kind"]) for x in parsed}) != len(parsed):
        raise ValueError("Plan unique nonempty targets before editing.")
    content = {item["path"]: safe_file(root, item["path"]).read_bytes() for item in parsed}
    git_error = None
    def git(*args):
        nonlocal git_error
        if git_error:
            return None
        try:
            process = subprocess.run(["git", "-C", str(root), *args], capture_output=True, check=False, timeout=10)
        except (OSError, subprocess.TimeoutExpired) as exc:
            git_error = f"Git metadata unavailable: {type(exc).__name__}; selected-file snapshots remain available."
            return None
        return process.stdout if process.returncode == 0 else None
    head, status = git("rev-parse", "HEAD"), git("status", "--porcelain=v1")
    baseline = {"head": head.decode().strip() if head else None,
                "status": status.decode("utf-8", errors="replace") if status is not None else None}
    if out.exists() or any(out == safe_file(root, name) for name in content):
        raise ValueError("Use a new snapshot directory outside the selected files.")
    out.mkdir(parents=True, exist_ok=False)
    files = {}
    for name, data in content.items():
        path = out / "before" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        files[name] = content_info(data)
    for label, args in (("unstaged", ("diff", "--binary")), ("staged", ("diff", "--cached", "--binary"))):
        patch = git(*args)
        if patch is not None:
            (out / f"git-{label}.patch").write_bytes(patch)
            baseline[label + "_sha256"] = digest(patch)
    baseline["error"] = git_error
    if any(safe_file(root, name).read_bytes() != data for name, data in content.items()):
        raise ValueError("A selected file changed while snapshotting; keep this partial snapshot and start a fresh task.")
    manifest = {"schema": 1, "started_utc": started, "snapshot_finished_utc": now(), "root": str(root), "files": files,
                "targets": parsed, "git_baseline": baseline,
                "scope": "Selected existing files only; no reset, checkout, or business-code changes."}
    write_json(out / "manifest.json", manifest)
    return manifest


def load_task(directory):
    directory = Path(directory).resolve()
    manifest = strict_json(directory / "manifest.json")
    for name, info in manifest["files"].items():
        if digest(safe_file(directory / "before", name).read_bytes()) != info["sha256"]:
            raise ValueError("Task-start snapshot changed.")
    return directory, manifest


def record(directory, selected, grant=None, disposition=None, note=None):
    directory, manifest = load_task(directory)
    item = target(selected)
    if item not in manifest["targets"]:
        raise ValueError("Target was not planned in the task-start manifest.")
    before = safe_file(directory / "before", item["path"])
    after = safe_file(Path(manifest["root"]), item["path"])
    if disposition is not None:
        if disposition not in {"accepted", "excluded", "unresolved"} or not note or not note.strip():
            raise ValueError("Manual review/exclusion requires disposition and concrete evidence/reason.")
        result = bound_check(before, after, __file__,
                             lambda: {"status": "manual_review", "disposition": disposition, "note": note})
    elif item["kind"] == "comments":
        if grant is not None:
            raise ValueError("Ordinary-comment mode has no bypass.")
        from check_comments import check_files
        result = check_files(before, after)
    elif item["kind"] == "docstrings":
        from check_docstrings import check_files
        result = check_files(before, after, grant)
    elif item["kind"] == "prose":
        from check_rewrite import check_files
        result = check_files(before, after, allow=grant or ())
    else:
        raise ValueError("Manual targets require --disposition and --note.")
    entry = {"target": item, "manifest_sha256": digest((directory / "manifest.json").read_bytes()),
             "recorded_utc": now(), "result": result}
    write_json(directory / "records" / (uuid.uuid4().hex + ".json"), entry)
    return entry


def summarize(directory):
    directory, manifest = load_task(directory)
    manifest_hash = digest((directory / "manifest.json").read_bytes())
    records = [strict_json(path) for path in (directory / "records").glob("*.json")]
    counts = dict.fromkeys(("passed", "failed", "unsupported", "manual_review", "unverified"), 0)
    details, open_failures = [], []
    for item in manifest["targets"]:
        history = sorted((row for row in records if row["target"] == item), key=lambda x: x["recorded_utc"])
        latest = history[-1] if history else None
        status, reason = "unverified", "No check executed."
        if latest:
            result = latest["result"]
            evidence = result.get("evidence", {})
            try:
                current = safe_file(Path(manifest["root"]), item["path"]).read_bytes()
                tool = evidence["tool"]
                valid = (latest["manifest_sha256"] == manifest_hash
                         and evidence.get("inputs_stable") is True
                         and evidence["before"]["sha256"] == manifest["files"][item["path"]]["sha256"]
                         and evidence["candidate"]["sha256"] == digest(current)
                         and tool == tool_identity(Path(__file__).with_name(tool["name"])))
            except (OSError, KeyError, ValueError):
                valid = False
            if valid and result["status"] in counts:
                status, reason = result["status"], result.get("reason", "Current content-bound evidence.")
            else:
                reason = "Stale, missing, or incompatible evidence; rerun the actual check."
            failures = [row for row in history if row["result"]["status"] == "failed"]
            excluded = (status == "manual_review" and result.get("disposition") == "excluded")
            if failures and status != "passed" and not excluded:
                open_failures.append(item)
        counts[status] += 1
        details.append({"target": item, "status": status, "reason": reason,
                        "history": len(history), "latest": latest})
    return {"counts": counts, "open_failures": open_failures, "targets": details,
            "complete": (counts["passed"] == len(details) and not open_failures),
            "limitations": ["Manual review and exclusion are never mechanical passes.",
                            "History is retained; stale passes and unexecuted checks are unverified.",
                            "Snapshots cover planned existing files; additions/deletions and mixed-mode chains require explicit review."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    initial = commands.add_parser("start")
    initial.add_argument("root", type=Path)
    initial.add_argument("out", type=Path)
    initial.add_argument("--target", action="append", required=True)
    check = commands.add_parser("check")
    check.add_argument("directory", type=Path)
    check.add_argument("--target", required=True)
    check.add_argument("--allow", type=Path)
    check.add_argument("--disposition", choices=("accepted", "excluded", "unresolved"))
    check.add_argument("--note")
    summary = commands.add_parser("summary")
    summary.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.action == "start":
            result = start(args.root, args.out, args.target)
        elif args.action == "check":
            result = record(args.directory, args.target,
                            strict_json(args.allow) if args.allow else None, args.disposition, args.note)
        else:
            result = summarize(args.directory)
        print(json.dumps(result, ensure_ascii=True))
        if args.action == "summary":
            return 0 if result["complete"] else 1
        if args.action == "check":
            return {"passed": 0, "failed": 1}.get(result["result"]["status"], 2)
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(json.dumps({"status": "unsupported", "reason": str(exc)}, ensure_ascii=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

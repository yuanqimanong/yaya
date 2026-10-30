#!/usr/bin/env python3
"""Local, data-only language pack operations. Python 3.10+, standard library."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import shutil
import stat
import sys
import tempfile
import uuid
import zipfile

CORE = Path(__file__).resolve().parents[1]
FORMAT = 1
CORE_MAJOR = 0
REQUIRED = {"pack.json", "GUIDE.md", "examples.md", "LICENSE"}
ALLOWED = REQUIRED | {"REVIEW.md", "PATTERNS.md"}
FIELDS = {"format_version", "id", "version", "core_major", "name", "license", "quality", "direction"}
MAX_FILE = 512 * 1024
MAX_TOTAL = 2 * 1024 * 1024
MAX_ARCHIVE = 8 * 1024 * 1024
SEMVER = re.compile(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)(?:\.(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*))*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?", re.ASCII)


class PackError(ValueError):
    pass


def canonical_tag(value: str) -> str:
    """BCP 47 subset; no registry, extensions, private-use or grandfathered tags."""
    parts = value.split("-")
    if not re.fullmatch(r"[A-Za-z]{2,3}", parts[0]):
        raise PackError("Expected a language tag such as fr, sr-Latn or es-419")
    out = [parts.pop(0).lower()]
    if parts and re.fullmatch(r"[A-Za-z]{4}", parts[0]):
        out.append(parts.pop(0).title())
    if parts and re.fullmatch(r"[A-Za-z]{2}|[0-9]{3}", parts[0]):
        out.append(parts.pop(0).upper())
    seen = set()
    for part in parts:
        if not re.fullmatch(r"[A-Za-z0-9]{5,8}|[0-9][A-Za-z0-9]{3}", part) or part.lower() in seen:
            raise PackError("Unsupported or duplicate BCP 47 subtag")
        seen.add(part.lower())
        out.append(part.lower())
    return "-".join(out)


def pack_id(value: str) -> str:
    if canonical_tag(value) != value:
        raise PackError("Pack IDs must use canonical language-Script-REGION casing")
    return value


def candidates(value: str) -> list[str]:
    parts = canonical_tag(value).split("-")
    result = ["-".join(parts)]
    if parts[0] == "zh" and len(parts) > 1 and parts[1] in {"CN", "SG", "TW", "HK", "MO"}:
        script = "Hans" if parts[1] in {"CN", "SG"} else "Hant"
        parts.insert(1, script)
    while parts:
        tag = "-".join(parts)
        if tag not in result:
            result.append(tag)
        parts.pop()
    return result


def no_links(path: Path) -> None:
    for item in (path, *path.parents):
        if item.is_symlink() or (hasattr(item, "is_junction") and item.is_junction()):
            raise PackError(f"Symlink or junction is not allowed: {item}")
        # Python 3.10 lacks Path.is_junction on Windows.
        if item.exists() and getattr(item.lstat(), "st_file_attributes", 0) & 0x400:
            raise PackError(f"Reparse point is not allowed: {item}")


def inside(path: Path, root: Path) -> Path:
    no_links(path)
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()) or resolved == root.resolve():
        raise PackError("Operation escaped its data directory")
    return resolved


def strict_json(text: str, document: str = "pack.json") -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise PackError(f"Duplicate JSON key: {key}")
            result[key] = value
        return result
    result = json.loads(text, object_pairs_hook=pairs)
    if not isinstance(result, dict):
        raise PackError(f"{document} must contain an object")
    return result


def validate(path: Path, compatible: bool = True) -> dict:
    no_links(path)
    if not path.is_dir():
        raise PackError(f"Pack directory missing: {path}")
    files = list(path.iterdir())
    names = {p.name for p in files}
    if not REQUIRED <= names or not names <= ALLOWED:
        raise PackError("Pack must contain pack.json, GUIDE.md, examples.md, LICENSE; only REVIEW.md and PATTERNS.md are optional")
    total = 0
    content = {}
    for item in files:
        no_links(item)
        if not item.is_file() or item.stat().st_size > MAX_FILE:
            raise PackError(f"Invalid file or size: {item.name}")
        with item.open("rb") as stream:
            raw = stream.read(MAX_FILE + 1)
        if len(raw) > MAX_FILE:
            raise PackError(f"Invalid file or size: {item.name}")
        total += len(raw)
        content[item.name] = raw.decode("utf-8")
        if not content[item.name].strip() or "\x00" in content[item.name]:
            raise PackError(f"Empty or binary content: {item.name}")
    if total > MAX_TOTAL:
        raise PackError("Pack exceeds 2 MiB")
    meta = strict_json(content["pack.json"])
    if set(meta) != FIELDS:
        raise PackError("Missing or unknown metadata fields")
    for key in ("format_version", "core_major"):
        if type(meta[key]) is not int or meta[key] < 0:
            raise PackError(f"{key} must be a nonnegative integer")
    for key in FIELDS - {"format_version", "core_major"}:
        if not isinstance(meta[key], str):
            raise PackError(f"{key} must be a string")
    pack_id(meta["id"])
    if not SEMVER.fullmatch(meta["version"]):
        raise PackError("version must be SemVer")
    if not meta["name"].strip() or not 1 <= len(meta["name"]) <= 100:
        raise PackError("name must contain 1–100 characters")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9.+-]*", meta["license"]):
        raise PackError("license must be a single SPDX identifier (registry not checked)")
    if meta["quality"] not in {"experimental", "reviewed"} or meta["direction"] not in {"ltr", "rtl"}:
        raise PackError("Invalid quality or direction")
    if meta["quality"] == "reviewed" and "REVIEW.md" not in content:
        raise PackError("reviewed packs require REVIEW.md evidence")
    if compatible and not is_compatible(meta):
        raise PackError("Incompatible pack format or core major version")
    return meta


def is_compatible(meta: dict) -> bool:
    return meta["format_version"] == FORMAT and meta["core_major"] == CORE_MAJOR


def roots(data_dir: str | None, project: str | None) -> list[tuple[str, Path]]:
    result = []
    if project:
        result.append(("project", Path(project).absolute() / ".yaya" / "language-packs"))
    result.extend([("user", (Path(data_dir).absolute() if data_dir else Path.home() / ".yaya") / "language-packs"), ("bundled", CORE / "languages")])
    return result


def resolve(language: str, data_dir=None, project=None) -> dict:
    requested = canonical_tag(language)
    base = {"requested": requested, "available": False, "resolved": None, "guide": None, "examples": None, "patterns": None}
    for source, root in roots(data_dir, project):
        try:
            no_links(root)
            if root.exists() and not root.is_dir():
                raise PackError(f"Pack root is not a directory: {root}")
        except (ValueError, OSError) as error:
            return {**base, "status": "invalid", "source": source, "error": str(error)}
        for tag in candidates(requested):
            directory = root / tag
            if not directory.exists() and not directory.is_symlink():
                continue
            try:
                meta = validate(directory, compatible=False)
                if meta["id"] != tag:
                    raise PackError("Directory ID differs from metadata ID")
            except (ValueError, OSError) as error:
                return {**base, "status": "invalid", "source": source, "error": str(error)}
            if not is_compatible(meta):
                return {**base, "status": "incompatible", "source": source, "version": meta["version"]}
            patterns = directory / "PATTERNS.md"
            return {**base, "status": "ready", "available": True, "resolved": tag, "source": source, "path": str(directory.resolve()), "guide": str((directory / "GUIDE.md").resolve()), "examples": str((directory / "examples.md").resolve()), "patterns": str(patterns.resolve()) if patterns.is_file() else None, "quality": meta["quality"], "version": meta["version"], "format_version": meta["format_version"]}
    return {**base, "status": "missing"}


def inventory(data_dir=None, project=None) -> dict:
    packs = []
    for source, root in roots(data_dir, project):
        no_links(root)
        if not root.exists():
            continue
        for item in sorted(root.iterdir()):
            try:
                meta = validate(item, compatible=False)
                if item.name != meta["id"]:
                    raise PackError("Directory ID differs from metadata ID")
                compatible = is_compatible(meta)
                packs.append({**meta, "source": source, "status": "ready" if compatible else "incompatible"})
            except (ValueError, OSError) as error:
                packs.append({"id": item.name, "source": source, "status": "invalid", "error": str(error)})
    return {"status": "listed", "packs": packs}


def data_root(data_dir=None, project=None) -> Path:
    root = (Path(project).absolute() / ".yaya") if project else (Path(data_dir).absolute() if data_dir else Path.home() / ".yaya")
    no_links(root)
    root = root.resolve()
    if root == CORE or root.is_relative_to(CORE):
        raise PackError("External packs must be outside the core Skill directory")
    root.mkdir(parents=True, exist_ok=True)
    return root


def backup(destination: Path, root: Path, identifier: str) -> Path:
    parent = inside(root / "backups" / identifier, root)
    parent.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    target = inside(parent / (stamp + "-" + uuid.uuid4().hex), root)
    inside(destination, root).rename(target)
    return target


def same_pack(a: Path, b: Path) -> bool:
    names = {p.name for p in a.iterdir()}
    return names == {p.name for p in b.iterdir()} and all((a / n).read_bytes() == (b / n).read_bytes() for n in names)


def validate_existing(path: Path, identifier: str) -> None:
    if validate(path, compatible=False)["id"] != identifier:
        raise PackError("Directory ID differs from metadata ID")


def restore_previous(previous: Path | None, destination: Path, operation_error: OSError) -> None:
    if previous is None:
        return
    try:
        previous.rename(destination)
    except OSError as restore_error:
        raise PackError(
            f"Operation failed: {operation_error}. Automatic restoration also failed: {restore_error}. "
            f"Previous pack remains at {previous}; restore it before retrying."
        ) from restore_error


def install(archive: Path, checksum: str, data_dir=None, project=None, replace=False) -> dict:
    if not re.fullmatch(r"[0-9a-fA-F]{64}", checksum):
        raise PackError("Provide a SHA-256 from a trusted release catalog")
    if archive.stat().st_size > MAX_ARCHIVE:
        raise PackError("Archive exceeds 8 MiB")
    with archive.open("rb") as stream:
        raw = stream.read(MAX_ARCHIVE + 1)
    if len(raw) > MAX_ARCHIVE:
        raise PackError("Archive exceeds 8 MiB")
    if hashlib.sha256(raw).hexdigest() != checksum.lower():
        raise PackError("SHA-256 mismatch")
    root = data_root(data_dir, project)
    stage = Path(tempfile.mkdtemp(prefix=".stage-", dir=root))
    previous = None
    try:
        # Open the verified bytes so a later archive change cannot alter this install.
        import io
        with zipfile.ZipFile(io.BytesIO(raw)) as zf:
            members = zf.infolist()
            names = [member.filename for member in members]
            if len(names) != len(set(n.casefold() for n in names)):
                raise PackError("Duplicate or case-colliding archive members")
            if not REQUIRED <= set(names) or not set(names) <= ALLOWED:
                raise PackError("Unexpected archive members; packs have a flat, fixed file layout")
            if sum(m.file_size for m in members) > MAX_TOTAL:
                raise PackError("Expanded pack exceeds 2 MiB")
            for member in members:
                mode = member.external_attr >> 16
                if member.flag_bits & 1 or member.is_dir() or member.file_size > MAX_FILE or stat.S_ISLNK(mode):
                    raise PackError("Encrypted, linked, oversized or directory member")
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise PackError("Archive contains a special file")
                if PurePosixPath(member.filename).name != member.filename or "\\" in member.filename:
                    raise PackError("Unsafe archive path")
                inside(stage / member.filename, root).write_bytes(zf.read(member))
        meta = validate(stage)
        destination = inside(root / "language-packs" / meta["id"], root)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            validate_existing(destination, meta["id"])
            if same_pack(stage, destination):
                return {"status": "unchanged", "id": meta["id"], "path": str(destination)}
            if not replace:
                raise PackError("Pack already exists; use --replace for a reversible update")
            previous = backup(destination, root, meta["id"])
        try:
            stage.rename(destination)
        except OSError as error:
            restore_previous(previous, destination, error)
            raise
        return {"status": "installed", "id": meta["id"], "path": str(destination), "backup": str(previous) if previous else None}
    finally:
        if stage.exists():
            pending_error = sys.exc_info()[1]
            try:
                shutil.rmtree(inside(stage, root))
            except (ValueError, OSError) as cleanup_error:
                context = f"{pending_error}. " if pending_error else ""
                raise PackError(f"{context}Temporary pack cleanup failed at {stage}: {cleanup_error}") from cleanup_error


def remove(identifier: str, data_dir=None, project=None) -> dict:
    pack_id(identifier)
    root = data_root(data_dir, project)
    destination = inside(root / "language-packs" / identifier, root)
    if not destination.exists():
        return {"status": "missing", "id": identifier}
    validate_existing(destination, identifier)
    previous = backup(destination, root, identifier)
    return {"status": "removed", "id": identifier, "backup": str(previous)}


def rollback(identifier: str, data_dir=None, project=None) -> dict:
    pack_id(identifier)
    root = data_root(data_dir, project)
    parent = inside(root / "backups" / identifier, root)
    choices = sorted(parent.iterdir(), reverse=True) if parent.exists() else []
    if not choices:
        raise PackError("No backup for this language")
    source = inside(choices[0], root)
    meta = validate(source)
    if meta["id"] != identifier:
        raise PackError("Backup ID mismatch")
    destination = inside(root / "language-packs" / identifier, root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous = None
    if destination.exists():
        validate_existing(destination, identifier)
        previous = backup(destination, root, identifier)
    try:
        source.rename(destination)
    except OSError as error:
        restore_previous(previous, destination, error)
        raise
    return {"status": "restored", "id": identifier, "path": str(destination), "backup": str(previous) if previous else None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("validate")
    check.add_argument("directory", type=Path)
    for name in ("resolve", "list", "install", "remove", "rollback"):
        command = commands.add_parser(name)
        locations = command.add_mutually_exclusive_group() if name in {"install", "remove", "rollback"} else command
        locations.add_argument("--data-dir")
        locations.add_argument("--project")
        if name == "resolve":
            command.add_argument("--language", required=True)
        elif name == "install":
            command.add_argument("archive", type=Path)
            command.add_argument("--sha256", required=True)
            command.add_argument("--replace", action="store_true")
        elif name in {"remove", "rollback"}:
            command.add_argument("id")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            result = {"status": "valid", "pack": validate(args.directory)}
        elif args.command == "resolve":
            result = resolve(args.language, args.data_dir, args.project)
        elif args.command == "list":
            result = inventory(args.data_dir, args.project)
        elif args.command == "install":
            result = install(args.archive, args.sha256, args.data_dir, args.project, args.replace)
        elif args.command == "remove":
            result = remove(args.id, args.data_dir, args.project)
        else:
            result = rollback(args.id, args.data_dir, args.project)
        print(json.dumps(result, ensure_ascii=True))
        return 0 if result["status"] not in {"invalid", "incompatible"} else 1
    except (ValueError, OSError, zipfile.BadZipFile, RuntimeError) as error:
        print(json.dumps({"status": "error", "error": str(error)}, ensure_ascii=True))
        return 1


if __name__ == "__main__":
    sys.exit(main())

"""Audit rebuilt refinement archives and byte costs without running a model."""
from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path, PurePosixPath
import platform
import stat
import sys
import zipfile

sys.dont_write_bytecode = True
OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
CORE = ROOT / "core/yaya"
DIST = ROOT / "dist"
BACKUP = ROOT / ".tmp/pre-refinement-0.2"
sys.path.insert(0, str(ROOT / ".tmp/validation-deps"))
from jsonschema import Draft202012Validator


def digest(data):
    return hashlib.sha256(data).hexdigest()


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


baseline = load(ROOT / ".tmp/refinement-release-baseline.json")
issues = []
commands = {
    name: load(OUT / filename)
    for name, filename in (
        ("quick_validate", "quick-validate-refinement.json"),
        ("release_tests", "test-release-refinement.json"),
        ("build", "build-release-refinement.json"),
    )
}
for name, result in commands.items():
    if result["returncode"]:
        issues.append(f"Command failed: {name}")

spec = importlib.util.spec_from_file_location("refinement_packs", CORE / "scripts/packs.py")
packs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packs)
version = load(CORE / "version.json")
if version != {"version": "0.2.0", "pack_format": 1, "core_major": 0}:
    issues.append("Unexpected core version or pack format")

catalog = load(DIST / "catalog.json")
assets = [catalog["core"], *catalog["language_packs"]]
checksums = {}
for line in (DIST / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    checksum, filename = line.split("  ", 1)
    if filename in checksums:
        issues.append(f"Duplicate SHA256SUMS member: {filename}")
    checksums[filename] = checksum
expected_dist = {"catalog.json", "SHA256SUMS", *(asset["file"] for asset in assets)}
if {p.name for p in DIST.iterdir()} != expected_dist:
    issues.append("Unexpected dist file set")
if set(checksums) != {asset["file"] for asset in assets}:
    issues.append("SHA256SUMS file set differs from catalog")

archive_rows = []
for asset in assets:
    is_core = asset is catalog["core"]
    source = CORE if is_core else ROOT / "language-packs" / asset["id"]
    expected = {
        ("yaya/" if is_core else "") + p.relative_to(source).as_posix(): p
        for p in source.rglob("*")
        if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
    }
    path = DIST / asset["file"]
    raw = path.read_bytes()
    archive_hash = digest(raw)
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        file_set_equal = set(names) == set(expected) and len(names) == len(set(names))
        layout_valid = all(
            not info.is_dir()
            and not PurePosixPath(info.filename).is_absolute()
            and ".." not in PurePosixPath(info.filename).parts
            and "\\" not in info.filename
            and stat.S_IFMT(info.external_attr >> 16) == stat.S_IFREG
            and (info.filename.startswith("yaya/") if is_core else "/" not in info.filename)
            for info in infos
        )
        members = []
        for name in names:
            member_hash = digest(archive.read(name))
            source_hash = digest(expected[name].read_bytes()) if name in expected else None
            members.append({
                "member": name, "archive_sha256": member_hash,
                "source_sha256": source_hash, "equal": member_hash == source_hash,
            })
        byte_match = all(item["equal"] for item in members)
        catalog_match = asset["sha256"] == archive_hash and asset["bytes"] == len(raw)
        checksum_match = checksums.get(path.name) == archive_hash
        passed = file_set_equal and layout_valid and byte_match and catalog_match and checksum_match
        row = {
            "file": path.name, "sha256": archive_hash, "bytes": len(raw),
            "source_file_count": len(expected), "archive_file_count": len(names),
            "file_set_equal": file_set_equal, "layout_valid": layout_valid,
            "source_bytes_equal": byte_match, "catalog_equal": catalog_match,
            "sha256sums_equal": checksum_match,
            "unchanged_from_prebuild": baseline["dist"].get(path.name, {}).get("sha256") == archive_hash,
            "files": members, "passed": passed,
        }
        if not is_core:
            metadata = json.loads(archive.read("pack.json"))
            row["metadata"] = metadata
            if any(asset.get(key) != value for key, value in metadata.items()):
                row["passed"] = False
                issues.append(f"Catalog metadata differs: {path.name}")
        archive_rows.append(row)
        if not row["passed"]:
            issues.append(f"Archive mismatch: {path.name}")

schema_path = ROOT / "schemas/language-pack.schema.json"
schema = load(schema_path)
Draft202012Validator.check_schema(schema)
schema_files = sorted(p.name for p in (ROOT / "schemas").glob("language-pack*.json"))
if schema_files != ["language-pack.schema.json"] or schema["properties"]["format_version"].get("const") != 1:
    issues.append("Expected one format 1 language-pack schema")
validator = Draft202012Validator(schema)
pack_directories = [
    CORE / "languages/en", CORE / "languages/zh-Hans",
    *(ROOT / "language-packs" / tag for tag in ("ja", "ko", "zh-Hant")),
]
pack_rows = []
for directory in [*pack_directories, ROOT / "templates/language-pack"]:
    metadata = load(directory / "pack.json")
    errors = [error.message for error in validator.iter_errors(metadata)]
    checked = packs.validate(directory) if directory in pack_directories else None
    passed = not errors and metadata["format_version"] == 1 and metadata["core_major"] == 0
    if checked is not None:
        passed = passed and checked == metadata
    pack_rows.append({
        "directory": directory.relative_to(ROOT).as_posix(),
        "metadata_sha256": digest((directory / "pack.json").read_bytes()),
        "schema_passed": not errors, "format_version": metadata["format_version"],
        "core_major": metadata["core_major"],
        "directory_validation": "passed" if checked is not None else "not_run_template_has_contributor_files",
        "errors": errors, "passed": passed,
    })
    if not passed:
        issues.append(f"Pack validation failed: {directory}")

core_zip = DIST / catalog["core"]["file"]
old_zip = BACKUP / core_zip.name
with zipfile.ZipFile(old_zip) as old, zipfile.ZipFile(core_zip) as new:
    old_names, new_names = set(old.namelist()), set(new.namelist())
    changed = [
        {
            "member": name, "before_sha256": digest(old.read(name)), "after_sha256": digest(new.read(name)),
            "before_bytes": len(old.read(name)), "after_bytes": len(new.read(name)),
        }
        for name in sorted(old_names & new_names)
        if old.read(name) != new.read(name)
    ]
    expected_changed = {"yaya/references/humanize.md", "yaya/languages/zh-Hans/PATTERNS.md"}
    change_scope_valid = old_names == new_names and {row["member"] for row in changed} == expected_changed
    if not change_scope_valid:
        issues.append("Core delta exceeds the two intended guidance files")
    backup_guides_equal = all(
        (BACKUP / name.removeprefix("yaya/")).read_bytes() == old.read(name)
        for name in expected_changed
    )
    if not backup_guides_equal:
        issues.append("Backup guides differ from backup archive")

preservation = []
for relative, prior in baseline["preserved"].items():
    current = digest((ROOT / relative).read_bytes())
    preservation.append({"file": relative, "before_sha256": prior, "after_sha256": current, "equal": prior == current})
    if current != prior:
        issues.append(f"Protected historical evidence changed: {relative}")

old_cost = load(OUT / "context-cost.json")
cost_rows = []
for row in old_cost["rows"]:
    files = [
        {"file": name, "bytes": (ROOT / name).stat().st_size, "sha256": digest((ROOT / name).read_bytes())}
        for name in row["files"]
    ]
    total = sum(item["bytes"] for item in files)
    cost_rows.append({
        "task": row["task"], "language": row["language"], "before_bytes": row["bytes"],
        "bytes": total, "delta_bytes": total - row["bytes"], "files": files,
    })
cost = {
    "date": "2026-10-20", "unit": "UTF-8 bytes, not tokens",
    "scope": old_cost["scope"], "baseline": "context-cost.json",
    "baseline_sha256": digest((OUT / "context-cost.json").read_bytes()),
    "core_archive_sha256": digest(core_zip.read_bytes()), "rows": cost_rows,
    "limitations": [
        "Byte totals are static file sizes, not measured model input tokens or quality.",
        "Optional extra guidance, host prompts, user input, and tool output are excluded.",
    ],
}
evidence = {
    "date": "2026-10-20", "status": "passed" if not issues else "failed", "issues": issues,
    "environment": {"python": platform.python_version(), "platform": platform.platform()},
    "commands": commands, "core_version": version, "archives": archive_rows,
    "schema": {"file": schema_path.relative_to(ROOT).as_posix(), "sha256": digest(schema_path.read_bytes()),
               "files": schema_files, "format_version_const": 1, "packs": pack_rows},
    "core_delta": {"backup_archive": old_zip.relative_to(ROOT).as_posix(),
                   "before_sha256": digest(old_zip.read_bytes()), "after_sha256": digest(core_zip.read_bytes()),
                   "file_set_unchanged": old_names == new_names, "changed": changed,
                   "only_intended_guidance_changed": change_scope_valid, "backup_guides_equal": backup_guides_equal},
    "preserved_evidence": preservation,
    "dist_files": {p.name: {"sha256": digest(p.read_bytes()), "bytes": p.stat().st_size} for p in sorted(DIST.iterdir())},
    "limits": ["No model execution or semantic effectiveness evaluation.", "Three Windows symlink subtests were skipped for missing host privilege."],
}
save(OUT / "release-refinement.json", evidence)
save(OUT / "context-cost-refinement.json", cost)
print(json.dumps({
    "status": evidence["status"], "archive_files": sum(row["archive_file_count"] for row in archive_rows),
    "archives": len(archive_rows), "pack_metadata_valid": sum(row["passed"] for row in pack_rows),
    "core_changed_members": [row["member"] for row in changed],
    "humanize_byte_costs": [{k: row[k] for k in ("language", "before_bytes", "bytes", "delta_bytes")} for row in cost_rows if row["task"] == "humanize"],
    "preserved_evidence": all(row["equal"] for row in preservation), "issues": issues,
}, ensure_ascii=True, indent=2))
raise SystemExit(0 if not issues else 1)

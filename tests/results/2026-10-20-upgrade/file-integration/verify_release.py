"""Read-only dist/source/schema audit; jsonschema is a validation dependency only."""
import hashlib
import json
from pathlib import Path
import sys
import zipfile

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
assert ROOT == (REPO / "tests/results/2026-10-20-upgrade/file-integration").resolve()
DEPS = REPO / ".tmp/validation-deps"
sys.path.insert(0, str(DEPS))
import jsonschema
from jsonschema import Draft202012Validator

sha256 = lambda data: hashlib.sha256(data).hexdigest()
dist, core = REPO / "dist", REPO / "core/yaya"
issues = []
core_archive = dist / "yaya-core-0.2.0.zip"
expected = {
    "yaya/" + p.relative_to(core).as_posix(): p
    for p in core.rglob("*")
    if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
}
with zipfile.ZipFile(core_archive) as archive:
    names = [info.filename for info in archive.infolist() if not info.is_dir()]
    if len(names) != len(set(names)):
        issues.append("Duplicate core archive members")
    if set(names) != set(expected):
        issues.append("Core/source file set differs")
    core_rows = []
    for name in names:
        source = expected.get(name)
        archived_hash = sha256(archive.read(name))
        source_hash = sha256(source.read_bytes()) if source else None
        equal = archived_hash == source_hash
        core_rows.append({"member": name, "archive_sha256": archived_hash,
                          "source_sha256": source_hash, "equal": equal})
        if not equal:
            issues.append("Core byte mismatch: " + name)

pack_rows = []
for language in ("ja", "ko", "zh-Hant"):
    path = dist / f"yaya-lang-{language}-0.2.0.zip"
    with zipfile.ZipFile(path) as archive:
        infos = archive.infolist()
        names = [item.filename for item in infos if not item.is_dir()]
        flat = all("/" not in item.filename and "\\" not in item.filename and not item.is_dir()
                   for item in infos)
        unique = len(names) == len(set(names))
        metadata = json.loads(archive.read("pack.json"))
        source = REPO / "language-packs" / language
        source_names = {p.name for p in source.iterdir() if p.is_file()}
        same_set = set(names) == source_names
        members = {name: {"archive_sha256": sha256(archive.read(name)),
                          "source_sha256": sha256((source / name).read_bytes())}
                   for name in names}
        source_equal = all(row["archive_sha256"] == row["source_sha256"] for row in members.values())
        valid = flat and unique and same_set and source_equal and metadata["format_version"] == 1
        pack_rows.append({"archive": path.name, "sha256": sha256(path.read_bytes()),
                          "members": members, "flat": flat, "unique": unique,
                          "source_file_set_equal": same_set, "source_bytes_equal": source_equal,
                          "format_version": metadata["format_version"], "passed": valid})
        if not valid:
            issues.append("Language archive mismatch: " + language)

schema_path = REPO / "schemas/language-pack.schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
Draft202012Validator.check_schema(schema)
validator = Draft202012Validator(schema)
metadata_paths = [
    "core/yaya/languages/en/pack.json",
    "core/yaya/languages/zh-Hans/pack.json",
    "language-packs/ja/pack.json",
    "language-packs/ko/pack.json",
    "language-packs/zh-Hant/pack.json",
    "templates/language-pack/pack.json",
]
schema_rows = []
for relative in metadata_paths:
    path = REPO / relative
    data = json.loads(path.read_text(encoding="utf-8"))
    errors = [{"path": list(error.absolute_path), "message": error.message}
              for error in validator.iter_errors(data)]
    valid = not errors and data["format_version"] == 1
    schema_rows.append({"file": relative, "sha256": sha256(path.read_bytes()),
                        "format_version": data["format_version"], "passed": valid,
                        "errors": errors})
    if not valid:
        issues.append("Schema validation failed: " + relative)
schema_files = sorted(p.relative_to(REPO).as_posix() for p in (REPO / "schemas").glob("language-pack*.json"))
if schema_files != ["schemas/language-pack.schema.json"] or schema["properties"]["format_version"].get("const") != 1:
    issues.append("Language schema is not singular format 1")

checksums = {}
for line in (dist / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
    digest, name = line.split(maxsplit=1)
    checksums[name.strip()] = digest
checksum_rows = {}
for archive in (core_archive, *(dist / row["archive"] for row in pack_rows)):
    checksum_rows[archive.name] = checksums.get(archive.name) == sha256(archive.read_bytes())
    if not checksum_rows[archive.name]:
        issues.append("SHA256SUMS differs: " + archive.name)

evidence = {
    "status": "passed" if not issues else "failed", "issues": issues,
    "core_archive": {"file": core_archive.name, "sha256": sha256(core_archive.read_bytes()),
                     "source_file_count": len(expected), "archive_file_count": len(core_rows),
                     "file_set_equal": set(names for names in expected) == {row["member"] for row in core_rows},
                     "files": core_rows},
    "language_archives": pack_rows,
    "schema": {"file": schema_path.relative_to(REPO).as_posix(),
               "sha256": sha256(schema_path.read_bytes()), "files": schema_files,
               "format_version_const": schema["properties"]["format_version"].get("const"),
               "metadata": schema_rows},
    "sha256sums": checksum_rows,
    "validation_dependency": {"jsonschema_module": jsonschema.__file__,
                               "dependency_directory": str(DEPS),
                               "product_files_modified": False},
}
(ROOT / "release-verification.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": evidence["status"], "core_files": len(core_rows),
                  "core_all_equal": all(row["equal"] for row in core_rows),
                  "flat_format1_packs": sum(row["passed"] for row in pack_rows),
                  "schema_metadata_passed": sum(row["passed"] for row in schema_rows),
                  "single_schema": schema_files, "sha256sums": checksum_rows,
                  "issues": issues}, ensure_ascii=True, indent=2))
raise SystemExit(0 if not issues else 1)

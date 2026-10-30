#!/usr/bin/env python3
"""Build reproducible local release assets; never upload or publish."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CORE = ROOT / "core" / "yaya"
sys.path.insert(0, str(CORE / "scripts"))
from yaya import load_catalog

spec = importlib.util.spec_from_file_location("yaya_packs", CORE / "scripts" / "packs.py")
packs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(packs)


def zip_files(destination: Path, items: list[tuple[str, Path]]) -> dict:
    packs.no_links(destination)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, path in sorted(items):
            packs.no_links(path)
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, path.read_bytes(), compresslevel=9)
    raw = destination.read_bytes()
    return {"file": destination.name, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def build(output: Path) -> dict:
    output = output.absolute()
    packs.no_links(output)
    output = output.resolve()
    # Never mix generated assets into source directories.
    if output == ROOT or any(output.is_relative_to(ROOT / p) for p in ("core", "language-packs", "templates", "scripts", "schemas", "tests", "evals", "docs")):
        raise ValueError("Choose a separate output directory, normally dist/")
    version_path = CORE / "version.json"
    packs.no_links(version_path)
    version = packs.strict_json(version_path.read_text(encoding="utf-8"), "version.json")
    if not {"version", "pack_format", "core_major"} <= set(version):
        raise ValueError("Core version.json is missing required metadata")
    if any(type(version[key]) is not int for key in ("pack_format", "core_major")):
        raise ValueError("Core pack_format and core_major must be integers")
    if not isinstance(version["version"], str) or not packs.SEMVER.fullmatch(version["version"]):
        raise ValueError("Core version must be SemVer")
    if version["pack_format"] != packs.FORMAT or version["core_major"] != packs.CORE_MAJOR:
        raise ValueError("Core version and pack compatibility constants disagree")
    if int(version["version"].split(".")[0]) != version["core_major"]:
        raise ValueError("core_major must equal the SemVer major version")
    bundled = sorted((CORE / "languages").iterdir())
    if {p.name for p in bundled} != {"en", "zh-Hans"}:
        raise ValueError("Core must bundle exactly en and zh-Hans")
    optional = sorted((ROOT / "language-packs").iterdir())
    for directory in bundled + optional:
        meta = packs.validate(directory)
        if meta["id"] != directory.name:
            raise ValueError("Pack directory must equal its ID")
    source_files = [CORE / name for name in (
        "SKILL.md", "LICENSE", "version.json", "agents/openai.yaml", "catalog.json",
        "scripts/packs.py", "scripts/check_comments.py", "scripts/detect_tells.py",
        "scripts/check_rewrite.py", "scripts/prose_scan.py", "scripts/tell_rules.json",
        "scripts/check_docstrings.py", "scripts/edit_evidence.py", "scripts/yaya.py",
    )]
    source_files.extend(sorted((CORE / "references").rglob("*.md")))
    for directory in bundled:
        source_files.extend(sorted(directory.iterdir()))
    for source in source_files:
        packs.no_links(source)
        if not source.is_file():
            raise ValueError(f"Required runtime file missing: {source.relative_to(CORE)}")
    load_catalog(CORE)
    output.mkdir(parents=True, exist_ok=True)
    # Reject existing links before writing any asset or index.
    for filename in [f"yaya-core-{version['version']}.zip", "catalog.json", "SHA256SUMS", *[f"yaya-lang-{p.name}-{packs.validate(p)['version']}.zip" for p in optional]]:
        packs.no_links(output / filename)
    core_items = [("yaya/" + p.relative_to(CORE).as_posix(), p) for p in source_files]
    core = {"version": version["version"], "bundled_languages": [p.name for p in bundled], **zip_files(output / f"yaya-core-{version['version']}.zip", core_items)}
    language_assets = []
    for directory in optional:
        meta = packs.validate(directory)
        asset = zip_files(output / f"yaya-lang-{meta['id']}-{meta['version']}.zip", [(p.name, p) for p in directory.iterdir()])
        language_assets.append({**meta, **asset})
    catalog = {"catalog_version": 1, "core": core, "language_packs": language_assets}
    (output / "catalog.json").write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    assets = [core, *language_assets]
    (output / "SHA256SUMS").write_text("".join(f"{a['sha256']}  {a['file']}\n" for a in assets), encoding="utf-8", newline="\n")
    return catalog


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    args = parser.parse_args()
    try:
        print(json.dumps(build(args.output), ensure_ascii=True, indent=2))
    except (ValueError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
"""Inspect this runtime without repairing it, reading user material or networking."""
from __future__ import annotations

import json
import argparse
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

CORE = Path(__file__).resolve().parents[1]
HELPERS = ("yaya.py", "packs.py", "prose_scan.py", "check_rewrite.py", "check_comments.py",
           "check_docstrings.py", "edit_evidence.py", "detect_tells.py", "doctor.py")


def diagnose(core=CORE):
    core = Path(core).resolve()
    checks = []

    def check(name, operation):
        try:
            detail = operation()
        except (OSError, ValueError, ImportError, SyntaxError, KeyError, TypeError, AttributeError) as exc:
            checks.append({"name": name, "status": "failed", "detail": str(exc)})
        else:
            checks.append({"name": name, "status": "passed", "detail": detail})

    checks.append({"name": "python", "status": "passed" if sys.version_info >= (3, 10) else "failed",
                   "detail": {"version": sys.version.split()[0], "minimum": "3.10"}})

    def files():
        required = ["SKILL.md", "LICENSE", "version.json", "catalog.json", "agents/openai.yaml",
                    "scripts/tell_rules.json", *("scripts/" + name for name in HELPERS)]
        missing = [name for name in required if not (core / name).is_file()]
        if missing:
            raise ValueError("Missing runtime files: " + ", ".join(missing))
        return {"required_files": len(required)}

    def version():
        from yaya import version_info
        return version_info(core)

    def catalog():
        from yaya import load_catalog
        value = load_catalog(core)
        return {"commands": list(value["commands"]), "domains": list(value["domains"])}

    def rules():
        from detect_tells import load_rules
        value = load_rules(core / "scripts/tell_rules.json")
        return {"rules": len(value), "languages": sorted({row["language"] for row in value})}

    def bundled():
        from packs import validate
        result = {}
        for tag in ("en", "zh-Hans"):
            meta = validate(core / "languages" / tag)
            if meta["id"] != tag:
                raise ValueError("Bundled language directory and ID disagree: " + tag)
            result[tag] = {key: meta[key] for key in ("version", "quality")}
        return result

    def links():
        guides = [core / "SKILL.md", *sorted((core / "references").rglob("*.md"))]
        guides += [core / "languages" / tag / name for tag in ("en", "zh-Hans")
                   for name in ("GUIDE.md", "PATTERNS.md")]
        checked = 0
        for guide in guides:
            for target in re.findall(r"\[[^\]\n]*\]\(([^()\s]+)\)", guide.read_text(encoding="utf-8")):
                parsed = urlsplit(target)
                if parsed.scheme or parsed.netloc or not parsed.path:
                    continue
                destination = (guide.parent / unquote(parsed.path)).resolve()
                if not destination.is_relative_to(core) or not destination.is_file():
                    raise ValueError(f"Broken local resource: {guide.relative_to(core)} -> {target}")
                checked += 1
        return {"local_file_links": checked, "anchors_checked": False}

    for name, operation in (("runtime-files", files), ("version", version), ("catalog", catalog),
                            ("tell-rules", rules), ("bundled-languages", bundled), ("guide-links", links)):
        check(name, operation)
    return {"status": "ready" if all(row["status"] == "passed" for row in checks) else "degraded",
            "runtime": str(core), "read_only": True, "checks": checks,
            "limitations": ["Checks local runtime structure, not editorial quality or host Skill discovery.",
                            "User/project language overrides, remote links and document anchors are not checked."]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is always emitted")
    parser.parse_args(argv)
    sys.dont_write_bytecode = True
    result = diagnose()
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())

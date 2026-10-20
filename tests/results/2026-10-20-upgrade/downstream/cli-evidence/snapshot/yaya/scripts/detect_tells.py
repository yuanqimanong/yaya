#!/usr/bin/env python3
"""Report literal wording candidates; never infer authorship or rewrite input."""

from __future__ import annotations

import bisect
import json
from pathlib import Path
import re
import sys

from prose_scan import InputError, JsonParser, LIMITATIONS, Unsupported, emit, read_utf8, snapshot

RULES_PATH = Path(__file__).with_name("tell_rules.json")


def load_rules():
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return data["rules"]


def detect(text, language):
    if language not in ("en", "zh-Hans"):
        return {"status": "unsupported", "language": language, "findings": [],
                "error": "Literal candidate detection supports en and zh-Hans only."}
    try:
        scan = snapshot(text, protect_quotes=True, strict_quotes=False)
    except (InputError, Unsupported) as exc:
        return {"status": "unsupported", "language": language, "findings": [],
                "error": str(exc), "limitations": LIMITATIONS}
    line_starts = [0] + [match.end() for match in re.finditer("\n", text)]
    findings = []
    for rule in load_rules():
        if rule["language"] != language:
            continue
        for phrase in rule["phrases"]:
            pattern = re.escape(phrase)
            if language == "en":
                pattern = r"(?<![A-Za-z])" + pattern + r"(?![A-Za-z])"
            for match in re.finditer(pattern, scan.masked, re.I if language == "en" else 0):
                findings.append({
                    "id": rule["id"], "severity": rule["severity"],
                    "line": bisect.bisect_right(line_starts, match.start()),
                    "quote": text[match.start():match.end()],
                    "message": rule["message"], "weak_alone": True,
                    "kind": "literal_candidate", "start": match.start(), "end": match.end(),
                })
    findings.sort(key=lambda item: (item["start"], item["id"]))
    return {
        "status": "ok", "language": language, "findings": findings,
        "metrics": {"characters": len(text), "candidates": len(findings),
                    "protected_spans": len(scan.spans)},
        "limitations": [
            "Literal candidates only: each needs contextual review; zero findings does not mean good writing.",
            "No authorship probability, semantic judgment, or instruction to delete a matching phrase.",
            "Code, quoted spans, blockquotes, tables, and recognized markup are excluded.",
            "Only paired quotes are excluded; unmatched quotation marks are treated as punctuation.",
        ] + LIMITATIONS[:2],
    }


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 file, or - for stdin")
    parser.add_argument("--language", required=True)
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is always emitted")
    parser.add_argument("--fail-on", choices=("P1", "P2"), help="Explicit candidate threshold for exit 1")
    args = parser.parse_args(argv)
    try:
        result = detect(read_utf8(args.file), args.language)
    except (InputError, OSError, ValueError, KeyError) as exc:
        result = {"status": "error", "error": str(exc)}
    emit(result)
    if result["status"] != "ok":
        return 2
    severity = {"P1": 1, "P2": 2}
    if args.fail_on and any(severity[item["severity"]] <= severity[args.fail_on] for item in result["findings"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

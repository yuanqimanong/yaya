#!/usr/bin/env python3
"""Report literal wording candidates; never infer authorship or rewrite input."""

from __future__ import annotations

import bisect
from pathlib import Path
import re
import sys

from prose_scan import InputError, JsonParser, LIMITATIONS, Unsupported, emit, read_utf8, snapshot
from packs import strict_json

RULES_PATH = Path(__file__).with_name("tell_rules.json")


def load_rules(path=None):
    data = strict_json((Path(path) if path else RULES_PATH).read_text(encoding="utf-8"), "tell_rules.json")
    if type(data.get("format_version")) is not int or data["format_version"] != 1:
        raise ValueError("Unsupported tell rule format_version")
    rules = data.get("rules")
    if not isinstance(rules, list) or not rules:
        raise ValueError("Tell rules must be a nonempty list")
    identifiers = set()
    for index, rule in enumerate(rules):
        context = f"tell_rules.json rules[{index}]"
        if not isinstance(rule, dict) or set(rule) != {"id", "language", "severity", "phrases", "message"}:
            raise ValueError(f"{context}: expected id, language, severity, phrases and message")
        if any(not isinstance(rule[key], str) or not rule[key].strip() for key in ("id", "language", "severity", "message")):
            raise ValueError(f"{context}: metadata must be nonempty strings")
        if rule["id"] in identifiers or not re.fullmatch(r"[a-z][a-z0-9-]*", rule["id"]):
            raise ValueError(f"{context}: invalid or duplicate rule id")
        identifiers.add(rule["id"])
        if rule["language"] not in {"en", "zh-Hans"} or rule["severity"] not in {"P1", "P2"}:
            raise ValueError(f"{context}: unsupported language or severity")
        phrases = rule["phrases"]
        if (not isinstance(phrases, list) or not phrases
                or any(not isinstance(value, str) or not value.strip() or "\n" in value or "\r" in value for value in phrases)):
            raise ValueError(f"{context}: phrases must be nonempty single-line strings")
        normalized = [value.casefold() if rule["language"] == "en" else value for value in phrases]
        if len(normalized) != len(set(normalized)):
            raise ValueError(f"{context}: duplicate phrases")
    return rules


def select_rules(rules, language, rule_ids=None):
    available = {rule["id"]: rule for rule in rules if rule["language"] == language}
    if rule_ids is None:
        return list(available.values())
    if isinstance(rule_ids, (str, bytes)):
        raise ValueError("Rule selection must be a list of rule IDs")
    try:
        selected = list(rule_ids)
    except TypeError as exc:
        raise ValueError("Rule selection must be a list of rule IDs") from exc
    if not selected or any(not isinstance(name, str) or name not in available for name in selected):
        raise ValueError(f"Choose rules for {language}: {', '.join(available)}")
    return [available[name] for name in dict.fromkeys(selected)]


def detect(text, language, rule_ids=None):
    if language not in ("en", "zh-Hans"):
        return {"status": "unsupported", "language": language, "findings": [],
                "error": "Literal candidate detection supports en and zh-Hans only."}
    rules = select_rules(load_rules(), language, rule_ids)
    try:
        scan = snapshot(text, protect_quotes=True, strict_quotes=False)
    except (InputError, Unsupported) as exc:
        return {"status": "unsupported", "language": language, "findings": [],
                "error": str(exc), "limitations": LIMITATIONS}
    line_starts = [0] + [match.end() for match in re.finditer("\n", text)]
    # Keep source offsets, but never let flexible whitespace bridge hidden markup.
    visible = list(scan.masked)
    for span in scan.spans:
        visible[span.start:span.end] = "\x00" * (span.end - span.start)
    visible = "".join(visible)
    findings = []
    for rule in rules:
        for phrase in rule["phrases"]:
            pattern = re.escape(phrase)
            if language == "en":
                pattern = pattern.replace(r"\ ", r"(?:[ \t]+|[ \t]*\r?\n[ \t]*)")
                # Unicode letters/digits extend words; underscores may be emphasis.
                pattern = r"(?<![^\W_])" + pattern + r"(?![^\W_])"
            for match in re.finditer(pattern, visible, re.I if language == "en" else 0):
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
        "enabled_rules": [rule["id"] for rule in rules],
        "metrics": {"characters": len(text), "candidates": len(findings),
                    "protected_spans": len(scan.spans)},
        "limitations": [
            "Literal candidates only: each needs contextual review; zero findings does not mean good writing.",
            "No authorship probability, semantic judgment, or instruction to delete a matching phrase.",
            "Code, quoted spans, blockquotes, tables, and recognized markup are excluded.",
            "Only paired quotes are excluded; unmatched quotation marks are treated as punctuation.",
            "English phrases allow spaces, tabs and soft line wraps, but not blank paragraphs or protected spans.",
        ] + LIMITATIONS[:2],
    }


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="-", help="UTF-8 file, or - for stdin")
    parser.add_argument("--language", required=True)
    parser.add_argument("--rule", action="append", help="Run only this rule ID; repeat to select more")
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is always emitted")
    parser.add_argument("--fail-on", choices=("P1", "P2"), help="Explicit candidate threshold for exit 1")
    args = parser.parse_args(argv)
    try:
        result = detect(read_utf8(args.file), args.language, args.rule)
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

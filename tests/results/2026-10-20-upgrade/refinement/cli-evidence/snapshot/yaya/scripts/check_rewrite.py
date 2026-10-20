#!/usr/bin/env python3
"""Compare mechanical prose protections; never modify either input file.

Exit 0: checked categories passed; 1: unauthorized changes; 2: error/unsupported.
This checker cannot verify semantics or fact-to-number associations.
"""

from __future__ import annotations

from collections import Counter
import sys

from prose_scan import InputError, JsonParser, LIMITATIONS, Unsupported, emit, numbers, read_utf8, snapshot

CATEGORIES = (
    "bom", "frontmatter", "fences", "inline_code", "link_targets", "html",
    "explicit_ids", "placeholders", "urls", "blockquotes", "tables", "quotes",
    "literals", "numbers",
)


def compare(before, after, allow=(), protect_quotes=False, literals=()):
    invalid = set(allow) - set(CATEGORIES)
    if invalid:
        raise InputError("Unknown allowed category: " + ", ".join(sorted(invalid)))
    if any(not literal or literal not in before for literal in literals):
        raise InputError("Each protected literal must be nonempty and present in BEFORE.")
    try:
        old_scan = snapshot(before, protect_quotes, literals)
        new_scan = snapshot(after, protect_quotes, literals)
    except Unsupported as exc:
        return {"status": "unsupported", "error": str(exc), "limitations": LIMITATIONS}
    old, new = old_scan.items(), new_scan.items()
    old["numbers"], new["numbers"] = numbers(old_scan), numbers(new_scan)
    changes = []
    for category in CATEGORIES:
        prior, current = old.get(category, []), new.get(category, [])
        equal = Counter(prior) == Counter(current) if category == "numbers" else prior == current
        if not equal:
            changes.append({
                "category": category, "allowed": category in allow,
                "before": prior, "after": current,
            })
    violations = [change for change in changes if not change["allowed"]]
    return {
        "status": "failed" if violations else "passed",
        "changed": before != after,
        "checked_categories": list(CATEGORIES),
        "quote_protection": protect_quotes,
        "allowed_categories": sorted(set(allow)),
        "changes": changes, "violations": violations,
        "limitations": LIMITATIONS + [
            "Numbers are compared as a multiset of number/recognized-unit lexemes in unprotected prose; unlisted units and reordered associations can pass.",
            "Protected spans are compared in source order within each category, not against surrounding prose or document structure.",
            "A pass says only that these mechanical checks found no unauthorized changes.",
        ],
    }


def check_files(before, after, allow=(), protect_quotes=False, literals=()):
    if str(before) == "-" and str(after) == "-":
        raise InputError("Only one input may use stdin.")
    return compare(read_utf8(before), read_utf8(after), allow, protect_quotes, literals)


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--language", help="Optional metadata only; mechanical checks are language independent")
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is always emitted")
    parser.add_argument("--allow", action="append", choices=CATEGORIES, default=[])
    parser.add_argument("--protect-quotes", action="store_true", help="Preserve paired double/curly/East Asian quoted spans")
    parser.add_argument("--protect-literal", action="append", default=[], help="Preserve exact occurrences; repeat for each literal")
    args = parser.parse_args(argv)
    try:
        result = check_files(args.before, args.after, args.allow, args.protect_quotes, args.protect_literal)
    except (InputError, OSError) as exc:
        result = {"status": "error", "error": str(exc), "limitations": LIMITATIONS}
    emit(result)
    return {"passed": 0, "failed": 1}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())

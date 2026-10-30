#!/usr/bin/env python3
"""Compare mechanical prose protections; never modify either input file.

Exit 0: checked categories passed; 1: unauthorized changes; 2: error/unsupported.
This checker cannot verify semantics or fact-to-number associations.
Recognizes decimal/scientific numerals with selected currencies, scales and units.
Compares literal spellings and counts; equivalent conversions still need review.
"""

from __future__ import annotations

from collections import Counter
import sys

from prose_scan import InputError, JsonParser, LIMITATIONS, MAX_BYTES, Unsupported, emit, numbers, read_utf8, snapshot
from edit_evidence import bound_check, exact_grant, strict_json

CATEGORIES = (
    "bom", "frontmatter", "fences", "inline_code", "link_targets", "html",
    "explicit_ids", "placeholders", "urls", "blockquotes", "tables", "quotes",
    "literals", "numbers", "task_markers", "link_roles",
)


def literal_values(literals):
    """Freeze one-shot inputs so both scans and evidence use the same values."""
    if isinstance(literals, (str, bytes)):
        raise InputError("Protected literals must be an iterable of strings, not one string.")
    try:
        values = tuple(literals)
    except TypeError as exc:
        raise InputError("Protected literals must be an iterable of strings.") from exc
    if any(not isinstance(value, str) or not value for value in values):
        raise InputError("Each protected literal must be a nonempty string.")
    return tuple(dict.fromkeys(values))


def compare(before, after, allow=(), protect_quotes=False, literals=()):
    literals = literal_values(literals)
    permitted = []
    if allow is not None and not (type(allow) is tuple and not allow):
        try:
            permitted = exact_grant(allow, before.encode("utf-8"), after.encode("utf-8"), "changes")
        except (TypeError, ValueError) as exc:
            raise InputError(str(exc)) from exc
        if any(not isinstance(entry, dict) or set(entry) != {"category", "before", "after"}
               or not isinstance(entry["category"], str) or entry["category"] not in CATEGORIES
               or not all(isinstance(entry[field], list) and all(isinstance(value, str) for value in entry[field])
                          for field in ("before", "after")) for entry in permitted):
            raise InputError("Allow entries must enumerate exact category/before/after differences.")
        if len({entry["category"] for entry in permitted}) != len(permitted):
            raise InputError("Duplicate authorized category difference.")
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
            difference = {"category": category, "before": prior, "after": current}
            changes.append({**difference, "allowed": difference in permitted})
    actual = [{key: change[key] for key in ("category", "before", "after")} for change in changes]
    if any(entry not in actual for entry in permitted):
        raise InputError("Grant contains a stale, unused, or inexact difference.")
    violations = [change for change in changes if not change["allowed"]]
    return {
        "status": "failed" if violations else "passed",
        "changed": before != after,
        "checked_categories": list(CATEGORIES),
        "quote_protection": protect_quotes,
        "authorized_differences": permitted,
        "changes": changes, "violations": violations,
        "limitations": LIMITATIONS + [
            "Numbers are compared as a multiset of literal quantities and recognized numeric dates/times; no unit, calendar or timezone conversion is inferred.",
            "Unlisted units, written-out numbers, decimal-comma/space-grouped notation, and reordered associations can pass; units/currencies on separate lines or in headers are not associated with values.",
            "Protected spans are compared in source order within each category, not against surrounding prose or document structure.",
            "A pass says only that these mechanical checks found no unauthorized changes.",
        ],
    }


def check_files(before, after, allow=(), protect_quotes=False, literals=()):
    literals = literal_values(literals)
    if str(before) == "-" and str(after) == "-":
        raise InputError("Only one input may use stdin.")
    operation = lambda: compare(read_utf8(before), read_utf8(after), allow, protect_quotes, literals)
    if str(before) == "-" or str(after) == "-":
        result = operation()
        result["evidence"] = {"status": "unbound", "reason": "stdin input has no stable file identity; save files for batch evidence."}
        return result
    return bound_check(before, after, __file__, operation,
                       {"allow": allow, "protect_quotes": protect_quotes, "literals": list(literals)},
                       max_bytes=MAX_BYTES)


def main(argv=None):
    parser = JsonParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after")
    parser.add_argument("--language", help="Optional metadata only; mechanical checks are language independent")
    parser.add_argument("--json", action="store_true", help="Compatibility flag; JSON is always emitted")
    parser.add_argument("--allow", help="Path to reviewed JSON binding exact file hashes and category differences; broad categories are rejected")
    parser.add_argument("--protect-quotes", action="store_true", help="Preserve paired double/curly/East Asian quoted spans")
    parser.add_argument("--protect-literal", action="append", default=[], help="Preserve exact occurrences; repeat for each literal")
    args = parser.parse_args(argv)
    try:
        grant = strict_json(args.allow) if args.allow else ()
        result = check_files(args.before, args.after, grant, args.protect_quotes, args.protect_literal)
    except (InputError, OSError, ValueError) as exc:
        result = {"status": "error", "error": str(exc), "limitations": LIMITATIONS}
    emit(result)
    return {"passed": 0, "failed": 1}.get(result["status"], 2)


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Check exact grants for Python docstring literals; never write source files.

Exit 0 passed, 1 failed, 2 unsupported. Use --inventory BEFORE.py to list nodes.
Only UTF-8 Python and single-token docstrings are supported. AST checks establish
mechanical scope, not factual accuracy or unchanged runtime behavior (__doc__).
"""

from __future__ import annotations

import argparse
import ast
import codecs
import doctest
import io
import json
from pathlib import Path
import re
import sys
import tokenize

from check_comments import UnsupportedSource, _snapshot
from edit_evidence import bound_check, content_info, digest, exact_grant, strict_json

LIMITATIONS = [
    "Only UTF-8 .py/.pyi accepted by the running interpreter; selected docstrings must be single STRING tokens.",
    "Only granted existing docstring values may change; other bytes and physical newline sequences are protected.",
    "Recognized doctests and the tail starting at an example/usage/code-block marker are protected, even within granted nodes.",
    "Unmarked examples and project-specific documentation syntax require manual review; example editing needs a separate check.",
    "AST equivalence proves only a mechanical implementation boundary, not comment correctness or invariant runtime behavior; __doc__ changes.",
]


def parse(data, filename):
    source = _snapshot(data, filename)
    if source.encoding not in {"utf-8", "utf-8-sig"}:
        raise UnsupportedSource("Docstring mode supports UTF-8 only; the declared source encoding differs.")
    try:
        text = data.decode("utf-8-sig")
    except UnicodeError as exc:
        raise UnsupportedSource("Docstring mode supports UTF-8 only; use a byte-preserving language-aware alternative.") from exc
    tree = ast.parse(text, filename=filename)
    lines = text.split("\n")
    offsets = [0]
    for line in lines[:-1]:
        offsets.append(offsets[-1] + len((line + "\n").encode("utf-8")))
    payload = data[3:] if data.startswith(codecs.BOM_UTF8) else data
    tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    def token_offset(position):
        line, column = position
        return offsets[line - 1] + len(lines[line - 1][:column].encode("utf-8"))
    strings = {(token_offset(tok.start), token_offset(tok.end)): tok.string
               for tok in tokens if tok.type == tokenize.STRING}
    docs = {}
    def visit(node, owners=()):
        scoped = isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        names = owners + ((node.name,) if hasattr(node, "name") and scoped else ())
        if scoped and node.body and isinstance(node.body[0], ast.Expr):
            value = node.body[0].value
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                start = offsets[value.lineno - 1] + value.col_offset
                end = offsets[value.end_lineno - 1] + value.end_col_offset
                selector = (".".join(names) if names else "<module>") + f"@{getattr(node, 'lineno', 1)}"
                docs[selector] = {"start": start, "end": end, "literal": payload[start:end],
                                  "single_token": (start, end) in strings,
                                  "value": value, "owner": node}
        for child in ast.iter_child_nodes(node):
            visit(child, names if scoped else owners)
    visit(tree)
    return tree, payload, docs


def examples(text):
    try:
        tests = doctest.DocTestParser().get_examples(text)
    except ValueError as exc:
        raise UnsupportedSource("Cannot conservatively parse docstring examples.") from exc
    protected = [(example.source, example.want, example.exc_msg, example.options, example.indent)
                 for example in tests]
    # Freeze a recognized example section in full, including output and prose.
    marker = re.compile(r"^\s*(?:```|~~~|>>>|\.\.\s+(?:code|code-block|sourcecode)::|(?:examples?|usage)\s*:?[ \t]*$)", re.I)
    lines = text.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if marker.search(line) or line.rstrip().endswith("::"):
            protected.append("".join(lines[index:]))
            break
    return protected


def shape(literal):
    match = re.match(rb"(?i)([ru]*)(\"\"\"|'''|\"|')", literal)
    if not match or not literal.endswith(match[2]):
        raise UnsupportedSource("Cannot map a docstring literal exactly.")
    return match[1], match[2]


def _check(before, after, grant):
    before, after = Path(before), Path(after)
    if before.suffix.lower() not in {".py", ".pyi"}:
        return {"status": "unsupported", "reason": "Use a host-language parser, exact diff review, and actual project checks."}
    old, new = before.read_bytes(), after.read_bytes()
    try:
        old_tree, old_payload, old_docs = parse(old, str(before))
    except (UnsupportedSource, SyntaxError, tokenize.TokenError) as exc:
        return {"status": "unsupported", "reason": f"Baseline: {exc}"}
    try:
        new_tree, new_payload, new_docs = parse(new, str(after))
    except (UnsupportedSource, SyntaxError, tokenize.TokenError) as exc:
        return {"status": "failed", "reason": f"Candidate: {exc}"}
    try:
        entries = exact_grant(grant, old, new, "docstrings")
        allowed = {}
        for entry in entries:
            if (not isinstance(entry, dict) or set(entry) != {"node", "before_sha256", "after_sha256"}
                    or not isinstance(entry["node"], str) or entry["node"] in allowed):
                raise ValueError("Each grant must name one unique exact node and both literal hashes.")
            name = entry["node"]
            if name not in old_docs or name not in new_docs:
                raise ValueError(f"Grant names a missing or moved docstring: {name}")
            prior, current = old_docs[name], new_docs[name]
            if (entry["before_sha256"] != digest(prior["literal"])
                    or entry["after_sha256"] != digest(current["literal"])
                    or prior["literal"] == current["literal"]):
                raise ValueError("Grant must describe an actual exact literal difference.")
            if not prior["single_token"] or not current["single_token"]:
                return {"status": "unsupported", "reason": "Concatenated docstring tokens need a separate token-aware review."}
            allowed[name] = entry
    except (TypeError, ValueError) as exc:
        return {"status": "failed", "reason": str(exc)}
    violations = []
    if old.startswith(codecs.BOM_UTF8) != new.startswith(codecs.BOM_UTF8):
        violations.append("BOM changed.")
    if re.findall(rb"\r\n|\n", old) != re.findall(rb"\r\n|\n", new):
        violations.append("Physical line count or line endings changed.")
    def mask(payload, docs):
        for name, doc in sorted(docs.items(), key=lambda x: x[1]["start"], reverse=True):
            if name in allowed:
                payload = payload[:doc["start"]] + b"<authorized-docstring>" + payload[doc["end"]:]
        return payload
    if mask(old_payload, old_docs) != mask(new_payload, new_docs):
        violations.append("Bytes outside authorized docstring literals changed (code, comments, strings, or whitespace).")
    try:
        for name in allowed:
            prior, current = old_docs[name], new_docs[name]
            if shape(prior["literal"]) != shape(current["literal"]):
                violations.append(f"{name}: literal prefix or quote delimiter changed.")
            if (examples(prior["value"].value) != examples(current["value"].value)
                    or examples(prior["literal"].decode("utf-8")) != examples(current["literal"].decode("utf-8"))):
                violations.append(f"{name}: protected examples changed.")
            prior["value"].value = "<authorized-docstring>"
            current["value"].value = "<authorized-docstring>"
    except UnsupportedSource as exc:
        return {"status": "unsupported", "reason": str(exc)}
    ast_equal = ast.dump(old_tree, include_attributes=False) == ast.dump(new_tree, include_attributes=False)
    if not ast_equal:
        violations.append("AST outside authorized docstring values changed.")
    return {"status": "failed" if violations else "passed", "violations": violations,
            "authorized_nodes": sorted(allowed), "ast_boundary_equal": ast_equal,
            "source_format": {"before": content_info(old), "candidate": content_info(new)}}


def check_files(before, after, grant=None):
    result = bound_check(before, after, __file__, lambda: _check(before, after, grant), options={"allow": grant})
    result["limitations"] = LIMITATIONS
    return result


def inventory(path):
    path = Path(path)
    if path.suffix.lower() not in {".py", ".pyi"}:
        raise UnsupportedSource("Only Python .py/.pyi is supported.")
    data = path.read_bytes()
    _, _, docs = parse(data, str(path))
    return {"status": "inventory", "source": content_info(data),
            "nodes": [{"node": name, "literal_sha256": digest(doc["literal"]),
                       "single_token": doc["single_token"]} for name, doc in docs.items()],
            "limitations": LIMITATIONS}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before")
    parser.add_argument("after", nargs="?")
    parser.add_argument("--allow", type=Path, help="Reviewed exact-node/candidate JSON grant")
    parser.add_argument("--inventory", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.inventory and args.after is None and args.allow is None:
            result = inventory(args.before)
        elif args.after is not None and not args.inventory:
            result = check_files(args.before, args.after, strict_json(args.allow) if args.allow else None)
        else:
            raise ValueError("Use --inventory BEFORE, or BEFORE AFTER --allow FILE.")
    except (OSError, ValueError, UnsupportedSource, SyntaxError) as exc:
        result = {"status": "unsupported", "reason": str(exc), "limitations": LIMITATIONS}
    print(json.dumps(result, ensure_ascii=True))
    return {"passed": 0, "inventory": 0, "failed": 1}.get(result["status"], 2)


if __name__ == "__main__":
    raise SystemExit(main())

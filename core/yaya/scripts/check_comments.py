#!/usr/bin/env python3
"""Check that a Python edit only changes ordinary # comments; never write files.

Usage: python check_comments.py BEFORE AFTER
The BEFORE suffix selects the language (.py/.pyi); AFTER may be a temporary file.
Exit codes: 0 passed, 1 failed, 2 unsupported (including unreadable input).
Requires Python 3.10+. A pass checks the edit boundary, not comment accuracy.
"""

from __future__ import annotations

import ast
import codecs
import io
import json
from pathlib import Path
import re
import sys
import tokenize
from dataclasses import dataclass


LIMITATIONS = [
    "Only .py/.pyi sources parseable by the running Python interpreter are supported.",
    "Only ordinary # comment text may change; line count, line endings, BOM, and all other bytes must remain identical.",
    "Docstrings, f-strings, t-strings, and doctests inside strings are immutable; recognized comment directives and comment doctest blocks are protected.",
    "Unknown external-tool directives cannot be exhaustively recognized; review the diff and run the host project's checks.",
    "A pass does not verify that comments are accurate, useful, or consistent with the code.",
    "LF and CRLF are supported; lone-CR newlines and encodings that cannot be mapped exactly are unsupported.",
]

_DIRECTIVE = re.compile(
    r"^\s*(?:[!@:]|%%|In\s*\[|"
    r"(?:type|noqa|nosec|nosemgrep|nosonar|noinspection|"
    r"pylint|pyright|mypy|ruff|fmt|isort|yapf|autopep8|black|"
    r"flake8|bandit|pyre(?:-ignore|-fixme)?|pytype|pragma|coverage|"
    r"doctest|cython|distutils|numba|cspell|spellchecker|codespell|"
    r"sourcery|region|endregion|TODO|FIXME|XXX|HACK|"
    r"SPDX-License-Identifier|SPDX-FileCopyrightText|copyright)\b)",
    re.IGNORECASE,
)
_COOKIE = re.compile(r"coding\s*[:=]", re.IGNORECASE)
_DOCTEST = re.compile(r"^#\s*(?:>>>|\.\.\.)(?:\s|$)")


@dataclass(frozen=True)
class Comment:
    prefix: bytes
    body: bytes
    suffix: bytes
    text: str
    full_line: bool


@dataclass(frozen=True)
class Snapshot:
    lines: list[bytes]
    comments: dict[int, Comment]
    protected: set[int]
    encoding: str
    bom: bytes


class UnsupportedSource(Exception):
    """The source cannot be checked conservatively with this interpreter."""


def _lf_lines(value):
    """Split only at LF; retain CR and every other source character verbatim."""
    separator = b"\n" if isinstance(value, bytes) else "\n"
    pieces = value.split(separator)
    return [piece + separator for piece in pieces[:-1]] + (
        [pieces[-1]] if pieces[-1] else []
    )


def _snapshot(data: bytes, filename: str) -> Snapshot:
    if re.search(rb"\r(?!\n)", data):
        raise UnsupportedSource("Lone-CR newlines cannot be checked.")
    try:
        encoding, _ = tokenize.detect_encoding(io.BytesIO(data).readline)
        encoding = codecs.lookup(encoding).name
        text = data.decode(encoding)
        # Validate with the same interpreter that supplies tokenize.
        ast.parse(data, filename=filename)
        tokens = list(tokenize.tokenize(io.BytesIO(data).readline))
    except (SyntaxError, UnicodeError, LookupError, ValueError, tokenize.TokenError) as exc:
        raise UnsupportedSource(
            f"Source is not valid Python for this interpreter ({type(exc).__name__})."
        ) from exc

    bom = codecs.BOM_UTF8 if data.startswith(codecs.BOM_UTF8) else b""
    payload = data[len(bom) :]
    fragment_encoding = "utf-8" if encoding == "utf-8-sig" else encoding
    lines = _lf_lines(payload)
    text_lines = _lf_lines(text)
    if len(lines) != len(text_lines):
        raise UnsupportedSource("Source encoding does not preserve physical line boundaries.")

    comments: dict[int, Comment] = {}
    protected: set[int] = set()
    interpolation_depth = 0
    for token in tokens:
        token_name = tokenize.tok_name.get(token.type)
        if token_name in {"FSTRING_START", "TSTRING_START"}:
            interpolation_depth += 1
        elif token_name in {"FSTRING_END", "TSTRING_END"}:
            interpolation_depth -= 1
        if token.type != tokenize.COMMENT:
            continue
        row, start = token.start
        end_row, end = token.end
        if row != end_row or row in comments or not 1 <= row <= len(lines):
            raise UnsupportedSource("Comment token cannot be mapped to one physical line.")
        line = text_lines[row - 1]
        pieces = (line[:start], line[start:end], line[end:])
        try:
            prefix, body, suffix = (piece.encode(fragment_encoding) for piece in pieces)
        except (UnicodeError, LookupError) as exc:
            raise UnsupportedSource("Comment encoding cannot be mapped exactly.") from exc
        # Do not infer byte positions from character columns or normalize source bytes.
        if prefix + body + suffix != lines[row - 1] or pieces[1] != token.string:
            raise UnsupportedSource("Comment encoding cannot be mapped exactly.")
        comment = Comment(prefix, body, suffix, token.string, not pieces[0].strip())
        comments[row] = comment
        content = token.string[1:]
        if (
            interpolation_depth
            or any(_DIRECTIVE.search(part) for part in content.split("#"))
            or (row <= 2 and _COOKIE.search(content))
        ):
            protected.add(row)

    # A commented doctest includes its output lines, not just its >>> prompt.
    block: list[int] = []

    def protect_doctest_block() -> None:
        if any(_DOCTEST.match(comments[row].text) for row in block):
            protected.update(block)

    for row, comment in comments.items():
        if not comment.full_line:
            protect_doctest_block()
            block = []
            if _DOCTEST.match(comment.text):
                protected.add(row)
        else:
            if block and row != block[-1] + 1:
                protect_doctest_block()
                block = []
            block.append(row)
    protect_doctest_block()
    return Snapshot(lines, comments, protected, encoding, bom)


def _result(status: str, **details) -> dict:
    return {"status": status, "language": "python", **details, "limitations": LIMITATIONS}


def _check_files(before: Path | str, after: Path | str) -> dict:
    """Read two files and return a JSON-serializable result without modifying them."""
    before, after = Path(before), Path(after)
    if before.suffix.lower() not in {".py", ".pyi"}:
        return _result(
            "unsupported",
            reason="Only Python .py/.pyi baselines are supported; use a host-language parser and review the candidate diff.",
        )
    try:
        original_bytes, candidate_bytes = before.read_bytes(), after.read_bytes()
    except OSError as exc:
        return _result("unsupported", reason=f"Cannot read input files ({type(exc).__name__}).")
    try:
        original = _snapshot(original_bytes, str(before))
    except UnsupportedSource as exc:
        return _result("unsupported", reason=f"Baseline: {exc}")
    try:
        candidate = _snapshot(candidate_bytes, str(after))
    except UnsupportedSource as exc:
        return _result("failed", violations=[{"reason": f"Candidate: {exc}"}])

    violations: list[dict] = []
    changed: list[int] = []
    if original.encoding != candidate.encoding or original.bom != candidate.bom:
        violations.append({"reason": "Source encoding or BOM changed."})
    if len(original.lines) != len(candidate.lines):
        violations.append({"reason": "Physical line count changed."})
    for row, (old_line, new_line) in enumerate(zip(original.lines, candidate.lines), start=1):
        if old_line == new_line:
            continue
        old, new = original.comments.get(row), candidate.comments.get(row)
        if old is None or new is None:
            violations.append({"line": row, "reason": "A non-comment byte or comment boundary changed."})
        elif row in original.protected or row in candidate.protected:
            violations.append({"line": row, "reason": "A protected directive, doctest, or interpolated-string comment changed."})
        elif old.prefix != new.prefix or old.suffix != new.suffix:
            violations.append({"line": row, "reason": "Bytes outside the comment changed (including whitespace or line endings)."})
        else:
            changed.append(row)
    return _result(
        "failed" if violations else "passed",
        changed_comment_lines=changed,
        violations=violations,
    )


def check_files(before: Path | str, after: Path | str) -> dict:
    from edit_evidence import bound_check
    return bound_check(before, after, __file__, lambda: _check_files(before, after))


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        result = _result("unsupported", reason="Usage: python check_comments.py BEFORE AFTER")
    else:
        result = check_files(args[0], args[1])
    # ASCII escaping keeps JSON usable even on a non-UTF-8 Windows console.
    print(json.dumps(result, ensure_ascii=True))
    return {"passed": 0, "failed": 1, "unsupported": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())

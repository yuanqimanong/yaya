#!/usr/bin/env python3
"""Conservative source spans for yaya's read-only prose tools (Python 3.10+).

This is a bounded Markdown subset, not a CommonMark parser. Ambiguous constructs
return unsupported instead of being silently treated as editable prose.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys

MAX_BYTES = 2 * 1024 * 1024
LIMITATIONS = [
    "Checks a conservative Markdown subset, not a full CommonMark/HTML parser.",
    "Indented blocks, nested containers with fences, footnotes, multiline links, and raw HTML blocks are unsupported.",
    "Blockquotes (including lazy continuation lines) are protected; ordinary quoted prose is protected only with --protect-quotes or --protect-literal.",
    "Literal equality cannot verify facts, attribution, negation, conditions, author identity, or number-to-entity associations.",
    "Unmarked identifiers, paths, and names require explicit --protect-literal when their exact spelling must be preserved.",
]


class InputError(ValueError):
    """Unreadable or invalid bounded UTF-8 input."""


class Unsupported(ValueError):
    """The source is outside the supported subset."""


class JsonParser(argparse.ArgumentParser):
    def error(self, message):
        emit({"status": "error", "error": message})
        raise SystemExit(2)


def emit(value):
    # ASCII escapes make output usable even on non-UTF-8 Windows consoles.
    print(json.dumps(value, ensure_ascii=True, indent=2))


def validate_text(text):
    if not isinstance(text, str):
        raise InputError("Input must be text.")
    try:
        size = len(text.encode("utf-8"))
    except UnicodeEncodeError as exc:
        raise InputError("Input must be valid UTF-8 text.") from exc
    if size > MAX_BYTES:
        raise InputError("Input exceeds 2 MiB.")
    if "\x00" in text or re.search(r"\r(?!\n)", text):
        raise InputError("NUL and lone-CR newlines are unsupported.")
    return text


def read_utf8(path):
    try:
        if str(path) == "-":
            raw = sys.stdin.buffer.read(MAX_BYTES + 1)
        else:
            with Path(path).open("rb") as stream:
                raw = stream.read(MAX_BYTES + 1)
    except OSError as exc:
        raise InputError(f"Cannot read input ({type(exc).__name__}).") from exc
    if len(raw) > MAX_BYTES:
        raise InputError("Input exceeds 2 MiB.")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Input must be valid UTF-8.") from exc
    return validate_text(text)


@dataclass(frozen=True)
class Span:
    start: int
    end: int
    category: str
    value: str


@dataclass
class Snapshot:
    text: str
    spans: list[Span]
    masked: str

    def items(self):
        result = {}
        for span in sorted(self.spans, key=lambda item: (item.start, item.end)):
            result.setdefault(span.category, []).append(span.value)
        return result


_FENCE = re.compile(r" {0,3}(`{3,}|~{3,})(.*)$")
_HTML_START = re.compile(r"</?[A-Za-z][A-Za-z0-9:-]*(?=[\s/>])")
_HTML_LIKE = re.compile(r"</?[A-Za-z!]")
_RAW_HTML = re.compile(
    r"</?(?:script|style|pre|textarea|div|table|section|article|details|iframe|"
    r"address|aside|body|blockquote|caption|center|col|colgroup|dd|dialog|dir|dl|dt|"
    r"fieldset|figcaption|figure|footer|form|frame|frameset|h[1-6]|head|header|hr|html|"
    r"legend|li|link|main|menu|nav|ol|optgroup|option|p|param|summary|tbody|td|tfoot|"
    r"th|thead|title|tr|ul)\b", re.I)
# A leading zero belongs to width; overlapping zero flags/width cause quadratic
# backtracking on long invalid fields. Unusual flag orders need explicit literals.
_PRINTF = (r"%%|%(?:\([A-Za-z_]\w{0,63}\)|[1-9]\d*\$)?[#+\-]*"
           r"(?:\d+|\*(?:[1-9]\d*\$)?)?(?:\.(?:\d+|\*(?:[1-9]\d*\$)?))?"
           r"[hlL]?[diouxXeEfFgGcrsa](?![A-Za-z])")
_PLACEHOLDER = re.compile(r"\{\{[^{}\r\n]{1,256}\}\}|\$\{[^{}\r\n]{1,256}\}|"
                          + _PRINTF + r"|(?<![\w:]):[A-Za-z_]\w{0,63}\b")
_URL = re.compile(r"https?://[^\s<>\"“”「」]+")
_URI_START = re.compile(r"<[A-Za-z][A-Za-z0-9+.-]{1,31}:")
_MAIL_DOMAIN = r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?"
_AUTOLINK = re.compile(r"<(?:[A-Za-z][A-Za-z0-9+.-]{1,31}:[^\x00-\x20<>]*|"
                       r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@" + _MAIL_DOMAIN
                       + r"(?:\." + _MAIL_DOMAIN + r")*)>")


def _table_separator(line):
    stripped = line.strip()
    cells = stripped.strip("|").split("|")
    return ("|" in stripped or len(cells) > 1) and all(re.fullmatch(r":?-{3,}:?", cell.strip()) for cell in cells)


def _inline_code_end(text, start):
    end_run = start + 1
    while end_run < len(text) and text[end_run] == "`":
        end_run += 1
    marker = text[start:end_run]
    search = end_run
    while search < len(text):
        found = text.find(marker, search)
        if found < 0:
            break
        after = found + len(marker)
        if text[found - 1] != "`" and (after == len(text) or text[after] != "`"):
            return after
        search = after
    raise Unsupported("Unclosed inline code.")


def snapshot(text, protect_quotes=False, literals=(), strict_quotes=True):
    validate_text(text)
    spans = []
    occupied = bytearray(len(text))

    def add(start, end, category, overlap=False):
        if end > start and (overlap or not any(occupied[start:end])):
            spans.append(Span(start, end, category, text[start:end]))
            occupied[start:end] = b"\x01" * (end - start)
            return True
        return False

    # CommonMark lines end at LF/CRLF, not Unicode separators or form feeds.
    lines = re.findall(r"[^\n]*\n|[^\n]+$", text)
    offsets = []
    offset = 0
    for line in lines:
        offsets.append(offset)
        offset += len(line)
    start_line = 0
    bom_offset = 1 if text.startswith("\ufeff") else 0
    if bom_offset:
        add(0, 1, "bom")
    if lines and lines[0][bom_offset:].rstrip("\r\n") == "---":
        end = next((i for i in range(1, len(lines)) if lines[i].rstrip("\r\n") in ("---", "...")), None)
        if end is None:
            raise Unsupported("Unclosed frontmatter.")
        add(bom_offset, offsets[end] + len(lines[end]), "frontmatter")
        start_line = end + 1
    index = start_line
    while index < len(lines):
        line, start = lines[index], offsets[index]
        body = "".join(" " if occupied[start + i] else char for i, char in enumerate(line)).rstrip("\r\n")
        if not body.strip():
            index += 1
            continue
        if re.match(r" {0,3}>", body):
            end = index + 1
            while end < len(lines) and lines[end].strip():
                end += 1
            add(start, offsets[end] if end < len(lines) else len(text), "blockquotes")
            index = end
            continue
        if not occupied[start] and re.match(r"(?: {4}|\t)", body):
            raise Unsupported("Indented blocks are outside the supported Markdown subset.")
        if re.search(r"^\s*(?:[-+*]|\d+[.)])\s+(?:`{3,}|~{3,})", body):
            raise Unsupported("Fences inside list containers are unsupported.")
        if re.match(r" {0,3}\[\^", body):
            raise Unsupported("Markdown footnotes are unsupported.")
        # Comments beginning outside code must shield embedded Markdown before
        # the block pass can interpret it as a fence, table, or indented block.
        if not _FENCE.fullmatch(body):
            cursor, line_end = start, start + len(line)
            while cursor < line_end:
                if occupied[cursor]:
                    cursor += 1
                    continue
                if text[cursor] == "\\":
                    cursor += 2
                    continue
                if text[cursor] == "`":
                    closing = _inline_code_end(text, cursor)
                    if not add(cursor, closing, "inline_code"):
                        raise Unsupported("Overlapping inline code.")
                    cursor = closing
                    continue
                if text.startswith("<!--", cursor):
                    closing = text.find("-->", cursor + 4)
                    if closing < 0:
                        raise Unsupported("Unclosed HTML comment.")
                    add(cursor, closing + 3, "html", overlap=True)
                    cursor = closing + 3
                    continue
                cursor += 1
            body = "".join(" " if occupied[start + i] else char for i, char in enumerate(line)).rstrip("\r\n")
            if not body.strip():
                index += 1
                continue
        fence = _FENCE.fullmatch(body)
        if fence:
            marker = fence.group(1)
            if marker.startswith("`") and "`" in fence.group(2):
                raise Unsupported("Invalid backtick fence information string.")
            closer = re.compile(r" {0,3}" + re.escape(marker[0]) + "{" + str(len(marker)) + r",}[ \t]*$")
            end = next((i for i in range(index + 1, len(lines)) if closer.fullmatch(lines[i].rstrip("\r\n"))), None)
            if end is None:
                raise Unsupported("Unclosed fenced code block.")
            add(start, offsets[end] + len(lines[end]), "fences")
            index = end + 1
            continue
        if index + 1 < len(lines) and "|" in body and _table_separator(lines[index + 1]):
            end = index + 2
            while end < len(lines) and "|" in lines[end] and lines[end].strip():
                end += 1
            add(start, offsets[end] if end < len(lines) else len(text), "tables", overlap=True)
            index = end
            continue
        if re.match(r" {0,3}\[[^\]\r\n]+\]:", body):
            if not re.fullmatch(r" {0,3}\[[^\]\r\n]+\]:\s*(?:<[^<>\r\n]+>|[^\s]+)(?:\s+(?:\"[^\"\r\n]*\"|'[^'\r\n]*'|\([^()\r\n]*\)))?\s*", body):
                raise Unsupported("Unsupported link reference definition.")
            add(start, start + len(line), "link_targets", overlap=True)
        task = re.match(r" {0,3}(?:[-+*]|\d+[.)])[ \t]+(\[[ xX]\])(?=[ \t]|$)", body)
        if task:
            add(start + task.start(1), start + task.end(1), "task_markers")
        index += 1

    # Inline spans. Scan from left to right so code and comments shield syntax.
    escapes = bytearray(len(text))
    slash_count = 0
    for position, char in enumerate(text):
        escapes[position] = slash_count % 2
        slash_count = slash_count + 1 if char == "\\" else 0

    def escaped(position):
        return bool(escapes[position])

    def label_start(end):
        depth = 1
        for cursor in range(end - 1, -1, -1):
            if occupied[cursor] or escaped(cursor):
                continue
            if text[cursor] == "]":
                depth += 1
            elif text[cursor] == "[":
                depth -= 1
                if depth == 0:
                    return cursor
        raise Unsupported("Link target has no supported opening label.")

    def link_role(start):
        image = start > 0 and text[start - 1] == "!" and not escaped(start - 1)
        spans.append(Span(start, start + 1, "link_roles", "image" if image else "link"))

    index = 0
    while index < len(text):
        if occupied[index]:
            index += 1
            continue
        if text.startswith("[^", index):
            raise Unsupported("Markdown footnotes are unsupported.")
        if text[index] == "\\" and index + 1 < len(text):
            index += 2
            continue
        if text.startswith("<!--", index):
            end = text.find("-->", index + 4)
            if end < 0:
                raise Unsupported("Unclosed HTML comment.")
            add(index, end + 3, "html", overlap=True)
            index = end + 3
            continue
        if text[index] == "`":
            closing = _inline_code_end(text, index)
            if any(occupied[index:closing]):
                raise Unsupported("Unclosed or overlapping inline code.")
            add(index, closing, "inline_code")
            index = closing
            continue
        if text[index] == "<":
            autolink = _AUTOLINK.match(text, index)
            if autolink:
                add(index, autolink.end(), "urls")
                index = autolink.end()
                continue
            if _URI_START.match(text, index):
                raise Unsupported("Malformed or unclosed URI autolink.")
            if _RAW_HTML.match(text, index):
                raise Unsupported("Raw HTML blocks are unsupported.")
            tag = _HTML_START.match(text, index)
            if tag:
                cursor, quote = tag.end(), None
                while cursor < len(text):
                    char = text[cursor]
                    if char in "\r\n<":
                        raise Unsupported("Multiline or nested HTML-like tags are unsupported.")
                    if quote:
                        if char == quote:
                            quote = None
                    elif char in "\"'":
                        quote = char
                    elif char == ">":
                        break
                    cursor += 1
                if cursor == len(text) or quote:
                    raise Unsupported("Incomplete HTML-like tag.")
                add(index, cursor + 1, "html")
                index = cursor + 1
                continue
            if _HTML_LIKE.match(text, index):
                raise Unsupported("Unsupported or incomplete HTML-like markup.")
        if text.startswith("](", index):
            opening = label_start(index)
            start = index + 2
            cursor, depth, quote = start, 1, None
            while cursor < len(text):
                char = text[cursor]
                if char in "\r\n":
                    raise Unsupported("Multiline inline links are unsupported.")
                if char == "\\":
                    cursor += 2
                    continue
                if quote:
                    if char == quote:
                        quote = None
                elif char in "\"'" and cursor > start and text[cursor - 1].isspace():
                    quote = char
                elif char == "(":
                    depth += 1
                    if depth > 32:
                        raise Unsupported("Link nesting exceeds the supported limit.")
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        break
                cursor += 1
            if depth or quote:
                raise Unsupported("Unclosed inline link.")
            if not add(index, cursor + 1, "link_targets"):
                raise Unsupported("Overlapping link markup.")
            link_role(opening)
            index = cursor + 1
            continue
        if text.startswith("][", index):
            opening = label_start(index)
            end = text.find("]", index + 2)
            if end < 0 or "\n" in text[index:end]:
                raise Unsupported("Unclosed link reference.")
            # Include the whole link label for collapsed references.
            start = opening if end == index + 2 else index
            if start < 0:
                raise Unsupported("Unsupported reference syntax.")
            add(start, end + 1, "link_targets", overlap=True)
            link_role(opening)
            index = end + 1
            continue
        index += 1

    # Shortcut reference labels resolve through definitions already preserved.
    def normalize_label(label):
        return " ".join(label.split()).casefold()

    labels = {normalize_label(re.match(r"\s*\[([^\]]+)\]", span.value).group(1))
              for span in spans if span.category == "link_targets" and re.match(r"\s*\[[^\]]+\]:", span.value)}
    cursor = 0
    while labels and cursor < len(text):
        start = text.find("[", cursor)
        if start < 0:
            break
        end = text.find("]", start + 1)
        if end < 0:
            break
        label = text[start + 1:end]
        slash = start
        while slash > 0 and text[slash - 1] == "\\":
            slash -= 1
        is_escaped = (start - slash) % 2 == 1
        explicit = text[end + 1:end + 2] in {"(", "["}
        if normalize_label(label) in labels and not occupied[start] and not is_escaped and not explicit:
            if "\n" in label or "\r" in label:
                raise Unsupported("Multiline shortcut references are unsupported.")
            add(start, end + 1, "link_targets", overlap=True)
            link_role(start)
        cursor = end + 1
    for pattern, category in (
        (re.compile(r"\{#[A-Za-z_][\w:.-]*\}"), "explicit_ids"),
        (_URL, "urls"),
        (_PLACEHOLDER, "placeholders"),
    ):
        for match in pattern.finditer(text):
            end = match.end()
            if category == "urls":
                while end > match.start() and text[end - 1] in ".,;!?，。！？；":
                    end -= 1
            add(match.start(), end, category)
    if protect_quotes:
        visible = "".join("\n" if char == "\n" else " " if occupied[i] else char for i, char in enumerate(text))
        pairs = {'"': '"', "“": "”", "「": "」", "『": "』", "《": "》"}
        unmatched = set()
        cursor = 0
        while cursor < len(visible):
            char = visible[cursor]
            if char == "\\":
                cursor += 2
                continue
            if char in pairs and char not in unmatched:
                end = cursor + 1
                while end < len(visible) and visible[end] != pairs[char]:
                    end += 2 if visible[end] == "\\" else 1
                if end >= len(visible) or visible[end] != pairs[char]:
                    if strict_quotes:
                        raise Unsupported("Unclosed quoted span under quote protection.")
                    unmatched.add(char)
                    cursor += 1
                    continue
                add(cursor, end + 1, "quotes", overlap=True)
                cursor = end + 1
                continue
            cursor += 1
    # Explicit literals are independent checks, including inside protected spans.
    for literal in literals:
        if not literal:
            raise InputError("Protected literals must not be empty.")
        cursor = 0
        while True:
            found = text.find(literal, cursor)
            if found < 0:
                break
            spans.append(Span(found, found + len(literal), "literals", literal))
            occupied[found:found + len(literal)] = b"\x01" * len(literal)
            cursor = found + len(literal)
    masked = "".join("\n" if char == "\n" else " " if occupied[i] else char for i, char in enumerate(text))
    return Snapshot(text, spans, masked)


def _quantity_terms(values):
    # Longer spellings precede their prefixes; an English word may use tabs/spaces.
    return "(?:" + "|".join(re.escape(value).replace(r"\ ", r"[ \t]+")
                            for value in sorted(set(values), key=lambda s: (-len(s), s))) + ")"


_QUANTITY_CURRENCIES = (
    "USD", "EUR", "GBP", "CNY", "RMB", "JPY", "HKD", "SGD", "AUD", "CAD", "CHF", "INR", "KRW",
    "人民币", "美元", "欧元", "英镑", "日元", "港元", "港币", "新加坡元", "澳元", "加元", "瑞士法郎", "卢比", "韩元",
    "$", "€", "£", "¥", "￥", "₹", "₩",
)
_QUANTITY_SCALES = ("万亿", "亿", "万", "千", "百", "trillion", "billion", "million", "thousand")
_QUANTITY_UNITS = (
    "%", "％", "个百分点", "百分点", "个基点", "基点", "percentage points", "percentage point",
    "basis points", "basis point", "percent", "bp", "bps", "pp", "元",
    "TiB/s", "GiB/s", "MiB/s", "KiB/s", "TB/s", "GB/s", "MB/s", "KB/s", "B/s",
    "TiB", "GiB", "MiB", "KiB", "TB", "GB", "MB", "KB", "B", "Tb", "Gb", "Mb", "Kb",
    "Tbps", "Gbps", "Mbps", "Kbps", "kbps", "bit/s", "bits/s", "bytes", "byte", "bits", "bit",
    "纳秒", "微秒", "毫秒", "秒", "分钟", "小时", "天", "年",
    "nanoseconds", "nanosecond", "microseconds", "microsecond", "milliseconds", "millisecond",
    "seconds", "second", "minutes", "minute", "hours", "hour", "days", "day", "years", "year",
    "ns", "μs", "µs", "us", "ms", "min", "s", "h", "kg", "km", "cm", "g", "m",
)
_Q_SPACE = r"[ \t]*"
_Q_SIGN = r"[-+−]"
_Q_CURRENCY = _quantity_terms(_QUANTITY_CURRENCIES)
_MONEY_MARK = re.compile(_quantity_terms((*_QUANTITY_CURRENCIES, "元")))
_Q_UNIT = _quantity_terms((*_QUANTITY_CURRENCIES, *_QUANTITY_UNITS))
_Q_SCALE = "(?i:" + _quantity_terms(_QUANTITY_SCALES) + ")"
_Q_COEFFICIENT = r"(?:(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|(?<!\.)\.\d+)"
_MONTH = r"(?:0?[1-9]|1[0-2])"
_DAY = r"(?:0?[1-9]|[12]\d|3[01])"
_DATE = rf"\d{{4}}(?:-{_MONTH}-{_DAY}|/{_MONTH}/{_DAY}|年{_MONTH}月{_DAY}日)"
_TIME = r"(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d(?:\.\d+)?)?"
_ZONE = r"(?:Z|[+-](?:[01]\d|2[0-3]):?[0-5]\d)"
_DATETIME = rf"(?:{_DATE}(?:[T ]{_TIME}{_ZONE}?)?|{_TIME}{_ZONE}?)"
_QUANTITY = re.compile(
    r"(?<![A-Za-z_\d])"
    + rf"(?:{_DATETIME}|"
    # Signs adjoin their currency or numeral; a Markdown '- ' is not a sign.
    + rf"(?:{_Q_SIGN}(?:{_Q_CURRENCY}{_Q_SPACE})?|{_Q_CURRENCY}{_Q_SPACE}{_Q_SIGN}?)?"
    + _Q_COEFFICIENT + r"(?:[eE][-+−]?\d+)?"
    + rf"(?:{_Q_SPACE}(?:{_Q_SCALE}(?:{_Q_SPACE}{_Q_UNIT})?|{_Q_UNIT}))?"
    + r")(?![A-Za-z_\d])"
)


def numbers(scan):
    """Literal quantities in visible prose; no conversion or semantic inference."""
    # A masked code/quote span must not join distant currency and amount tokens.
    visible = "".join("\x00" if original != masked else masked
                      for original, masked in zip(scan.text, scan.masked))
    values = []
    for match in _QUANTITY.finditer(visible):
        value_start, value_end = match.span()
        value = match.group(0)
        if _MONEY_MARK.search(value):
            start, end = match.span()
            while start > 0 and visible[start - 1] in " \t":
                start -= 1
            while end < len(visible) and visible[end] in " \t":
                end += 1
            if {"(": ")", "（": "）"}.get(visible[start - 1:start]) == visible[end:end + 1]:
                value_start, value_end = start - 1, end + 1
        prefix = value_start
        while prefix > 0 and visible[prefix - 1] in " \t":
            prefix -= 1
        operator = visible[max(0, prefix - 2):prefix]
        if operator not in {"<=", ">=", "==", "!="}:
            operator = visible[max(0, prefix - 1):prefix]
        if operator in {"<=", ">=", "==", "!=", "<", ">", "=", "≤", "≥", "≠", "≈", "~"}:
            operator_start = prefix - len(operator)
            if operator_start == 0 or visible[operator_start - 1] not in "<>=!≤≥≠≈~":
                value_start = operator_start
        if values:
            prior_start, prior_end = values[-1]
            gap = visible[prior_end:value_start]
            # Join explicit dash/ellipsis pairs without interpreting their units.
            # In 5-10, the quantity scanner owns the minus sign in the second atom.
            joined = re.fullmatch(r"[ \t]*(?:[-–—…]|\.\.)[ \t]*", gap)
            adjacent_minus = (re.fullmatch(r"[ \t]*", gap)
                              and visible[value_start:value_start + 1] == "-")
            if joined or adjacent_minus:
                values[-1] = (prior_start, value_end)
                continue
        values.append((value_start, value_end))
    return [visible[start:end] for start, end in values]

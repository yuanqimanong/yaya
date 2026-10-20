"""Read-only product audit; generated fixtures and evidence stay in this directory."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
AUDIT = ROOT / "tests" / "runs" / "0.2-tools-audit"
SCRIPTS = ROOT / "core" / "yaya" / "scripts"
assert Path(__file__).resolve().parent == AUDIT.resolve()


def save(name, text):
    path = (AUDIT / name).resolve()
    path.relative_to(AUDIT.resolve())
    path.write_text(text, encoding="utf-8", newline="\n")
    return path


def run_case(name, before, after=None, flags=()):
    first = save(name + ".before.md", before)
    if after is None:
        argv = [sys.executable, "-B", str(SCRIPTS / "detect_tells.py"),
                str(first), "--language", "en", *flags]
    else:
        second = save(name + ".after.md", after)
        argv = [sys.executable, "-B", str(SCRIPTS / "check_rewrite.py"),
                str(first), str(second), *flags]
    start = time.perf_counter()
    result = subprocess.run(argv, capture_output=True, timeout=30)
    elapsed = time.perf_counter() - start
    try:
        payload = json.loads(result.stdout)
    except (ValueError, UnicodeError):
        payload = {"unparsed_stdout": result.stdout.decode("utf-8", errors="replace")}
    return {
        "case": name, "argv": argv, "bytes": len(before.encode("utf-8")),
        "exit": result.returncode, "elapsed_seconds": round(elapsed, 4),
        "payload": payload,
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    }


cases = [
    ("html_comment_fence",
     "<!-- Keep this source note.\n```text\nexact code\n```\n-->\n",
     "<!-- Changed source note.\n```text\nexact code\n```\n-->\n"),
    ("html_comment_table",
     "<!-- Keep this source note.\n| A | B |\n| --- | --- |\n| x | y |\n-->\n",
     "<!-- Changed source note.\n| A | B |\n| --- | --- |\n| x | y |\n-->\n"),
    ("html_comment_detection",
     "<!-- note\n| A | B |\n| --- | --- |\n| x | y |\nOnly time will tell.\n-->\n"),
    ("collapsed_reference_code",
     "[A `x`][]\n\n[A `x`]: url\n",
     "[B `x`][]\n\n[A `x`]: url\n"),
    ("shortcut_reference_code",
     "[A `x`]\n\n[A `x`]: url\n",
     "[B `x`]\n\n[A `x`]: url\n"),
    ("single_column_table",
     "| Name |\n| --- |\n| Alice |\n",
     "| Name |\n| --- |\n| Bob |\n"),
    ("apostrophe_url",
     "[O'Brien](https://en.wikipedia.org/wiki/Tim_O'Brien)\n",
     "[O'Brien](https://en.wikipedia.org/wiki/Tim_O'Brien)\n"),
    ("hard_wrapped_quote",
     "She wrote: “The analysis is complete,\nand the result is ready.”\n\nOnly time will tell.\n"),
    ("inch_mark",
     'The display is 6" wide. Only time will tell.\n'),
]
results = [run_case(*case) for case in cases]

# Lexical boundaries: recognized units, unrecognized suffixes, and whole words.
sys.path.insert(0, str(SCRIPTS))
from prose_scan import numbers, snapshot

numeric_cases = [
    "Wait 2 seconds.", "Wait 2 secondhand customers.",
    "Wait 2ms.", "Wait 2MS.", "Memory 256MiB.",
    "Pay 30万元。", "Cost 2 más.", "Wait 2 minutes.",
]
numbers_report = {value: numbers(snapshot(value)) for value in numeric_cases}

# Every input is below the advertised 2 MiB bound; the process has a timeout.
performance = []
for name, text in [
    ("perf_plain", ("ordinary prose without markup.\n" * 60_000)),
    ("perf_inline_code", ("ordinary `code` prose.\n" * 85_000)),
    ("perf_digits", "8" * 2_000_000 + "x"),
    ("perf_reference_spaces", "[id]: x " + " " * 1_999_990 + " invalid"),
]:
    assert len(text.encode("utf-8")) <= 2 * 1024 * 1024
    performance.append(run_case(name, text, text))
performance.append(run_case("perf_unmatched_quotes", "“" * 12_000))

cli_errors = []
for script, argv, data in [
    ("detect_tells.py", ["-", "--language", "en"], b"\xff"),
    ("detect_tells.py", ["-", "--language", "en"], b"a\x00b"),
    ("detect_tells.py", ["-", "--language", "en"], b"first\rnext"),
    ("detect_tells.py", ["-", "--language", "en"], b"x" * (2 * 1024 * 1024 + 1)),
    ("detect_tells.py", ["-", "--language", "en", "--fail-on", "all"], b"text"),
    ("check_rewrite.py", ["-", "-"], b"text"),
    ("check_rewrite.py", [], b""),
    ("check_rewrite.py", ["absent-before-input.md", "absent-after-input.md"], b""),
]:
    result = subprocess.run(
        [sys.executable, "-B", str(SCRIPTS / script), *argv],
        input=data, capture_output=True, timeout=10,
    )
    cli_errors.append({
        "script": script, "argv": argv, "input_bytes": len(data),
        "exit": result.returncode, "payload": json.loads(result.stdout),
        "stderr": result.stderr.decode("utf-8", errors="replace"),
    })

evidence = {
    "script_sha256": {
        name: hashlib.sha256((SCRIPTS / name).read_bytes()).hexdigest()
        for name in ("prose_scan.py", "check_rewrite.py", "detect_tells.py", "tell_rules.json")
    },
    "cases": results,
    "numbers": numbers_report,
    "performance": performance,
    "cli_errors": cli_errors,
}
save("prose-audit-evidence.json", json.dumps(evidence, ensure_ascii=False, indent=2) + "\n")
for result in results + performance:
    payload = result["payload"]
    print(json.dumps({
        "case": result["case"], "exit": result["exit"], "bytes": result["bytes"],
        "status": payload.get("status"), "error": payload.get("error"),
        "changes": payload.get("changes"),
        "findings": len(payload.get("findings", [])),
        "seconds": result["elapsed_seconds"],
    }, ensure_ascii=True))
print(json.dumps({"numbers": numbers_report}, ensure_ascii=True))
print(json.dumps({"cli_errors": [
    {"script": result["script"], "argv": result["argv"],
     "exit": result["exit"], "status": result["payload"].get("status")}
    for result in cli_errors
]}, ensure_ascii=True))

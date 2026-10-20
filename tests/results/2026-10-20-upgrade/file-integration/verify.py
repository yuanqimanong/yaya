"""Recheck retained integration evidence with only Python's standard library."""
import ast
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tokenize

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parents[3]
assert ROOT == (REPO / "tests/results/2026-10-20-upgrade/file-integration").resolve()
checks = {}
manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
for item in manifest["files"]:
    target = (ROOT / item["path"]).resolve()
    target.relative_to(ROOT)
    checks["sha256:" + item["path"]] = hashlib.sha256(target.read_bytes()).hexdigest() == item["sha256"]

before, after = ROOT / "before", ROOT / "after"
for name, heading, end in [
    ("report.md", "## 收入说明", "## 接口说明"),
    ("scoped-overview.md", "## Overview", "## API"),
]:
    old, new = (before / name).read_bytes(), (after / name).read_bytes()
    start, tail = heading.encode(), end.encode()
    checks[name + ":prefix_equal"] = old[:old.index(start)] == new[:new.index(start)]
    checks[name + ":suffix_equal"] = old[old.index(tail):] == new[new.index(tail):]
    checks[name + ":headings_equal"] = [x for x in old.splitlines(keepends=True) if x.startswith(b"#")] == [x for x in new.splitlines(keepends=True) if x.startswith(b"#")]

old, new = (before / "metrics.py").read_bytes(), (after / "metrics.py").read_bytes()
checks["python:ast_equal"] = ast.dump(ast.parse(old), include_attributes=False) == ast.dump(ast.parse(new), include_attributes=False)
old_tokens = list(tokenize.tokenize(io.BytesIO(old).readline))
new_tokens = list(tokenize.tokenize(io.BytesIO(new).readline))
checks["python:noncomment_tokens_equal"] = [(t.type, t.string) for t in old_tokens if t.type != tokenize.COMMENT] == [(t.type, t.string) for t in new_tokens if t.type != tokenize.COMMENT]
checks["python:docstring_equal"] = ast.get_docstring(ast.parse(old).body[0]) == ast.get_docstring(ast.parse(new).body[0])
for label, marker in [("noqa_line", b"# noqa:"), ("string_line", b"LABEL =")]:
    checks["python:" + label + "_equal"] = next(line for line in old.splitlines(keepends=True) if marker in line) == next(line for line in new.splitlines(keepends=True) if marker in line)
checks["existing_style:bytes_equal"] = (before / "styles/existing.md").read_bytes() == (after / "styles/existing.md").read_bytes()
checks["new_style:separate_path"] = not (before / "styles/plain.md").exists() and (after / "styles/plain.md").is_file()

results = []
for name, checker in [
    ("report.md", "check_rewrite.py"),
    ("metrics.py", "check_comments.py"),
    ("scoped-overview.md", "check_rewrite.py"),
]:
    argv = [sys.executable, "-B", str(REPO / "core/yaya/scripts" / checker),
            str(before / name), str(after / name)]
    proc = subprocess.run(argv, cwd=REPO, capture_output=True, check=False)
    payload = json.loads(proc.stdout)
    results.append({"file": name, "argv": argv, "exit": proc.returncode,
                    "payload": payload, "stderr": proc.stderr.decode("utf-8")})
status = "passed" if all(checks.values()) and all(row["exit"] == 0 and row["payload"]["status"] == "passed" for row in results) else "failed"
evidence = {"status": status, "checks": checks, "tool_results": results,
            "runtime_hashes": {
                name: hashlib.sha256((REPO / "core/yaya/scripts" / name).read_bytes()).hexdigest()
                for name in ("check_comments.py", "check_rewrite.py", "prose_scan.py")
            }}
(ROOT / "retained-verification.json").write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"status": status, "checks": len(checks),
                  "failed_checks": [name for name, ok in checks.items() if not ok],
                  "tools": [{"file": row["file"], "status": row["payload"]["status"], "exit": row["exit"]} for row in results]}, ensure_ascii=True, indent=2))
raise SystemExit(0 if status == "passed" else 1)

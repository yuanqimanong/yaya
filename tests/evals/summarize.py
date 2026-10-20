"""Validate anonymous judgments and summarize them without changing raw evidence."""
from __future__ import annotations
import argparse
from collections import Counter
from pathlib import Path
import json
from collect import read_json


def summarize(result: Path) -> dict:
    cases = read_json(result / "cases.json")
    key = read_json(result / "blind-key.json")
    judgments = read_json(result / "judgments.json")
    if (not isinstance(cases, list) or not cases
            or any(not isinstance(case, dict) or not isinstance(case.get("id"), str) for case in cases)
            or len({case["id"] for case in cases}) != len(cases)):
        raise ValueError("Cases must have unique IDs")
    expected = {case["id"] for case in cases}
    if (not isinstance(key, dict) or set(key) != expected
            or any(not isinstance(value, dict) or set(value) != {"A", "B"}
                   or sorted(value.values()) != ["baseline", "skill"] for value in key.values())):
        raise ValueError("Blind key must map A/B to skill/baseline exactly once for every case")
    if not isinstance(judgments, list) or len(judgments) != len(expected):
        raise ValueError("One judgment per case is required")
    seen = set()
    totals = {mode: Counter() for mode in ("skill", "baseline")}
    preferences = Counter()
    case_by_id = {case["id"]: case for case in cases}
    groups = {}
    details = []
    mechanical = {}
    rows = read_json(result / "mechanical.json")
    if not isinstance(rows, list):
        raise ValueError("Mechanical checks must be an array")
    for check in rows:
        if (not isinstance(check, dict) or check.get("id") not in expected
                or check.get("condition") not in {"skill", "baseline"}
                or not isinstance(check.get("literal_failures"), list)
                or any(not isinstance(item, str) for item in check["literal_failures"])):
            raise ValueError("Malformed mechanical check")
        identity = (check["id"], check["condition"])
        if identity in mechanical:
            raise ValueError("Duplicate mechanical check")
        if ("comment_boundary" in check
                and (not isinstance(check["comment_boundary"], dict)
                     or check["comment_boundary"].get("status") not in {"passed", "failed", "unsupported", "error"})):
            raise ValueError("Unknown comment boundary status")
        mechanical[identity] = check
    if set(mechanical) != {(identifier, mode) for identifier in expected for mode in ("skill", "baseline")}:
        raise ValueError("A mechanical check is required for every case and condition")
    for row in judgments:
        identifier = row["id"]
        if identifier in seen or identifier not in expected:
            raise ValueError(f"Duplicate or unknown judgment: {identifier}")
        seen.add(identifier)
        group = case_by_id[identifier].get("group", "ungrouped")
        if not isinstance(group, str):
            raise ValueError(f"Invalid case group: {identifier}")
        group_totals = groups.setdefault(group, {"cases": 0, "conditions": {
            mode: Counter() for mode in ("skill", "baseline")}, "preferences": Counter()})
        group_totals["cases"] += 1
        if row["preference"] not in {"A", "B", "tie", "uncertain"} or not row["reason"].strip():
            raise ValueError(f"Invalid preference: {identifier}")
        statuses = {}
        for alias in ("A", "B"):
            value = row[alias]
            if any(value[field] not in {"pass", "fail", "uncertain"} for field in ("fidelity", "task")):
                raise ValueError(f"Invalid hard judgment: {identifier}")
            if value["quality"] not in {"better", "same", "worse", "uncertain", "not_applicable"} or not value["evidence"].strip():
                raise ValueError(f"Missing evidence or invalid quality: {identifier}")
            mode = key[identifier][alias]
            checks = mechanical[identifier, mode]
            failed = (bool(checks["literal_failures"]) or checks.get("comment_boundary", {}).get("status") == "failed"
                      or "fail" in (value["fidelity"], value["task"]))
            uncertain = ("uncertain" in (value["fidelity"], value["task"])
                         or checks.get("comment_boundary", {}).get("status") == "error")
            status = "fail" if failed else ("uncertain" if uncertain else "pass")
            statuses[alias] = status
            totals[mode]["hard_" + status] += 1
            totals[mode]["quality_" + value["quality"]] += 1
            group_totals["conditions"][mode]["hard_" + status] += 1
            group_totals["conditions"][mode]["quality_" + value["quality"]] += 1
            details.append({"id": identifier, "condition": mode, "hard_status": status,
                            "quality": value["quality"], "evidence": value["evidence"]})
        choice = row["preference"]
        if choice in {"A", "B"}:
            other = "B" if choice == "A" else "A"
            if statuses[choice] != "pass" and statuses[other] == "pass":
                raise ValueError(f"Preference overrides a hard issue: {identifier}")
            choice = key[identifier][choice]
        preferences[choice] += 1
        group_totals["preferences"][choice] += 1
    manifest = read_json(result / "manifest.json") if (result / "manifest.json").is_file() else {}
    return {"cases": len(expected), "conditions": {mode: dict(counts) for mode, counts in totals.items()},
            "preferences": {name: preferences[name] for name in ("skill", "baseline", "tie", "uncertain")},
            "groups": groups,
            "execution": read_json(result / "execution-audit.json") if (result / "execution-audit.json").is_file()
                         else {"status": "not_recorded"},
            "limitations": ["Model judgments, without native human calibration.",
                            "Generation isolation: " + manifest.get("isolation", "not recorded") + ".",
                            "A single run does not establish cross-model or repeated-run reliability.",
                            "Quality judgments are relative to the input; textual changes alone do not establish unnecessary editing.",
                            "A semantic pass does not establish tool use, persistence behavior, or unsupported-language parser validation."],
            "details": details}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("result", type=Path)
    args = parser.parse_args()
    summary = summarize(args.result)
    (args.result / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in summary.items() if key != "details"}))

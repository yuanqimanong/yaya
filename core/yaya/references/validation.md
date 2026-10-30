# Validation and batch evidence

Use checks proportionally. A normal rewrite needs a faithful result, not a diagnostic report. Batch file tasks need recoverable originals and evidence tied to the actual delivered candidate.

## Task-start boundary

Before editing, snapshot the selected current working-tree files, including existing uncommitted changes. Record Git HEAD/status and staged/unstaged diffs separately; HEAD is not the editing before-copy. Never reset, checkout, or overwrite unrelated work. The bundled helper snapshots planned existing files and performs no Git writes:

```text
python scripts/edit_evidence.py start PROJECT SNAPSHOT --target src/item.py:comments --target docs/run.md:prose --target docs/run.md:manual
python scripts/edit_evidence.py check SNAPSHOT --target src/item.py:comments
python scripts/edit_evidence.py check SNAPSHOT --target docs/run.md:prose
python scripts/edit_evidence.py check SNAPSHOT --target docs/run.md:manual --disposition accepted --note "Reviewed changed claims against config.py:42 and sample response api-01."
python scripts/edit_evidence.py summary SNAPSHOT
```

Paths use forward slashes relative to PROJECT. Choose a new snapshot directory outside the selected files. Include every intended check as a target; additions/deletions and mixed-mode editing chains need a separate explicit manifest/review. This helper does not discover arbitrary dependencies or replace project tests. It supports non-Git directories and records unavailable Git metadata as null.

Checks bind raw before/candidate SHA-256, format details, tool/dependency hashes, tool version, Python version, command/options, and UTC times. Reports are append-only. Summary rechecks the snapshot, current candidate, and tools. Content or tool changes make a previous report **unverified**, even when its old status was passed. Save actual external check commands/versions/results similarly. A JSON record is local audit evidence, not a signed provenance assertion.

Count **passed**, **failed**, **unsupported**, **manual_review**, and **unverified** separately. Manual acceptance is never a mechanical pass; unsupported needs an actual substitute or remains unsupported. Unexecuted checks remain unverified. A failed check stays open until a fresh pass on the repaired candidate or an explicit content-bound exclusion with evidence/reason (`--disposition excluded --note ...`). Accepted or unresolved manual notes do not close it. Preserve all earlier failures. `complete` is deliberately conservative: only all-mechanical-pass tasks return true; manual/excluded tasks require reading their dispositions.

## Exact grants

`--allow FILE` is a reviewed permission record, not a way to silence a failing category. Retain the user's authorization basis with the task. Do not auto-approve differences from the candidate merely because a checker detected them. Broad legacy forms such as `--allow numbers` are rejected in 0.2.1.

For prose, the JSON binds the raw UTF-8 file hashes and complete exact protected-category changes:

```json
{
  "schema": 1,
  "before_sha256": "SHA256_OF_BEFORE_FILE",
  "after_sha256": "SHA256_OF_CANDIDATE_FILE",
  "changes": [{"category": "numbers", "before": ["2"], "after": ["3"]}]
}
```

Another number, another candidate, unused entries, unknown fields, or duplicate categories cannot reuse this grant. Read detected category values verbatim from the failed report and authorize only the user's intended concrete change; reviewing relationships still requires semantics.

For Python docstrings, inspect `python scripts/check_docstrings.py --inventory BEFORE.py`. Selectors include the owner and its original definition line, such as `C.method@12` or `<module>@1`. The grant binds whole files and literal-token hashes:

```json
{
  "schema": 1,
  "before_sha256": "SHA256_OF_BEFORE_FILE",
  "after_sha256": "SHA256_OF_CANDIDATE_FILE",
  "docstrings": [{"node": "C.method@12", "before_sha256": "SHA256_OF_OLD_LITERAL", "after_sha256": "SHA256_OF_NEW_LITERAL"}]
}
```

No wildcard, new/deleted/moved node, encoding/BOM change, delimiter change, or line-count/ending change is allowed. Single-token UTF-8 docstrings are supported; implicit concatenation and other languages return unsupported. Recognized doctests and example/code sections remain protected even inside an authorized docstring. Unmarked examples require manual review. Example changes, docstring reflow, and runtime/schema strings need separately authorized, appropriate checks; this mode intentionally does not relax its boundary for them.

## Quantities in prose

Symbolic comparisons immediately before a quantity (`<`, `<=`, `>`, `>=`, `=`,
`==`, `!=`, `≤`, `≥`, `≠`, `≈`, `~`) are part of its literal token. Changing a
strict threshold to an inclusive one or removing approximation requires review.
This does not interpret verbal bounds such as "at most" or verify the surrounding
condition; equivalent rewrites between symbols and words also need review.

Parentheses immediately enclosing a recognized currency amount are retained as
part of its literal token: `(USD 5 million)` must not silently become `USD 5 million`.
They may express an accounting negative. Ordinary parenthetical prose remains
editable. Bare accounting values such as `(5)` without a currency still need
explicit literal protection or semantic review.

Numeric dates (`YYYY-MM-DD`, `YYYY/MM/DD`, `YYYY年M月D日`) and clock times
(`H:MM`, optional seconds/fraction and ISO offset) are compared as complete literal
tokens, including a date/time joined by `T` or one space. This catches component
swaps. It does not validate calendar dates or infer timezone equivalence; localized
month names, ambiguous day-first dates and date-to-event associations need review.

`check_rewrite.py` compares the spelling and occurrence count of recognized quantities
outside protected spans. It recognizes decimal and scientific numerals (such as
`1e-3`), selected currency prefixes/suffixes, scales such as `million` and `万`,
percentages/percentage points/basis points, and common time, storage and rate units.
The finite inventory is in `scripts/prose_scan.py`; it is not an arbitrary unit parser.

Changes such as `USD 5 million` to `EUR 5 billion`, `1e-3` to `1e+3`, or `8 MiB`
to `8 GiB` fail the number check. Surrounding wording may change. Whole sentences
may move when the quantities remain the same. Raw spelling is conservative: even
equivalent conversions and spacing changes within a quantity need review and,
when authorized, a content-bound exact grant. The tool does not convert currencies,
recalculate values, or infer that two spellings mean the same thing.

Keep checking which entity, period and condition each value belongs to. Swapping
unchanged quantities between entities can pass. Written-out numbers, unlisted units,
decimal-comma notation and digit grouping with spaces are not reliably covered;
currency/unit labels on another line or in a heading are not linked to a value.
Use `--protect-literal` for exact source spans that need explicit protection, and
semantic review for their relationships. Code, tables and blockquotes keep their
existing whole-span checks; quantities are not assembled across those spans.

## What a pass cannot establish

Images and hyperlinks retain their roles as well as destinations, including
supported reference forms. Inline image alt text and ordinary link labels remain
editable. Reordering roles and destinations across a document still needs review;
these category sequences are not a rendered document tree.

Markdown task markers (`- [ ]`, `- [x]`, `1. [X]`) are protected separately from
their editable descriptions. Changing, adding or removing a marker changes the
completion-state check. This does not verify the work described or associate a
marker with its task if unchanged markers and descriptions are rearranged.

AST and byte comparisons establish mechanical scope only. They cannot prove meaning, accuracy, absence of a latent code defect, or unchanged runtime behavior: `__doc__`, line tracing, reflection, doctests, and integrations can matter. Prose checks allow plain-prose newline changes and cannot associate numbers with entities; Python checks preserve line endings. JSON is ASCII-escaped for Windows consoles; source bytes retain UTF-8/BOM/CRLF details.

Test mechanics with scripts. Evaluate model decisions separately using predeclared expected outcomes, frozen old/new guidance, identical inputs/context, and the same target-model settings. Keep execution failures and missing outputs visible; report repeated-run/cross-model limits. No vocabulary hit rate proves naturalness, factual fidelity, or authorship accuracy.

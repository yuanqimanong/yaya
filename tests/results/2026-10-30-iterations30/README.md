# Thirty additional iterations after Yaya 0.4.0

Each numbered change is submitted as its own PR on the preceding branch. These
records describe actual checks, not model-quality certification. Domain and
language profiles retain their experimental status.

## 1 / cumulative 21 — Explicit literal iterables

Reproduced: changing `retry_limit` to `retry_count` failed with a list of protected
literals but passed with a generator. File evidence also consumed generators
before comparison. Normalize once to an immutable collection and reject a bare
string or invalid element. Duplicate selectors now have one protection meaning.
Regression checks cover changed/unchanged text, API/file parity and evidence
options. This protects spelling and occurrence counts; it does not verify meaning.

## 2 / cumulative 22 — Preserve authorization intent

Inspection and regression probes showed empty malformed grants were silently
treated as absent, and a manual disposition could discard a supplied checker
grant. Reject these combinations and notes without dispositions before writing
records. Normal omitted grants and explicit manual reviews remain supported.
This validates option intent; it does not turn manual review into a checker pass.

## 3 / cumulative 23 — Markdown physical lines

A Unicode line separator manufactured a blockquote in ordinary prose and a
closing fence inside a physical code line. The latter allowed edits after that
fake closer to pass. Split only at LF/CRLF, and limit fence trailing whitespace
to spaces/tabs. Regressions cover eight nonphysical separators, real code changes
and both supported newline encodings. The scanner remains a Markdown subset.

## 4 / cumulative 24 — Explicit term and quotation protection

The specialized prose helper supported term/quote preservation, but the bounded
`check` command could not select it. Add repeatable `--literal` and `--quotes`,
document their prose-only scope, and return an executable argument array in the
plan. An integration test runs that plan against changed terms/quotes and checks
the violations and unchanged source. Incompatible comment-mode options fail.
Expanded execution checks found the comment helper accepts two positional values
without an argparse `--` separator. Corrected its plan in the same PR and added
actual passed/failed comment executions, rather than relying on plan shape alone.

## 5 / cumulative 25 — Complete evaluation packets

A synthetic run with a valid result plus an unexpected empty `outputs.json` was
accepted. Collection also accepted outputs without their request packet. Require
an exact request/output file-set match and unique, nonempty request packets.
Regression tests cover both valid publication and each rejected case. These are
evidence-integrity tests, not model-quality measurements.

## 6 / cumulative 26 — Five-domain relationship evaluation

Add 15 predeclared relationship-preservation cases and execute both Skill and
baseline in fresh contexts. Complete inputs/outputs, runtime and assessments are
in [domain-relationships](domain-relationships/README.md). Both conditions met
the assessed semantic criteria; this supports regression coverage, not a claim
of improvement over the baseline. A duplicated percentage shows why literal
checker failures must remain separate from editorial judgments.

## 7 / cumulative 27 — Task completion markers

Changing `- [ ] Ship release` to `- [x] Ship release` previously passed. Protect
task markers while leaving descriptions editable. Checks cover unordered/ordered
lists, completion changes in both directions, ordinary bracketed text and code
boundaries. The checker cannot establish whether a task was actually completed
or bind a marker to its description after arbitrary rearrangement.

## 8 / cumulative 28 — Images remain images

`![diagram](flow.svg)` could become `[diagram](flow.svg)` without a violation.
Track image/link roles for inline and reference forms while allowing descriptive
label edits. Regressions include escaped exclamation marks, nested labels and
code inside labels. Cross-category rearrangement still needs semantic review.

## 9 / cumulative 29 — Formatted placeholders

`%1$s` could change to `%1$d` unnoticed. Recognize positional/mapping fields,
width, precision and `%%`, preserving their spelling and order. Regression cases
also keep normal percentage prose editable and protect code with its own category.
Space-flag forms remain outside this finite subset and require explicit literals.

## 10 / cumulative 30 — Explicit language selectors

`polish --lang not-a-tag` previously produced a usable-looking plan. Validate
selectors with the pack resolver's existing tag grammar and normalize casing.
Tests preserve regions/scripts, reject malformed/private-use syntax and accept
valid tags without claiming that a language pack is present or reviewed.

## 11 / cumulative 31 — Ordered numeric endpoints

Reversing `5%–10%` passed when only the quantity multiset was compared. Preserve
dash/ellipsis-connected quantities as one literal token, including signs and
separator spelling. Tests retain whole-sentence movement and prevent joining
across line breaks or protected spans. This does not parse verbal intervals or
validate the mathematics of a range.

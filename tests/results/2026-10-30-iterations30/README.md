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

## 12 / cumulative 32 — Reuse saved style cards

Add explicit `--style CARD.md` to rewriting commands, separate from editable input
files. Cards guide expression within the selected task and cannot supply facts or
file-operation authority. Parser checks and an [independent three-case test](style-use/README.md)
cover normal reuse, direct-focus scope and a missing card. All frozen inputs stayed
unchanged. The checkpoint suite ran 313 unittest methods with no failures/errors
and 8 environment skips; test discovery completed successfully.

## 13 / cumulative 33 — Explicit verification sources

`verify --file CLAIMS --source EVIDENCE` now distinguishes claims from repeatable
evidence selections. Both remain read-only. Parser tests and an [independent
technical/financial run](verify-sources/README.md) cover source citations, missing
evidence, runtime/annual-scope limits and embedded instructions. Input hashes stayed
unchanged; neither test claimed external authentication or complete verification.

## 14 / cumulative 34 — Discoverable literal scan

Expose the existing local detector as `scan --file PATH --lang en|zh-Hans` with
one-file, read-only scope. The plan names the actual helper/arguments, and the
guide keeps candidates, unsupported input and authorship claims distinct.
Integration checks execute a scan, verify findings and unchanged source, reject
unsupported selectors, and run the command from a relocated release.

## 15 / cumulative 35 — Concise verification findings

Actual verification responses repeated material limits and appended generic audit
and process disclaimers. A narrow delivery rule now places each necessary limit
beside its conclusion once. A [fresh same-request retest](verify-concise/README.md)
retained citations, environment-loading conditions, missing sources and unresolved
claims while removing the repeated framing. This is one observed retest, not a
measured cross-model improvement or permission to remove substantive uncertainty.

## 16 / cumulative 36 — Read-only installation diagnostics

Version discovery alone could not identify broken runtime dependencies. Add
`doctor [--json]` for helpers, metadata, bundled languages and local resource links.
It continues reporting when catalog data or the pack helper is missing. Tests
cover healthy/changed files, separate failed checks, no repairs and relocated
release execution. It does not validate host discovery, external packs or quality.

## 17 / cumulative 37 — Contact and URI autolinks

An unchanged `<team@example.com>` or `<mailto:team@example.com>` made an entire
document unsupported. Recognize email and scheme autolinks as protected targets,
allow surrounding prose edits, and retain errors for malformed/unclosed forms.
Tests cover destination changes, HTML/code boundaries and ordinary URI schemes.
This does not check whether an address delivers or a URI is reachable.

## 18 / cumulative 38 — Explicit formula spans

Changing `\(E=mc^2\)` to `\(E=mv^2\)` passed because the number stayed unchanged.
Preserve backslash-delimited inline/display formulas in full and shield their
contents from Markdown scanning. Tests cover changed symbols, multiline spans,
escaped delimiters, code/quote boundaries and ordinary unpaired Markdown escapes.
An initial check exposed a conflict with escaped literal brackets; paired-only
recognition fixes it, with a long-input regression for repeated unpaired escapes.
Dollar/unpaired notation and mathematical correctness remain outside protection.

## 19 / cumulative 39 — File inputs stay file-bound

`check --before -` previously selected the prose helper's stdin path, which can
read an empty stream rather than a stable original file. Reject lone-dash file
selectors for either kind. Actual dash filenames remain usable via explicit paths,
with executed stable-file evidence. Direct specialized stdin checks remain
available and keep their existing unbound-evidence label.

## 20 / cumulative 40 — Finite evaluation deadlines

`float('nan')` and infinity bypassed the positive timeout condition, reaching
execution or nonstandard JSON evidence. A shared guard now rejects these and
nonpositive values before any attempt files or processes. Entry-point checks
cover generation, judging, continuation, paired runs and direct execution;
finite fractional deadlines still work in the existing local stub suite.

## 21 / cumulative 41 — Diagnose broken helper syntax

A present `check_rewrite.py` containing invalid Python still reported `ready`.
Diagnostics now compile all runtime helpers in memory and name each syntax
failure, including compile-time errors such as a top-level return. A control
helper that raises at runtime proves compilation does not execute it. Diagnostics
remain read-only with no bytecode cache; compilation cannot establish behavior.

## 22 / cumulative 42 — Named scan rule selection

Users can now narrow a literal scan to named rule families with repeatable
`--rule ID`, discovered in `scan --help`. Unknown and wrong-language selections
fail instead of producing a misleading empty scan. Reports name the executed
rules, defaults retain full language coverage, and thresholds apply only to the
selected candidates. Executed command plans confirm scope and unchanged input.

## 23 / cumulative 43 — Single-brace interpolation fields

Renaming `{user.name}` or changing `{value!r}` to `{value!s}` passed prose checking.
Protect a bounded single-brace field subset, including names, positional fields,
attribute/index access, conversions and non-nested format specifications. Tests
retain editable surrounding prose, code boundaries and general brace expressions,
and exercise long unclosed inputs. Nested formatting and arbitrary expressions
still need explicit literal protection; this is not a template interpreter.

## 24 / cumulative 44 — Strict evaluation event evidence

Duplicate JSON fields could conceal a tool item, unknown top-level event types
were ignored, and nonfinite usage values were accepted. Evaluation JSON now
rejects duplicates/nonfinite numbers (including overflowed exponents); event
inspection rejects unknown types and malformed items. LF/CRLF record splitting
retains valid Unicode separators inside JSON strings. Regression stubs validate
the protocol only; these checks do not establish model quality or disable tools.

## 25 / cumulative 45 — Content-bound scan locations

CLI scan findings now identify the exact source bytes by SHA-256, length and path.
A second read suppresses stale findings when the source changed or disappeared
during scanning. Stdin retains a content hash but no stable-file claim. Tests
cover BOM/CRLF bytes, unchanged inputs, stdin and edits/removal during execution;
consumers still need to rerun after any later edit.

## 26 / cumulative 46 — Ordered ratios and fractions

Both `1:3` → `3:1` and `1/4` → `4/1` previously passed numeric comparison.
Explicit ratio/fraction connectors now preserve the whole expression and operand
order while allowing the unchanged expression to move with prose. Tests cover
multi-part, signed, decimal and scientific values plus line/code boundaries.
This compares source spelling; it does not evaluate or simplify the expression.

## 27 / cumulative 47 — Frozen locale selection fidelity

The CLI evaluator guessed Hans for bare `zh` and preferred bundled exact locales
over external fallback packs, disagreeing with runtime policy. Selection now
normalizes the supported tag subset, uses full region/script parent candidates,
and applies frozen external-location priority before specificity. Contract tests
compare runtime candidate sequences and exercise actual competing guide files.
The policy stays inside the hashed runner; existing results are not regenerated.

## 28 / cumulative 48 — Domain guidance in frozen CLI contexts

The CLI evaluator omitted domain guides even when a case declared its domain and
generation forbade reading other files. It now loads the selected frozen profile
and domain overview, records their hashes and rejects absent/unsafe resources.
Preparing all 15 relationship cases verifies 30 paired jobs: each Skill context
contains only its selected profile, baseline contexts remain empty and criteria
remain hidden. This is preparation validation, not new model-generation evidence;
the earlier subagent-based domain evaluation remains a separate unchanged record.

## 29 / cumulative 49 — Usable workflows and diagnostic instructions

User-facing docs omitted scan/doctor, saved style reuse and verification sources,
and incorrectly described every main CLI action as planning only. The README,
installation guidance and new workflow guide now distinguish plans from executed
checks, explain scopes/results, and show technical/financial examples. Disposable
fixtures exercise the documented diagnostic, scan and comparison commands. No
editing-quality claim follows from these documentation smoke checks.

## 30 / cumulative 50 — Coherent 0.5.0 delivery

Align runtime/Skill/archive versions, document compatibility and publish the PR
index. Complete the regression suite and reproducible builds, install from verified
bytes after comparing the prior receipt, and rehearse guarded rollback in isolation.
The final help text explicitly distinguishes planned tasks from executed doctor
diagnostics. Full outcomes and limits are in [delivery validation](release-050/README.md).

<!-- DELIVERY INDEX -->

## Delivery index

30/30 PRs recorded. Each link shows the incremental diff; review and merge in dependency order. The last branch contains the cumulative runtime. No PR was automatically merged.

| Batch | Cumulative | PR | Change |
| --- | --- | --- | --- |
| 1 | 21 | [#22](https://github.com/yuanqimanong/yaya/pull/22) | Preserve explicit literals from one-shot iterables |
| 2 | 22 | [#23](https://github.com/yuanqimanong/yaya/pull/23) | Reject discarded grants and conflicting review options |
| 3 | 23 | [#24](https://github.com/yuanqimanong/yaya/pull/24) | Use physical Markdown line boundaries |
| 4 | 24 | [#25](https://github.com/yuanqimanong/yaya/pull/25) | Expose literal and quotation protection in check |
| 5 | 25 | [#26](https://github.com/yuanqimanong/yaya/pull/26) | Require exact evaluation request and output packet sets |
| 6 | 26 | [#27](https://github.com/yuanqimanong/yaya/pull/27) | Add five-domain relationship preservation evaluations |
| 7 | 27 | [#28](https://github.com/yuanqimanong/yaya/pull/28) | Preserve Markdown task completion markers |
| 8 | 28 | [#29](https://github.com/yuanqimanong/yaya/pull/29) | Preserve image versus hyperlink roles in Markdown |
| 9 | 29 | [#30](https://github.com/yuanqimanong/yaya/pull/30) | Protect positional and formatted printf placeholders |
| 10 | 30 | [#31](https://github.com/yuanqimanong/yaya/pull/31) | Validate and normalize explicit language tags |
| 11 | 31 | [#32](https://github.com/yuanqimanong/yaya/pull/32) | Preserve ordered endpoints in numeric ranges |
| 12 | 32 | [#33](https://github.com/yuanqimanong/yaya/pull/33) | Apply selected saved style cards through explicit commands |
| 13 | 33 | [#34](https://github.com/yuanqimanong/yaya/pull/34) | Select verification evidence files explicitly |
| 14 | 34 | [#35](https://github.com/yuanqimanong/yaya/pull/35) | Expose read-only literal wording scans as scan |
| 15 | 35 | [#36](https://github.com/yuanqimanong/yaya/pull/36) | Keep verification findings concise without losing evidence limits |
| 16 | 36 | [#37](https://github.com/yuanqimanong/yaya/pull/37) | Add read-only runtime diagnostics with doctor |
| 17 | 37 | [#38](https://github.com/yuanqimanong/yaya/pull/38) | Support protected email and URI autolinks |
| 18 | 38 | [#39](https://github.com/yuanqimanong/yaya/pull/39) | Preserve explicitly delimited LaTeX formulas |
| 19 | 39 | [#40](https://github.com/yuanqimanong/yaya/pull/40) | Keep check inputs bound to explicit files |
| 20 | 40 | [#41](https://github.com/yuanqimanong/yaya/pull/41) | Reject nonfinite evaluation timeouts before execution |
| 21 | 41 | [#42](https://github.com/yuanqimanong/yaya/pull/42) | Diagnose unusable Python helpers without executing them |
| 22 | 42 | [#43](https://github.com/yuanqimanong/yaya/pull/43) | Select named scan rules and report the executed scope |
| 23 | 43 | [#44](https://github.com/yuanqimanong/yaya/pull/44) | Preserve common single-brace interpolation fields |
| 24 | 44 | [#45](https://github.com/yuanqimanong/yaya/pull/45) | Reject ambiguous and unknown evaluation event records |
| 25 | 45 | [#46](https://github.com/yuanqimanong/yaya/pull/46) | Bind scan locations to the exact input content |
| 26 | 46 | [#47](https://github.com/yuanqimanong/yaya/pull/47) | Preserve operand order in numeric ratios and fractions |
| 27 | 47 | [#48](https://github.com/yuanqimanong/yaya/pull/48) | Match evaluation language fallback to runtime precedence |
| 28 | 48 | [#49](https://github.com/yuanqimanong/yaya/pull/49) | Load selected frozen domain guides for domain evaluations |
| 29 | 49 | [#50](https://github.com/yuanqimanong/yaya/pull/50) | Document scoped workflows and installation diagnostics |
| 30 | 50 | [#51](https://github.com/yuanqimanong/yaya/pull/51) | Prepare Yaya 0.5.0 with verified upgrade and thirty-PR evidence |

See [0.5.0 delivery validation](release-050/README.md) and [machine-readable index](pr-index.json).

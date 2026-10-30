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

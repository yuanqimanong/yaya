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

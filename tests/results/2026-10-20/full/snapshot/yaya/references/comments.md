# Code comments

Read the code around each comment before rewriting it. Explain the actual behavior, reason, precondition, or limitation that matters to a maintainer. Do not invent design intent, complexity guarantees, performance measurements, or thread safety. If code and comment disagree, flag the mismatch; do not silently fix program logic during a comment task.

## Editable scope

The request authorizes comment prose, not executable code. Preserve identifiers, string literals, examples, formatting directives, license notices, and tooling annotations. A comment can affect tools: shebangs, encoding declarations, type checks, lint suppressions, coverage and formatter directives are not ordinary prose.

Docstrings are string objects and may be inspected at runtime. They and doctest examples stay unchanged unless explicitly requested. Editing them needs separate review; the bundled checker does not validate such changes.

## Check a candidate

Keep a before-copy and prepare the edited candidate. From the installed Yaya directory, run:

```text
python scripts/check_comments.py BEFORE AFTER
```

Version 0.1.0 supports `.py` and `.pyi` based on BEFORE's extension; AFTER may have a temporary filename. The source must parse on the running Python interpreter. It permits edits inside ordinary `#` comments while preserving code, strings, line structure, encoding, and recognized directive comments. This conservative check does not permit adding, deleting, moving, or reflowing comment lines. Comments inside f-string expressions stay protected because debug f-strings can expose their source text.

Read its JSON result:

- `passed` / exit 0: the implemented scope checks passed. Review whether the new comment is accurate; this is not a semantic proof.
- `failed` / exit 1: inspect the differences and repair or withdraw unintended edits. Do not write a failed candidate over the original or remove a check to accept it.
- `unsupported` / exit 2: there is no bundled check for this input. JavaScript, TypeScript, and other languages need the host's appropriate parser/checker and a focused diff review, or an explicitly unverified candidate. Do not report them as checked by Yaya.

The checker cannot recognize every tool-specific directive. Preserve unfamiliar directive-like comments and report only the checks actually performed. If Python is unavailable, provide a candidate/diff with that limitation rather than claiming validation.

## Example

Code: `return entries.get(key)`

Before: `# Leverage this powerful lookup to seamlessly retrieve the requested entry.`

After: `# Return the entry for key, or None if it is missing.`

This describes a plain dictionary lookup only when the surrounding code establishes that `entries` is a dictionary. A custom `get` method needs its own contract checked.

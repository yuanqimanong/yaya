# Compare a candidate with its original

`check` performs one read-only mechanical comparison of the two explicit files.
Resolve `--before`, `--after` and `--kind` through `scripts/yaya.py` before reading
the files. The plan is not a check result; execute the selected checker.

Both selectors name files. A lone `-` is rejected because the prose helper treats
it as stdin, which has no stable file identity. Use `./-` for a file literally named
`-`. Deliberate streaming checks remain available through `check_rewrite.py`
directly; their evidence is explicitly unbound and is not this file command.

| Kind | Helper beside this installed Skill | Boundary |
| --- | --- | --- |
| `prose` (default) | `scripts/check_rewrite.py BEFORE AFTER` | Supported Markdown protections and literal quantities |
| `comments` | `scripts/check_comments.py BEFORE AFTER` | Python ordinary-comment edits; other bytes stay fixed |

Execute `checker.script` with the plan's `checker.args` as separate argument
values, using the host's Python executable. Do not concatenate them into shell
code. The plan does not execute the checker itself.

For prose, `--literal TEXT` protects exact occurrences of a term or identifier;
repeat it for multiple terms. Each must be present in the original. `--quotes`
protects paired double/curly/East Asian quotations. These options are rejected
for comments. Example:
`yaya check --before original.md --after candidate.md --literal retry_limit --quotes`.

Pass paths as argument values through the host's execution tool. Keep both files
unchanged. Do not generate an allow grant, repair a candidate, or select another
kind to obtain a pass. Docstring grants remain available through the specialized
helper when explicitly requested outside this bounded command. Extra protections
apply only when selected; they do not authorize changes to protected content.

Report the helper's JSON status and concrete finding first. Include an exit code
only when captured from the checker process itself; host shells can remap it. Add
only limitations needed to interpret this result, rather than reciting its entire
limitations array. A `passed` result
means only that its checked boundaries held; it does not establish factual accuracy,
comment correctness, author origin, or date/number-to-entity associations. Use
`verify` for evidence-based factual claims. Preserve `failed`, `unsupported` and
input errors as distinct outcomes. If execution is unavailable, state that no check
ran instead of supplying an inferred result. Follow the helper's actual limitations
when interpreting unsupported formats; do not relabel them as failures or passes.

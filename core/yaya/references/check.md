# Compare a candidate with its original

`check` performs one read-only mechanical comparison of the two explicit files.
Resolve `--before`, `--after` and `--kind` through `scripts/yaya.py` before reading
the files. The plan is not a check result; execute the selected checker.

| Kind | Helper beside this installed Skill | Boundary |
| --- | --- | --- |
| `prose` (default) | `scripts/check_rewrite.py BEFORE AFTER` | Supported Markdown protections and literal quantities |
| `comments` | `scripts/check_comments.py BEFORE AFTER` | Python ordinary-comment edits; other bytes stay fixed |

Pass paths as argument values through the host's execution tool. Keep both files
unchanged. Do not generate an allow grant, repair a candidate, or select another
kind to obtain a pass. Docstring grants and extra protection options remain
available through the specialized helpers when explicitly requested outside this
bounded command; `check` does not silently add them.

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

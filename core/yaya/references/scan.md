# Scan literal wording candidates

`yaya scan --file draft.md --lang zh-Hans` selects the bundled read-only detector.
It requires one file and an explicit `en` or `zh-Hans` language. Pack availability
does not extend the detector's language inventory. Use `review` for contextual
editorial judgment and `human` for rewriting, including directness decisions.

Use repeatable `--rule ID` to select only named rules; `yaya scan --help` lists IDs.
For example, `--lang en --rule en-stock-close` scans only generic endings. Without
this option, all rules for the selected language run. Unknown or wrong-language
IDs are errors. Results name `enabled_rules`; describe an empty selected-rule
result within that scope, without implying that the other rules were checked.

| Suffix (prefix `en-` or `zh-`) | Candidate family |
| --- | --- |
| `empty-opener` | Generic opening context |
| `hype` | Stock promotional claims |
| `stock-close` | Generic conclusions |
| `light-verb` | Indirect verb phrases |

Resolve the command, then execute `scanner.script` with `scanner.args` as separate
arguments using the host's Python executable. The plan is not a scan result. Keep
the input file intact and do not silently switch tools if it returns unsupported.

The executed scanner records the input's SHA-256, byte length and absolute file
path. Locations refer to that content version; rerun after editing it. If a second
read finds changed/unreadable input, the scan returns an error without stale
findings. The specialized helper also accepts stdin: its content hash is recorded,
but `input_stable: null` indicates no stable file identity. The `scan` command
continues to require a selected file. A matching hash does not assess writing quality.

For an `ok` result, report the matched phrases and source lines, with the rule's
review question. A match is a candidate, not an instruction to delete it. An empty
list means the finite rules found no candidates, not that the text is natural or
human-written. Do not add an AI probability, model-brand label or automatic rewrite.
Report input errors and unsupported formats distinctly. If execution is unavailable,
state that no scan ran. Avoid copying the whole generic limitations list; mention
the limits needed to interpret this particular result.

# Scan literal wording candidates

`yaya scan --file draft.md --lang zh-Hans` selects the bundled read-only detector.
It requires one file and an explicit `en` or `zh-Hans` language. Pack availability
does not extend the detector's language inventory. Use `review` for contextual
editorial judgment and `human` for rewriting, including directness decisions.

Resolve the command, then execute `scanner.script` with `scanner.args` as separate
arguments using the host's Python executable. The plan is not a scan result. Keep
the input file intact and do not silently switch tools if it returns unsupported.

For an `ok` result, report the matched phrases and source lines, with the rule's
review question. A match is a candidate, not an instruction to delete it. An empty
list means the finite rules found no candidates, not that the text is natural or
human-written. Do not add an AI probability, model-brand label or automatic rewrite.
Report input errors and unsupported formats distinctly. If execution is unavailable,
state that no scan ran. Avoid copying the whole generic limitations list; mention
the limits needed to interpret this particular result.

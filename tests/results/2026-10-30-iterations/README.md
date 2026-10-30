# Twenty-iteration follow-up

These are local deterministic regressions, not model-quality scores. Each round
is proposed separately; later PRs depend on the previous round. Roll back a round
by reverting its commit, accounting for any later dependent changes.

| Round | Observed problem and resulting behavior | Validation |
| --- | --- | --- |
| 2 | Unsupported defaults entered plans; duplicate options crashed argparse; read-only deliveries accepted write configuration. Catalog loading now validates types, choices, actions and delivery boundaries before parsing or packaging. | New regressions initially reported 13 failures and 2 errors. Catalog, command and release suites pass after the fix (36 methods; 3 Windows symlink subcases skipped). |
| 3 | Prose evidence read entire files before the existing 2 MiB check. Initial and stability reads now share that limit, and oversized inputs never reach comparison. | Three new regressions failed before the fix; evidence and rewrite suites pass. Growth during checking invalidates the result. Other checker and snapshot size policies are unchanged. |
| 4 | Shortcut references with normalized whitespace were unprotected, while explicit link labels and escaped brackets could be frozen unnecessarily. Normalize reference IDs for lookup, distinguish explicit links and escapes, and report multiline shortcuts as unsupported. | Markdown edge, rewrite and tell-detection suites pass; regression inputs demonstrated both missed link changes and false positives before the fix. This remains a conservative Markdown subset. |

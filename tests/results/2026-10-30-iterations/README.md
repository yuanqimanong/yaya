# Twenty-iteration follow-up

These are local deterministic regressions, not model-quality scores. Each round
is proposed separately; later PRs depend on the previous round. Roll back a round
by reverting its commit, accounting for any later dependent changes.

| Round | Observed problem and resulting behavior | Validation |
| --- | --- | --- |
| 2 | Unsupported defaults entered plans; duplicate options crashed argparse; read-only deliveries accepted write configuration. Catalog loading now validates types, choices, actions and delivery boundaries before parsing or packaging. | New regressions initially reported 13 failures and 2 errors. Catalog, command and release suites pass after the fix (36 methods; 3 Windows symlink subcases skipped). |
| 3 | Prose evidence read entire files before the existing 2 MiB check. Initial and stability reads now share that limit, and oversized inputs never reach comparison. | Three new regressions failed before the fix; evidence and rewrite suites pass. Growth during checking invalidates the result. Other checker and snapshot size policies are unchanged. |
| 4 | Shortcut references with normalized whitespace were unprotected, while explicit link labels and escaped brackets could be frozen unnecessarily. Normalize reference IDs for lookup, distinguish explicit links and escapes, and report multiline shortcuts as unsupported. | Markdown edge, rewrite and tell-detection suites pass; regression inputs demonstrated both missed link changes and false positives before the fix. This remains a conservative Markdown subset. |
| 5 | The builder packaged a skill whose advertised version disagreed with its archive metadata. It now requires one simple metadata.version scalar matching version.json before creating output. | Release tests pass; mismatched, missing and duplicate skill-version declarations all reproduced acceptance before the fix. The supported frontmatter syntax is deliberately the repository's simple mapping, not arbitrary YAML. |
| 6 | English tell candidates disappeared after soft wrapping and matched inside Unicode/alphanumeric words. Matching now tolerates ordinary layout whitespace, preserves original offsets and respects word boundaries; protected spans and blank paragraphs interrupt matching. | 17 detector tests pass. Three wrapped cases and four embedded-word cases reproduced the previous misses/false positives. Markdown emphasis and protected-span counterexamples remain covered; candidates still require contextual review. |

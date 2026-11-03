# Local-tool design references

The [Vale CLI documentation](https://docs.vale.sh/topics/cli) exposes resolved
configuration and resource locations through dedicated commands. Yaya's `doctor`
reports local runtime structure and resource checks, leaving user material and the
installation unchanged. It does not implement Vale configuration, import its rules
or claim equivalent coverage.

[write-good](https://github.com/btford/write-good) exposes suggestions with source
positions. Yaya's explicit `scan` similarly presents review candidates and keeps
matching wording separate from judging its use in context.

[Vale's markup-scoping explanation](https://vale.sh/features/markup) illustrates
why code and link destinations should stay separate from editable prose. Yaya's
scanner covers a Markdown subset using only the standard library and reports
unsupported syntax; it does not claim full parser coverage. These are design
comparisons, not copied rules or code, and they include no measured performance
comparison. Sources checked 2026-10-30.

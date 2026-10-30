# Local-tool design references

The [Vale CLI documentation](https://docs.vale.sh/topics/cli) exposes resolved
configuration and resource locations through dedicated commands. Yaya's `doctor`
reports local runtime structure and resource checks. It leaves user material and
the installation unchanged. It does not
implement Vale configuration, import its rules or claim equivalent coverage.

[write-good](https://github.com/btford/write-good) exposes suggestions with source
positions. Yaya's explicit `scan` similarly presents review candidates and retains
the distinction between matching wording and judging its use in context.

[Vale's markup-scoping explanation](https://vale.sh/features/markup) illustrates
why code and link destinations should stay separate from editable prose. Yaya
keeps its existing standard-library subset scanner and reports unsupported syntax;
it does not claim full parser coverage. These are design comparisons, not copied
rules/code or measured performance comparisons. Sources checked 2026-10-30.

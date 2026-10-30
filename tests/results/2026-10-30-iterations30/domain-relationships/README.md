# Five-domain relationship preservation

Fifteen original synthetic requests were frozen before generation, three per
domain. Two fresh Codex subagents received identical requests in separate contexts;
one could use the frozen Yaya runtime and relevant references, the other used no
Skill. Each condition used one 15-case batch, so cases were not individually
isolated. The inherited model's exact revision/settings were unavailable. Neither
generator received criteria or the other output.

The parent agent reviewed the complete outputs against predeclared criteria.
This review was nonblind and is not professional human review. Both conditions
preserved the assessed meaning and task boundaries on all 15 cases. Both left four
already-clear passages unchanged. This run supports adding regression coverage;
it does not demonstrate that the Skill outperforms the baseline.

The frozen mechanical checker passed all 15 Skill outputs and 12 baseline outputs.
The three baseline findings were a repeated `2` removed from a retry explanation,
`60%` repeated to clarify its antecedent, and a year changed from `2024 年` to
parenthetical `2024`. Editorial review found their meaning preserved, while the
literal checker reported the changed counts or spelling. Mechanical failures
therefore need interpretation.

`cases.json`, `outputs.json` and `assessment.json` retain the full inputs, outputs
and case-level conclusions. `runtime.zip` preserves the actual frozen Skill;
`manifest.json` records input hashes and `artifacts.sha256.json` hashes this
evidence. The execution audit says `not_recorded` because these calls used the
host's subagent tool, not the Codex CLI runner; output shape alone cannot prove
execution provenance. Five domain profiles remain experimental.

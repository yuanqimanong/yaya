# Domain profiles

`catalog.json` lists the supported domain IDs, concrete coverage, protected
relationships, exclusions and guidance paths. `python scripts/yaya.py domains`
renders that list. A domain supplies editorial constraints and expression choices. Its coverage is
limited to the listed material and relationships; factual verification needs evidence.

## Load and apply

For an explicit `--domain`, require an exact catalog ID and load only its guide.
For a natural-language request, map a clearly requested field to the matching
profile; preserve the requested narrower subject rather than claiming coverage
of every subfield. If the subject is not listed, say that no dedicated profile
exists and offer or perform generic editing within the user's request. Never label
generic medical, legal or other unsupported work as validated domain support.

Keep four decisions separate: task (what to do), domain (which relationships must
survive), audience (what needs explaining), and tone (how it sounds). Language and
locale are resolved independently using the language-pack mechanism. A technical
or financial topic can be explained plainly. No profile calls for jargon just to
sound professional or for switching the material's language.

Apply only rules relevant to the supplied material. Use its existing terms unless
evidence establishes a correction. Domain examples are synthetic, not task facts.
For pure polishing, preserve claims and flag a consequential apparent conflict
separately; for verification, cite evidence and report unresolved claims. Do not
silently change a forecast into an outcome, association into causation, or a proposal
into a commitment. With an output-style prompt task, encode these constraints in
the downstream instructions without changing the prompt's substantive purpose.

## Quality and extension

All five profiles are **experimental**. Each provides scope, actionable editing
rules, original positive/preservation examples and source rationale. The sources
inform specific writing decisions; they do not endorse Yaya, certify the profiles,
or establish Chinese-language or cross-domain effectiveness.

Validation must distinguish deterministic command/scope checks from model-produced
edits and semantic review. The development suite is `tests/evals/commands-domains.json`;
execution evidence is under `tests/results/2026-10-30-commands-domains/` in the source
repository. Only a completed report can establish which cases were exercised.
Passing constructed cases does not establish general accuracy, professional review,
or a measured improvement over the old version. Language quality is also subject
to the language packs' own limitations.

To add a profile, add its catalog record and guide; supply cases that need editing,
cases that should stay unchanged, and tempting but wrong rewrites. Record sources,
supported languages and actual validation separately. Do not turn a newly added
ID into a claim of tested support. Profiles ship with the core; this version does
not install arbitrary domain packs or silently download rules.
